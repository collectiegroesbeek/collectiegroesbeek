import argparse
import csv
import logging
import os
import sys
import time
from typing import Dict, Optional, Type

from elasticsearch.helpers import bulk
from elasticsearch_dsl import Index, connections
import tqdm

from collectiegroesbeek.model import (
    BaseDocument,
    CardNameDoc,
    EigendomsaktenHeemskerk,
    JaartallenDoc,
    MaatboekBroekInWaterlandDoc,
    MaatboekHeemskerkDoc,
    MaatboekHeemstedeDoc,
    MaatboekSuderwoude,
    TransportRegisterBloemendaalDoc,
    TransportRegisterEgmondDoc,
    VoornamenDoc,
)

if sys.version_info[0] < 3:
    raise ImportError('Python < 3 is not supported.')


connections.create_connection(hosts=['localhost:9200'])


def logging_setup():
    log_format = '%(asctime)s - %(levelname)-8s - %(name)s - %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)


class CardProcessor:

    def __init__(self, batch_size=500):
        self.batch_size = batch_size
        self.client = connections.get_connection()
        self._movers: Dict[str, IndexMover] = {}
        self._items = []

    def register_index(self, doctype):
        """Mark an index as being updated, creating an IndexMover instance."""
        key = doctype.Index.name
        if key in self._movers:
            return
        self._movers[key] = IndexMover(doctype)

    def add(self, card: BaseDocument):
        d = card.to_dict(include_meta=True)
        d['_index'] = self._movers[d['_index']].new_name
        self._items.append(d)
        if len(self._items) > self.batch_size:
            self.flush()

    def flush(self):
        if len(self._items) > 0:
            bulk(self.client, self._items)
        self._items = []

    def finalize(self):
        self.flush()
        for mover in self._movers.values():
            mover.move_alias_to_new()


class IndexMover:

    def __init__(self, doctype: Type[BaseDocument]):
        self.alias = doctype.Index.name
        if doctype.Index().exists():
            self.old_name = next(iter(doctype.Index().get_alias().keys()))
            self.old_es_index: Optional[Index] = Index(name=self.old_name)
        else:
            self.old_es_index = None
            self.old_name = None
        self.new_name = '{}_{:.0f}'.format(self.alias, time.time())
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
    if filename.startswith('coll gr 6 egmond transportregister'):
        return TransportRegisterEgmondDoc
    elif filename.startswith('coll gr 7 bloemendaal transportregister'):
        return TransportRegisterBloemendaalDoc
    elif filename.startswith(('heemskerk maatboek', 'maatboek heemskerk')):
        return MaatboekHeemskerkDoc
    elif filename.startswith('maatboek heemstede'):
        return MaatboekHeemstedeDoc
    elif filename.startswith('maatboek broek in waterland'):
        return MaatboekBroekInWaterlandDoc
    elif filename.startswith('maatboek suderwoude'):
        return MaatboekSuderwoude
    elif filename.startswith('heemskerk eigendomsakten'):
        return EigendomsaktenHeemskerk
    if filename.startswith('coll gr'):
        if 'voornamen' in filename:
            return VoornamenDoc
        elif 'jaartallen' in filename:
            return JaartallenDoc
        return CardNameDoc
    else:
        raise ValueError('Cannot determine doctype from filename "{}"'.format(filename))


def run(path, doctype_name: Optional[str]):
    processor = CardProcessor()
    filenames = sorted(filename for filename in os.listdir(path) if filename.endswith('.csv'))
    pbar = tqdm.tqdm(filenames)
    for filename in pbar:
        pbar.set_postfix(filename=filename)
        doctype = filename_to_doctype(filename)
        if doctype_name and doctype.__name__ != doctype_name:
            continue
        processor.register_index(doctype)
        filepath = os.path.join(path, filename)
        with open(filepath) as f:
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


if __name__ == '__main__':
    logging_setup()
    assert connections.get_connection().ping()
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default='../collectiegroesbeek-data',
                        help='Folder with the CSV data files.')
    parser.add_argument('--doctype', required=False, help='Limit ingestion to this index only')
    options = parser.parse_args()
    run(path=options.path, doctype_name=options.doctype)
