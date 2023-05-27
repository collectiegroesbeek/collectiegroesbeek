import re
import string
import subprocess
import threading
import time
from datetime import datetime
from urllib.parse import quote
from typing import List, Tuple, Type

import flask

from . import app
from . import controller
from .controller import get_doc, get_number_of_total_docs
from .model import BaseDocument, list_doctypes, index_name_to_doctype


DROPBOX_TIMESTAMP_LOCK = threading.Lock()


@app.route('/')
def home():
    n_total_docs = get_number_of_total_docs()
    n_total_docs_str = f'{n_total_docs:,d}'.replace(',', '&nbsp;')
    return flask.render_template(
        'index.html',
        n_total_docs=n_total_docs_str,
        doctypes=list_doctypes(),
    )


@app.route('/zoek')
def search():
    q: str = flask.request.args.get('q')
    doctypes_selection: List[Type[BaseDocument]] = [
         index_name_to_doctype[index_name]
         for index_name in flask.request.args.getlist('index')
    ]
    if not doctypes_selection:
        doctypes_selection = [list_doctypes()[0]]
    doctypes: List[Tuple[str, str, bool]] = [
        (doctype.get_index_name_pretty(), doctype.Index.name, doctype in doctypes_selection)
        for doctype in list_doctypes()
    ]
    if q is None:
        return flask.render_template(
            'search.html',
            doctypes=doctypes,
        )
    if 0 < len(q) <= 2:
        return show_names_list(q)
    cards_per_page = 10
    page = flask.request.args.get('page', default=1, type=int)
    searcher = controller.Searcher(q.lower(), start=(page - 1) * cards_per_page,
                                   size=cards_per_page, doctypes=doctypes_selection)
    hits = searcher.get_results()
    hits_formatted = [format_hit(hit) for hit in hits]
    hits_total = searcher.count()
    page_range = controller.get_page_range(hits_total, page, cards_per_page)
    query_string = f'?q={quote(q)}'
    query_string = add_selected_doctypes_to_query_string(query_string, doctypes_selection)
    query_string += '&page='

    if page == 1:
        suggestions = controller.get_suggestions(searcher.keywords)
    else:
        suggestions = {}
    suggestion_urls = {}
    for token, _suggs in suggestions.items():
        for suggestion in _suggs:
            q_new = re.sub(r'\b{}\b'.format(token), f'{token} {suggestion}', q)
            url = f'/?q={quote(q_new)}'
            url = add_selected_doctypes_to_query_string(url, doctypes_selection)
            suggestion_urls[suggestion] = url

    return flask.render_template(
        'cards.html',
        hits=hits_formatted,
        hits_total=hits_total,
        q=q,
        query_string=query_string,
        page_range=page_range,
        page=page,
        suggestions=suggestion_urls,
        doctypes=doctypes,
    )


def add_selected_doctypes_to_query_string(
        query_string: str,
        doctypes_selection: List[Type[BaseDocument]]
) -> str:
    for doctype in doctypes_selection:
        query_string += f'&index={doctype.Index.name}'
    return query_string


@app.route('/namen/')
@app.route('/namen/<q>')
def show_names_list(q=''):
    if not q:
        return flask.render_template('names_letters.html', letters=string.ascii_lowercase[:27], hits_total=None)
    for letter in q.lower():
        if not letter.isalpha():
            return home()
    names_list = controller.get_names_list(q)
    hits_total = len(names_list)
    return flask.render_template('names.html', namen=names_list, hits_total=hits_total)


def format_hit(doc: BaseDocument) -> dict:
    return {
        'id': doc.meta.id,
        'score': doc.meta.score,
        'index': doc.get_index_name_pretty(),
        'title': doc.get_title(),
        'subtitle': doc.get_subtitle(),
        'body_lines': doc.get_body_lines(),
    }


@app.route('/doc/<int:doc_id>')
def get_product(doc_id):
    doc = get_doc(doc_id)
    doc_formatted = format_hit(doc)
    return flask.render_template('card.html', hit=doc_formatted)


@app.route('/verken/')
def browse():
    index_name = flask.request.args.get('index', None)
    return flask.render_template(
        "browse.html",
        index_name=index_name,
        doctypes=list_doctypes(),
    )


with open("names.txt", encoding="utf-8") as f:
    NAMES = f.readlines()


@app.route('/namen-ner/')
def names_ner():
    query = flask.request.args.get('q', '').lower().strip()
    page = int(flask.request.args.get('page', 1))
    return flask.render_template(
        "names_ner.html",
        query=query,
        page=page
    )


@app.route('/namen-ner/search/', methods=['GET'])
def search_names_ner():
    query = flask.request.args.get('q', '').lower().strip()
    page = int(flask.request.args.get('page', 1))
    per_page = int(flask.request.args.get('per_page', 1000))
    if query:
        filtered_names = [name for name in NAMES if query in name.lower()]
    else:
        filtered_names = NAMES
    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = -(-len(filtered_names) // per_page)  # Equivalent to ceiling division

    return flask.jsonify({
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'names': filtered_names[start:end]
    })


@app.route('/api/columns/')
def datatables_api_columns():
    index_name = flask.request.args.get('index')
    doctype = index_name_to_doctype[index_name]
    columns = doctype.get_columns()
    return [
        {'data': column, 'title': column}
        for column in columns
    ]


@app.route('/api/rows/', methods=["POST"])
def datatables_api():
    req = flask.request.json
    index_name = req['index']
    doctype = index_name_to_doctype[index_name]
    s = doctype.search()
    columns = doctype.get_columns()
    s = s.source(columns)
    s = s.extra(from_=req['start'], size=req['length'])
    s = s.sort(
        *[
            {doctype.get_sort_field(req['columns'][item['column']]['data']): {'order': item['dir']}}
            for item in req['order']
        ]
    )
    res = s.execute()
    docs = []
    for hit in res:
        hit_dict = hit.to_dict()
        doc = {field: hit_dict.get(field, None) for field in columns}
        doc['id'] = hit.meta.id
        docs.append(doc)
    resp = {
        "draw": int(req["draw"]),
        "recordsTotal": res['hits']['total']['value'],
        "recordsFiltered": res['hits']['total']['value'],
        "data": docs,
    }
    return resp


@app.route('/api/dropbox-webhook/', methods=['GET'])
def dropbox_webhook_verification():
    resp = flask.Response(flask.request.args.get('challenge'))
    resp.headers['Content-Type'] = 'text/plain'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp


@app.route('/api/dropbox-webhook/', methods=['POST'])
def dropbox_webhook():
    timestamp = int(time.time())
    with DROPBOX_TIMESTAMP_LOCK:
        with open("webhook_timestamp.txt") as f:
            timestamp_last_incoming_webhook = int(f.read())
        with open("webhook_timestamp.txt", "w") as f:
            f.write(str(timestamp))
    if (timestamp - timestamp_last_incoming_webhook) > 300:
        with open("/var/log/dropbox.log", "a") as f_log:
            f_log.write(f'\n{datetime.now()} incoming webhook\n')
            subprocess.Popen(
                ['./run_import.sh'],
                stdout=f_log,
                stderr=f_log,
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )
    return flask.make_response("", 200)
