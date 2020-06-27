import re
from urllib.parse import quote
from typing import List, Tuple, Type

import flask

from . import app
from . import controller
from .model import BaseDocument, list_doctypes


@app.route('/')
def home():
    q = flask.request.args.get('q')
    return index() if not q else search()


def index():
    return flask.render_template(
        'index.html',
        show_search=controller.is_elasticsearch_reachable(),
    )


@app.route('/zoek')
def search():
    q: str = flask.request.args.get('q')
    doctypes_selection: List[Type[BaseDocument]] = [
        doctype for doctype in list_doctypes()
        if flask.request.args.get(doctype.__name__) == 'on'
    ]
    if not doctypes_selection:
        doctypes_selection = list_doctypes()
    doctypes: List[Tuple[str, str, bool]] = [
        (doctype.get_index_name_pretty(), doctype.__name__, doctype in doctypes_selection)
        for doctype in list_doctypes()
    ]
    if not q:
        return flask.render_template(
            'search.html',
            show_search=controller.is_elasticsearch_reachable(),
            doctypes=doctypes,
        )
    elif len(q) <= 2:
        return show_names_list(q)
    cards_per_page = 10
    page = flask.request.args.get('page', default=1, type=int)
    searcher = controller.Searcher(q.lower(), start=(page - 1) * cards_per_page,
                                   size=cards_per_page, doctypes=doctypes_selection)
    hits = searcher.get_results()
    hits_formatted = [format_hit(hit) for hit in hits]
    hits_total = searcher.count()
    page_range = controller.get_page_range(hits_total, page, cards_per_page)
    query_string = f'?q={quote(q)}&page='

    if page == 1:
        suggestions = controller.get_suggestions(searcher.keywords)
    else:
        suggestions = {}
    suggestion_urls = {}
    for token, _suggs in suggestions.items():
        for suggestion in _suggs:
            q_new = re.sub(r'\b{}\b'.format(token), f'{token} {suggestion}', q)
            url = f'/?q={quote(q_new)}'
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


@app.route('/namen')
def show_names_list(q):
    for letter in q.lower():
        if not letter.isalpha():
            return index()
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
