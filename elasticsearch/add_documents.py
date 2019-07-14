import os
import logging
import sys
import csv
import argparse

from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections
import tqdm

from collectiegroesbeek.model import CardNameIndex


if sys.version_info[0] < 3:
    raise ImportError('Python < 3 is not supported.')


connections.create_connection(hosts=['localhost:9203'])


def logging_setup():
    log_format = '%(asctime)s - %(levelname)-8s - %(name)s - %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)


def reset_index():
    index = CardNameIndex.Index()
    if index.exists():
        index.delete()
    CardNameIndex.init()
    assert index.exists()


class CardProcessor:

    def __init__(self, batch_size=500):
        self.batch_size = batch_size
        self.client = connections.get_connection()
        self._items = []

    def add(self, card: CardNameIndex):
        self._items.append(card.to_dict(include_meta=True))
        if len(self._items) > self.batch_size:
            self.flush()

    def flush(self):
        if len(self._items) > 0:
            bulk(self.client, self._items)
        self._items = []


def run(path):
    reset_index()
    card_processor = CardProcessor()
    filenames = sorted(filename for filename in os.listdir(path) if filename.endswith('.csv'))
    pbar = tqdm.tqdm(filenames)
    for filename in pbar:
        pbar.set_postfix(filename=filename)
        filepath = os.path.join(path, filename)
        with open(filepath, newline='\r\n', encoding='utf-16') as f:
            csvreader = csv.reader(f, dialect=csv.excel_tab)
            for line in csvreader:
                if line[0] == 'id':  # First line contains header
                    continue
                card = CardNameIndex.from_csv_line(line)
                if not card.is_valid():
                    continue
                card_processor.add(card)
    card_processor.flush()


if __name__ == '__main__':
    logging_setup()
    assert connections.get_connection().ping()
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default='../collectiegroesbeek-data',
                        help='Folder with the CSV data files.')
    options = parser.parse_args()
    run(path=options.path)
