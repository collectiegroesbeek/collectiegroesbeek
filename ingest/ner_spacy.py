import csv
import logging
import os
import re

import spacy
from tqdm import tqdm

from collectiegroesbeek.model import NamesNerDoc
from ingest.ingest_pkg import logging_setup
from ingest.ingest_pkg.elasticsearch_utils import setup_es_connection, DocProcessor


logger = logging.getLogger(__name__)


def create_dataset():
    path = "../collectiegroesbeek-data"
    filenames = sorted(filename for filename in os.listdir(path) if filename.endswith(".csv"))
    text_pairs: list[tuple[str, str]] = []
    pbar = tqdm(filenames)
    for filename in pbar:
        if not filename.startswith(("Coll Gr 1", "Coll Gr 2")):
            continue
        pbar.set_postfix(filename=filename)
        filepath = os.path.join(path, filename)
        with open(filepath, encoding="utf-8") as f:
            csvreader = csv.DictReader(f)
            for item in csvreader:
                if filename.startswith("Coll Gr 1"):
                    field1 = item.get("naam")
                    field2 = item.get("inhoud")
                elif filename.startswith("Coll Gr 2"):
                    field1 = (item.get("voornaam", "") + " " + item.get("patroniem", "")).strip()
                    field2 = item.get("inhoud")
                if field1 and field2:
                    text_pairs.append((field1, field2))

    return text_pairs


def run_ner(text_pairs: list[tuple[str, str]]) -> tuple[set[str], set[str]]:
    nlp = spacy.load("nl_core_news_lg")

    names = set()
    locations = set()
    for pair in tqdm(text_pairs, desc="run ner"):
        name = pair[0]
        if "," in name:
            name = put_van_der_in_front(name)
        names.add(name)

        doc = nlp(pair[1])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                names.add(ent.text)
            elif ent.label_ == "GPE" or ent.label_ == "LOC":
                locations.add(ent.text)

    logger.info(f"Found {len(names)} names and {len(locations)} locations")

    return names, locations


def put_van_der_in_front(name: str) -> str:
    return " ".join(name.split(",")[::-1]).strip()


def clean(names: list[str]):
    titles_to_remove = (
        "jvr ",
        "jhr",
        "jonker ",
        "jonge ",
        "jonkheer ",
        "jonkvrouw ",
        "juffr ",
        "jonghe ",
        "hertog ",
        "hertogin ",
        "here ",
        "heren ",
        "heere ",
        "heer ",
        "grote ",
        "gravin ",
        "graaf ",
        "frère ",
        "fils de ",
        "filius ",
        "filii ",
        "filie ",
        "dr ",
    )
    out = []
    for name in names:
        name = _remove_double_spaces(name)
        name = " ".join(name.split(" ")[1:]) if name.startswith(titles_to_remove) else name
        name = _remove_double_spaces(name)
        if not name or not name_starts_with_capital_letter(name):
            continue
        out.append(name)
    out = sorted(set(out))
    return out


def _remove_double_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def name_starts_with_capital_letter(name: str) -> bool:
    if not name[0].islower():
        return True
    voorvoegsels = ("van ", "von ", "der ", "den ", "de ", "d' ")
    if name.startswith(voorvoegsels):
        name = " ".join(name.split(" ")[1:])
        return name_starts_with_capital_letter(name)
    return False


def store_in_elasticsearch(names: list[str]):
    processor = DocProcessor()
    processor.register_index(NamesNerDoc)
    for name in names:
        doc = NamesNerDoc(name=name)
        processor.add(doc)
    processor.finalize()


def main():
    logging_setup()
    setup_es_connection()

    text_pairs = create_dataset()
    names, locations = run_ner(text_pairs)
    names_cleaned = clean(list(names))
    with open("names_vergelijk.txt", "w") as f:
        for name in names_cleaned:
            print(name, f)
    store_in_elasticsearch(names_cleaned)


if __name__ == "__main__":
    main()
