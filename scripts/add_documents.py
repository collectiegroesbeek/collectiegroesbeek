import argparse
import csv
import os
import re
from typing import Optional, Type

import tqdm

from collectiegroesbeek.model import BaseDocument, index_number_to_doctype
from ingest.elasticsearch_utils import DocProcessor
from ingest import logging_setup
from ingest.elasticsearch_utils import setup_es_connection


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
    processor = DocProcessor(dryrun=dryrun)
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path", default="../collectiegroesbeek-data", help="Folder with the CSV data files."
    )
    parser.add_argument("--doctype", required=False, help="Limit ingestion to this index only")
    parser.add_argument("--dryrun", action="store_true", help="Don't actually ingest")
    options = parser.parse_args()
    run(path=options.path, doctype_name=options.doctype, dryrun=options.dryrun)
