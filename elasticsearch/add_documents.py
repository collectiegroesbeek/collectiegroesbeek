import argparse
import csv
import logging
import os
import re
import time
from typing import Dict, Optional, Type

from dotenv import dotenv_values
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Index, connections
import tqdm

from collectiegroesbeek.model import BaseDocument, index_number_to_doctype


connections.create_connection(hosts=[dotenv_values(".env")["elasticsearch_host"]])


def logging_setup():
    log_format = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
    logging.basicConfig(format=log_format, level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)


class CardProcessor:
    def __init__(self, batch_size=500, dryrun: bool = False):
        self.batch_size = batch_size
        self.dryrun = dryrun
        self.client = connections.get_connection()
        self._movers: Dict[str, IndexMover] = {}
        self._items = []

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


class IndexMover:
    def __init__(self, doctype: Type[BaseDocument]):
        self.alias = doctype.Index.name
        es_index: Index = doctype.Index()
        if es_index.exists():
            self.old_name = next(iter(es_index.get_alias().keys()))
            self.old_es_index: Optional[Index] = Index(name=self.old_name)
        else:
            self.old_es_index = None
            self.old_name = None
        self.new_name = "{}_{:.0f}".format(self.alias, time.time())
        self.new_es_index = Index(name=self.new_name)
        doctype.init(index=self.new_name)

    def move_alias_to_new(self):
        if self.old_es_index:
            self.old_es_index.delete_alias(name=self.alias)
        self.new_es_index.put_alias(name=self.alias)
        if self.old_es_index:
            self.old_es_index.delete()


def filename_to_doctype(filename):
    filename = filename.lower()
    index_number = int(re.match(r"coll gr (\d+) .*", filename).group(1))
    return index_number_to_doctype[index_number]


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
    assert connections.get_connection().ping()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path", default="../collectiegroesbeek-data", help="Folder with the CSV data files."
    )
    parser.add_argument("--doctype", required=False, help="Limit ingestion to this index only")
    parser.add_argument("--dryrun", action="store_true", help="Don't actually ingest")
    options = parser.parse_args()
    run(path=options.path, doctype_name=options.doctype, dryrun=options.dryrun)
