import re
from typing import Optional, List

from elasticsearch_dsl import Document, Index, Text, Keyword, Short


class BaseDocument(Document):

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['BaseDocument']:
        raise NotImplementedError()


class CardNameDoc(BaseDocument):
    datum = Text(norms=False)
    naam = Text(norms=False)
    inhoud = Text(norms=False)
    bron = Text(norms=False)
    getuigen = Text(norms=False)
    bijzonderheden = Text(norms=False)

    naam_keyword = Keyword()
    jaar = Short()

    class Index:
        name = 'namenindex'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['CardNameDoc']:
        doc = cls()
        if len(line[0]) == 0:
            return None
        doc.meta.id = int(line[0])
        doc.datum = parse_entry(line[1])
        doc.naam = parse_entry(line[2])
        doc.inhoud = parse_entry(line[3])
        doc.bron = parse_entry(line[4])
        doc.getuigen = parse_entry(line[5])
        doc.bijzonderheden = parse_entry(line[6])
        if not doc.is_valid():
            return None
        if doc.naam is not None:
            doc.naam_keyword = cls.create_name_keyword(str(doc.naam))
        if doc.datum is not None:
            doc.jaar = cls.create_year(str(doc.datum))
        return doc

    def is_valid(self):
        # At the end of a file there may be empty lines, skip them.
        if getattr(self.meta, 'id', None) is None:
            return False
        # Skip row if there is no data except an id. This happens a lot at the end of a file.
        if self.naam is None and self.datum is None:
            return False
        return True

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


class HeemskerkMaatboekDoc(BaseDocument):
    locatie = Text(fields={'keyword': Keyword()}, norms=False)
    sector = Text(fields={'keyword': Keyword()}, norms=False)

    eigenaar = Text(fields={'keyword': Keyword()}, norms=False)
    huurder = Text(fields={'keyword': Keyword()}, norms=False)

    oppervlakte = Keyword()
    prijs = Keyword()

    datum = Text(fields={'keyword': Keyword()}, norms=False)
    jaar = Short()

    bron = Text(fields={'keyword': Keyword()}, norms=False)
    opmerkingen = Text(norms=False)

    class Index:
        name = 'heemskerk_maatboek_index'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['HeemskerkMaatboekDoc']:
        # Return early, we'll discard it later using `is_valid`.
        if not parse_entry(line[0]) or not any(parse_entry(value) for value in line[1:]):
            return None
        doc = cls()
        doc.meta.id = line[0]
        doc.locatie = parse_entry(line[1])
        doc.sector = parse_entry(line[2])
        doc.oppervlakte = parse_entry(line[3])
        doc.eigenaar = parse_entry(line[4])
        doc.huurder = parse_entry(line[5])
        doc.prijs = parse_entry(line[6])
        doc.datum = parse_entry(line[7])
        doc.bron = parse_entry(line[8])
        doc.opmerkingen = parse_entry(line[9])
        doc.jaar = cls.parse_year(doc.datum)
        return doc

    @staticmethod
    def parse_year(datum: Optional[str]) -> Optional[int]:
        res = re.search(r'\d{4}', datum or '')
        return int(res[0]) if res else None


class HeemskerkAktenDoc(BaseDocument):

    class Index:
        name = 'heemskerk_akten_index'

        def __new__(cls):
            return Index(name=cls.name)

    # TODO: finish this stub


def parse_entry(entry: str) -> Optional[str]:
    return entry.strip() or None
