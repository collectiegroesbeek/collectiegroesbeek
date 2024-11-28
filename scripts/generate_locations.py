from itertools import chain
import logging

from tqdm import tqdm

from collectiegroesbeek.model import LocationDoc
from ingest import logging_setup
from ingest.dataloader import iter_csv_files, iter_csv_file_items
from ingest.elasticsearch_utils import setup_es_connection, DocProcessor
from ingest.locations import extract_location

logger = logging.getLogger(__name__)


def load_texts() -> list[str]:
    texts: list[str] = []
    for filepath, filename in iter_csv_files():
        if filename == "Coll Gr 9 Haarlem Transportregister.csv":
            for item in iter_csv_file_items(filepath=filepath):
                texts.append(item["inhoud"])
    return texts


def extract_locations(texts: list[str]) -> list[str]:
    locations: list[str] = []
    for text in texts:
        locations.extend(extract_location(text))
    return locations


def merge_locations(locations: list[str]) -> list[dict[str, int]]:
    collect = {}
    # first pass: just store everything
    for location in locations:
        if location not in collect:
            collect[location] = {location: 1}
        else:
            collect[location][location] += 1

    # second pass: merge lowercase into uppercase, then make all keys lowercase
    for key in list(collect.keys()):
        alt_key = key.lower()
        add_if(collect=collect, key=key, alt_key=alt_key)
    collect = {key.lower(): d for key, d in collect.items()}

    # merge common different spellings
    spelling_equivalents = [("aa", "ae"), ("ij", "y"), ("eeg", "ege"), ("acht", "aft"), ("en", "e"), ("i", "y"), ("f", "v"), ("er", "e"), ("y", "hi"), ("pp", "p"),
                            ("ck", "cx"), ("ck", "c"), ("k", "ck"), ("c", "k"), ("ss", "s"), ("u", "ue"), ("z", "s"), ("ijk", "yck"), ("s", ""), (" ", "")]
    for one, two in chain(spelling_equivalents, ((b, a) for a, b in spelling_equivalents)):
        if not one:
            continue
        for key in list(collect.keys()):
            alt_key = key.replace(one, two)
            add_if(collect=collect, key=key, alt_key=alt_key)

    unique_items: list[dict[str, int]] = keep_only_unique(collect)
    sorted_items = [dict(sorted(d.items(), key=lambda x: x[1], reverse=True)) for d in unique_items]
    return sorted_items


def add_if(collect: dict, key: str, alt_key: str):
    if alt_key != key and alt_key in collect:
        for group_key, group in collect.items():
            if alt_key in group:
                collect[key].update(group)
                collect[group_key] = collect[key]


def keep_only_unique(collect: dict[str, dict[str, int]]) -> list[dict[str, int]]:
    for i, d in enumerate(collect.values()):
        d["id"] = i
    unique = {d["id"]: d for d in collect.values()}
    out = list(unique.values())
    for item in out:
        item.pop("id")
    return out


def merge_nodes(collect: dict[str, dict[str, int]]):
    pass


def store_in_elasticsearch(collections: list[dict[str, int]]):
    processor = DocProcessor()
    processor.register_index(LocationDoc)
    for item in tqdm(collections, desc="store in ES"):
        location = sorted(item.items(), key=lambda x: x[1], reverse=True)[0][0]
        doc = LocationDoc(
            location=location,
            variants=list(item.keys()),
            variant_counts=list(item.values()),
        )
        processor.add(doc)
    processor.finalize()


def main():
    logging_setup()
    setup_es_connection()

    texts = load_texts()
    locations = extract_locations(texts)
    collections = merge_locations(locations)
    store_in_elasticsearch(collections)


if __name__ == "__main__":
    main()
