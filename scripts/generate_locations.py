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
    collect: dict[str, dict[str, int]] = {}
    # get counts and normalize casing
    for location in locations:
        location = location.lower()
        collect.setdefault(location, {location: 0})
        collect[location][location] += 1

    # merge common different spellings
    spelling_equivalents = [
        ("aa", "ae"),
        ("ae", "ai"),
        ("ae", "ee"),
        ("ll", "l"),
        ("ij", "y"),
        ("eeg", "ege"),
        ("acht", "aft"),
        ("en", "e"),
        ("ne", "n"),
        ("i", "y"),
        ("f", "v"),
        ("er", "e"),
        ("y", "hi"),
        ("pp", "p"),
        ("ede", "ee"),
        ("aef", "av"),
        ("hy", "y"),
        ("ees", "eis"),
        ("ern", "er"),
        ("cse", "cx"),
        ("ck", "cx"),
        ("ck", "c"),
        ("k", "ck"),
        ("c", "k"),
        ("ss", "s"),
        ("u", "ue"),
        ("z", "s"),
        ("ijk", "yck"),
        ("s", ""),
        (" ", ""),
    ]
    for one, two in chain(spelling_equivalents, ((b, a) for a, b in spelling_equivalents)):
        if not one:
            continue
        for key in list(collect.keys()):
            alt_key = key.replace(one, two)
            if alt_key != key and alt_key in collect:
                for group_key, group in collect.items():
                    if alt_key in group:
                        collect[key].update(group)
                        collect[group_key] = collect[key]

    unique_items: list[dict[str, int]] = keep_only_unique(collect)
    sorted_items = [dict(sorted(d.items(), key=lambda x: x[1], reverse=True)) for d in unique_items]
    return sorted_items


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
            location=location.title(),
            variants=[variant.title() for variant in item.keys()],
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
