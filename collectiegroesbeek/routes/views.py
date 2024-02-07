import json
import os
import posixpath
import re
from urllib.parse import quote
from typing import List, Tuple, Type

import flask

from .. import app
from .. import controller
from ..controller import get_doc, get_number_of_total_docs, get_indices_and_doc_counts, format_int
from ..model import BaseDocument, list_doctypes, index_name_to_doctype


@app.route("/")
def home():
    n_total_docs = get_number_of_total_docs()
    n_total_docs_str = format_int(n_total_docs)
    index_to_doc_count = {
        index: format_int(count) for index, count in get_indices_and_doc_counts().items()
    }
    return flask.render_template(
        "index.html",
        n_total_docs=n_total_docs_str,
        doctypes=list_doctypes(),
        index_to_doc_count=index_to_doc_count,
    )


@app.route("/zoek/")
def search():
    q: str = flask.request.args.get("q", default="", type=str)
    doctypes_selection: List[Type[BaseDocument]] = [
        index_name_to_doctype[index_name] for index_name in flask.request.args.getlist("index")
    ]
    if not doctypes_selection:
        doctypes_selection = [list_doctypes()[0]]
    doctypes: List[Tuple[str, str, bool]] = [
        (doctype.get_index_name_pretty(), doctype.Index.name, doctype in doctypes_selection)
        for doctype in list_doctypes()
    ]
    if q is None:
        return flask.render_template(
            "search.html",
            doctypes=doctypes,
        )
    cards_per_page = 10
    page = flask.request.args.get("page", default=1, type=int)
    searcher = controller.Searcher(
        q.lower(),
        start=(page - 1) * cards_per_page,
        size=cards_per_page,
        doctypes=doctypes_selection,
    )
    hits = searcher.get_results()
    hits_formatted = [format_hit(hit) for hit in hits]
    hits_total = searcher.count()
    page_range = controller.get_page_range(hits_total, page, cards_per_page)
    query_string = f"?q={quote(q)}"
    query_string = add_selected_doctypes_to_query_string(query_string, doctypes_selection)
    query_string += "&page="

    if page == 1:
        suggestions = controller.get_suggestions(searcher.keywords)
    else:
        suggestions = {}
    suggestion_urls = {}
    for token, _suggs in suggestions.items():
        for suggestion in _suggs:
            q_new = re.sub(r"\b{}\b".format(token), f"{token} {suggestion}", q)
            url = f"?q={quote(q_new)}"
            url = add_selected_doctypes_to_query_string(url, doctypes_selection)
            suggestion_urls[suggestion] = url

    return flask.render_template(
        "cards.html",
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
    query_string: str, doctypes_selection: List[Type[BaseDocument]]
) -> str:
    for doctype in doctypes_selection:
        query_string += f"&index={doctype.Index.name}"
    return query_string


def format_hit(doc: BaseDocument) -> dict:
    return {
        "id": doc.meta.id,
        "score": doc.meta.score,
        "index": doc.get_index_name_pretty(),
        "title": doc.get_title(),
        "subtitle": doc.get_subtitle(),
        "body_lines": doc.get_body_lines(),
    }


@app.route("/doc/<int:doc_id>")
def get_product(doc_id):
    doc = get_doc(doc_id)
    doc_formatted = format_hit(doc)
    return flask.render_template("card.html", hit=doc_formatted)


@app.route("/verken/")
def browse():
    index_name = flask.request.args.get("index", None)
    return flask.render_template(
        "browse.html",
        index_name=index_name,
        doctypes=list_doctypes(),
    )


def _load_names() -> list[str]:
    filepath = os.path.abspath(
        os.path.join(os.path.abspath(__file__), "..", "..", "..", "names.txt")
    )
    with open(filepath, encoding="utf-8") as f:
        return f.readlines()


NAMES = _load_names()


@app.route("/namen/")
def names_ner():
    query = flask.request.args.get("q", "").lower().strip()
    page = int(flask.request.args.get("page", 1))
    return flask.render_template("names_ner.html", query=query, page=page)


@app.route("/namen/search/", methods=["GET"])
def search_names_ner():
    query = flask.request.args.get("q", "").lower().strip()
    page = int(flask.request.args.get("page", 1))
    per_page = 1000
    if query:
        filtered_names = [name for name in NAMES if query in name.lower()]
    else:
        filtered_names = NAMES
    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = -(-len(filtered_names) // per_page)  # Equivalent to ceiling division

    return flask.jsonify(
        {
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "names": filtered_names[start:end],
        }
    )


@app.route("/publicaties/", methods=["GET"])
def publicaties():
    _publicaties = []
    _categorieen = set()
    path = "collectiegroesbeek/templates/publicaties"
    for filename_html in os.listdir(path):
        if not filename_html.endswith(".html"):
            continue
        filename_json = filename_html.replace(".html", ".json")
        with open(posixpath.join(path, filename_json)) as f:
            metadata = json.load(f)
        _publicaties.append(
            {
                "publicatie": filename_html.replace(".html", ""),
                "titel": metadata["titel"],
                "jaar": metadata["jaar"],
                "afkomstig_uit": metadata["afkomstig uit"],
                "omschrijving": metadata["omschrijving"],
                "categorie": metadata["categorie"],
            }
        )
        _categorieen.add(metadata["categorie"])
    _publicaties = sorted(_publicaties, key=lambda x: x["jaar"])
    return flask.render_template(
        "publicaties.html",
        publicaties=_publicaties,
        categorieen=sorted(_categorieen),
    )


@app.route("/publicaties/<publicatie>", methods=["GET"])
def publicatie_(publicatie: str):
    template_path = "publicaties/" + publicatie + ".html"
    return flask.render_template(
        "publicatie.html", publicatie=publicatie, template_path=template_path
    )
