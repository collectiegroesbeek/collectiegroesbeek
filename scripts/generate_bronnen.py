import logging
from collections import defaultdict

from elasticsearch_dsl import Index
from tqdm import tqdm

from collectiegroesbeek.controller import get_index_from_alias
from collectiegroesbeek.model import BronDoc
from ingest import logging_setup
from ingest.bronnen import split_multibron
from ingest.dataloader import iter_csv_file_items, iter_csv_files
from ingest.elasticsearch_utils import DocProcessor, setup_es_connection

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
            if len(bron_prefix) < 5:
                # bit of a hack to remove some garbage like just numbers
                continue
            out[bron_prefix] += count
    return out


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
