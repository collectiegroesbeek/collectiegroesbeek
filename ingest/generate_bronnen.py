import logging
import re
from collections import defaultdict

from elasticsearch_dsl import Index
from tqdm import tqdm

from collectiegroesbeek.controller import get_index_from_alias
from collectiegroesbeek.model import BronDoc
from ingest.ingest_pkg import logging_setup
from ingest.ingest_pkg.dataloader import iter_csv_files, iter_csv_file_items
from ingest.ingest_pkg.elasticsearch_utils import setup_es_connection, DocProcessor


logger = logging.getLogger(__name__)


def load_bronnen() -> dict[str, int]:
    bronnen: dict[str, int] = defaultdict(lambda: 0)
    for filepath, filename in iter_csv_files():
        for item in iter_csv_file_items(filepath=filepath):
            try:
                bron = item["bron"]
            except KeyError:
                continue
            bronnen[bron] += 1
    return bronnen


def process_bronnen(bronnen: dict[str, int]) -> dict[str, int]:
    out: dict[str, int] = defaultdict(lambda: 0)
    for multibron, count in bronnen.items():
        bronnen_prefix = split_multibron(multibron)
        for bron_prefix in bronnen_prefix:
            if not bron_prefix:
                continue
            out[bron_prefix] += count
    return out


def split_multibron(multibron: str) -> list[str]:
    bronnen = [bron.strip() for bron in multibron.split(";")]
    # remove subbron
    bronnen = [re.split(r"/\s?(?=\w)", bron)[0].strip() for bron in bronnen]
    # remove numbers
    bronnen = [
        re.sub(r"\b(?:fol|p|regest|bl|reg|dossier|no) [\d\s,v]+\b", "", bron).strip()
        for bron in bronnen
    ]
    return bronnen


def store_in_elasticsearch(bronnen: dict[str, int]):
    processor = DocProcessor()
    processor.register_index(BronDoc)
    for bron, count in tqdm(bronnen.items(), desc="store in ES", total=len(bronnen)):
        doc = BronDoc(
            bron=bron,
            bron_parts=bron.lower().split(" "),
            count=count,
        )
        processor.add(doc)
    processor.finalize()

    if len(bronnen) > 10_000:
        index = Index(get_index_from_alias(BronDoc.Index.name))
        index.settings(max_result_window=int(len(bronnen) * 1.1))
        index.save()


def main():
    logging_setup()
    setup_es_connection()

    bronnen = load_bronnen()
    bronnen = process_bronnen(bronnen)
    store_in_elasticsearch(bronnen)


if __name__ == "__main__":
    main()
