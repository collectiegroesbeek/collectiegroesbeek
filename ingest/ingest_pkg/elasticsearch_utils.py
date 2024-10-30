import logging
import time
from typing import Type, Optional, Dict

from dotenv import dotenv_values
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Index, Document
from elasticsearch_dsl.connections import connections


logger = logging.getLogger(__name__)


def setup_es_connection():
    connections.create_connection(hosts=[dotenv_values(".env")["elasticsearch_host"]])
    assert connections.get_connection().ping()


class IndexMover:
    def __init__(self, doctype: Type[Document]):
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


class DocProcessor:
    def __init__(self, batch_size=500, dryrun: bool = False):
        self.batch_size = batch_size
        self.dryrun = dryrun
        self.client = connections.get_connection()
        self._movers: Dict[str, IndexMover] = {}
        self._items: list[dict] = []
        self._count = 0

    def register_index(self, doctype: Type[Document]):
        """Mark an index as being updated, creating an IndexMover instance."""
        key = doctype.Index.name
        if key in self._movers:
            return
        if not self.dryrun:
            self._movers[key] = IndexMover(doctype)

    def add(self, doc: Document):
        d = doc.to_dict(include_meta=True)
        if not self.dryrun:
            d["_index"] = self._movers[d["_index"]].new_name
        self._items.append(d)
        if len(self._items) > self.batch_size:
            self.flush()

    def flush(self):
        if len(self._items) > 0 and not self.dryrun:
            bulk(self.client, self._items)
            self._count += len(self._items)
        self._items = []

    def finalize(self):
        self.flush()
        for mover in self._movers.values():
            mover.move_alias_to_new()
        logger.info("Pushed %d docs to %s", self._count, ", ".join(x.new_name for x in self._movers.values()))
