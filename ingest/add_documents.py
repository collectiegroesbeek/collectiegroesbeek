import argparse
import csv
import os
import re
from typing import Dict, Optional, Type

from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections
import tqdm

from collectiegroesbeek.model import BaseDocument, index_number_to_doctype
from ingest_pkg import logging_setup
from ingest_pkg.elasticsearch_utils import IndexMover, setup_es_connection


class CardProcessor:
    def __init__(self, batch_size=500, dryrun: bool = False):
        self.batch_size = batch_size
        self.dryrun = dryrun
        self.client = connections.get_connection()
        self._movers: Dict[str, IndexMover] = {}
        self._items: list[dict] = []

    def register_index(self, doctype):
        """Mark an index as being updated, creating an IndexMover instance."""
        key = doctype.Index.name
        if key in self._movers:
            return
        if not self.dryrun:
            self._movers[key] = IndexMover(doctype)

    def add(self, card: BaseDocument):
        d = card.to_dict(include_meta=True)
        if not self.dryrun:
            d["_index"] = self._movers[d["_index"]].new_name
        self._items.append(d)
        if len(self._items) > self.batch_size:
            self.flush()

    def flush(self):
        if len(self._items) > 0 and not self.dryrun:
            bulk(self.client, self._items)
        self._items = []

    def finalize(self):
        self.flush()
        for mover in self._movers.values():
            mover.move_alias_to_new()


def filename_to_doctype(filename: str) -> Type[BaseDocument]:
    filename = filename.lower()
    match = re.match(r"coll gr (\d+) .*", filename)
    assert match is not None
    index_number = int(match.group(1))
    try:
        return index_number_to_doctype[index_number]
    except KeyError:
        raise KeyError(f"Unknown index number {index_number}, filename {filename}")


def run(path, doctype_name: Optional[str], dryrun: bool):
    processor = CardProcessor(dryrun=dryrun)
    filenames = sorted(filename for filename in os.listdir(path) if filename.endswith(".csv"))
    pbar = tqdm.tqdm(filenames)
    for filename in pbar:
        pbar.set_postfix(filename=filename)
        doctype = filename_to_doctype(filename)
        if doctype_name and doctype.__name__ != doctype_name:
            continue
        processor.register_index(doctype)
        filepath = os.path.join(path, filename)
        with open(filepath, encoding="utf-8") as f:
            csvreader = csv.reader(f)
            next(csvreader)  # skip first line
            for line in csvreader:
                if not line:
                    continue
                card = doctype.from_csv_line(line)
                if card is None:
                    continue
                processor.add(card)
    processor.finalize()


if __name__ == "__main__":
    logging_setup()
    setup_es_connection()
    assert connections.get_connection().ping()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path", default="../collectiegroesbeek-data", help="Folder with the CSV data files."
    )
    parser.add_argument("--doctype", required=False, help="Limit ingestion to this index only")
    parser.add_argument("--dryrun", action="store_true", help="Don't actually ingest")
    options = parser.parse_args()
    run(path=options.path, doctype_name=options.doctype, dryrun=options.dryrun)
