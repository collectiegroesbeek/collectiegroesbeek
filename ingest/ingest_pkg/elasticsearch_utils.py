import time
from typing import Type, Optional

from dotenv import dotenv_values
from elasticsearch_dsl import Index, Document
from elasticsearch_dsl.connections import connections


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
