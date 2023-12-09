from typing import Any

import flask

from .. import app
from ..model import index_name_to_doctype


@app.route("/api/columns/")
def datatables_api_columns():
    index_name = flask.request.args.get("index")
    if index_name is None:
        return flask.abort(400)
    doctype = index_name_to_doctype[index_name]
    columns = doctype.get_columns()
    return [{"data": column, "title": column} for column in columns]


@app.route("/api/rows/", methods=["POST"])
def datatables_api():
    req: dict[str, Any] = flask.request.json  # type: ignore
    index_name: str = req["index"]
    doctype = index_name_to_doctype[index_name]
    s = doctype.search()
    columns = doctype.get_columns()
    s = s.source(columns)
    s = s.extra(from_=req["start"], size=req["length"])
    s = s.sort(
        *[
            {doctype.get_sort_field(req["columns"][item["column"]]["data"]): {"order": item["dir"]}}
            for item in req["order"]
        ]
    )
    res = s.execute()
    docs = []
    for hit in res:
        hit_dict = hit.to_dict()
        doc = {field: hit_dict.get(field, None) for field in columns}
        doc["id"] = hit.meta.id
        docs.append(doc)
    resp = {
        "draw": int(req["draw"]),
        "recordsTotal": res["hits"]["total"]["value"],
        "recordsFiltered": res["hits"]["total"]["value"],
        "data": docs,
    }
    return resp
