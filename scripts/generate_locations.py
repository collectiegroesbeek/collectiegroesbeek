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
    locations = set()
    for text in texts:
        locations.update(extract_location(text))
    return list(locations)


def store_in_elasticsearch(locations: list[str]):
    processor = DocProcessor()
    processor.register_index(LocationDoc)
    for location in tqdm(locations, desc="store in ES", total=len(locations)):
        doc = LocationDoc(
            location=location,
        )
        processor.add(doc)
    processor.finalize()


def main():
    logging_setup()
    setup_es_connection()

    texts = load_texts()
    locations = extract_locations(texts)
    store_in_elasticsearch(locations)


if __name__ == "__main__":
    main()
