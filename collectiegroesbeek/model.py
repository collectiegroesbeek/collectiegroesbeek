from typing import Optional, List

from elasticsearch_dsl import Document, Text, Keyword, Short


class CardNameIndex(Document):
    datum = Text(norms=False)
    naam = Text(norms=False)
    inhoud = Text(norms=False)
    bron = Text(norms=False)
    getuigen = Text(norms=False)
    bijzonderheden = Text(norms=False)

    naam_keyword = Keyword()
    jaar = Short()

    @classmethod
    def from_csv_line(cls, line: List[str]) -> 'CardNameIndex':
        doc = cls()
        doc.meta['id'] = int(line[0]) if len(line[0]) > 0 else None
        doc.meta['index'] = 'namenindex'
        doc.datum = cls.parse_entry(line[1])
        doc.naam = cls.parse_entry(line[2])
        doc.inhoud = cls.parse_entry(line[3])
        doc.bron = cls.parse_entry(line[4])
        doc.getuigen = cls.parse_entry(line[5])
        doc.bijzonderheden = cls.parse_entry(line[6])
        if not doc.valid:
            return doc
        if doc.naam is not None:
            doc.naam_keyword = cls.create_name_keyword(str(doc.naam))
        if doc.datum is not None:
            doc.jaar = cls.create_year(str(doc.datum))
        return doc

    @property
    def valid(self):
        # At the end of a file there may be empty lines, skip them.
        if self.meta['id'] is None:
            return False
        # Skip row if there is no data except an id. This happens a lot at the end of a file.
        if self.naam is None and self.datum is None:
            return False
        return True

    @staticmethod
    def parse_entry(entry: str) -> Optional[str]:
        return entry.strip() or None

    @staticmethod
    def create_name_keyword(naam: str) -> str:
        """Get a single keyword from the name field."""
        # todo: fix this one: Albrecht (St), van
        if len(naam.split(',')) >= 2:
            return naam.split(',')[0]
        elif len(naam.split('~')) >= 2:
            return naam.split('~')[0]
        elif len(naam.split(' ')) >= 2:
            return naam.split(' ')[0]
        else:
            return naam

    @staticmethod
    def create_year(datum: str) -> Optional[int]:
        """Parse a year from the datum field."""
        if datum is None or len(datum) < 4 or not datum[:4].isdigit():
            return None
        jaar = int(datum[:4])
        if 1000 < jaar < 2000:
            return jaar
        return None
