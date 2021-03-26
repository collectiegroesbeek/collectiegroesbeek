import re
from typing import Optional, List, Type

from elasticsearch_dsl import Document, Index, Text, Keyword, Short


class BaseDocument(Document):

    class Index:
        name: str = ''

    @classmethod
    def _matches(cls, hit):
        # override _matches to match indices in a pattern instead of just ALIAS
        # hit is the raw dict as returned by elasticsearch
        return bool(re.match(cls.Index.name + r'_\d{10}', hit['_index']))

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['BaseDocument']:
        raise NotImplementedError()

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        raise NotImplementedError()

    @staticmethod
    def get_index_name_pretty() -> str:
        raise NotImplementedError()

    def get_title(self) -> str:
        raise NotImplementedError()

    def get_subtitle(self) -> str:
        raise NotImplementedError()

    def get_body_lines(self) -> List[str]:
        raise NotImplementedError()


class CardNameDoc(BaseDocument):
    datum: Optional[str] = Text()
    naam: Optional[str] = Text()
    inhoud: Optional[str] = Text()
    bron: Optional[str] = Text()
    getuigen: Optional[str] = Text()
    bijzonderheden: Optional[str] = Text()

    naam_keyword: Optional[str] = Keyword()
    jaar: Optional[int] = Short()

    class Index:
        name: str = 'namenindex'

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
            doc.naam_keyword = create_name_keyword(str(doc.naam))
        if doc.datum is not None:
            doc.jaar = create_year(str(doc.datum))
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
    def get_multimatch_fields() -> List[str]:
        return ['naam^3', 'datum^3', 'inhoud^2', 'getuigen', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return 'Namenindex'

    def get_title(self) -> str:
        return '{} | {}'.format(self.naam or '', self.datum or '')

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [self.inhoud, self.getuigen, self.bijzonderheden]
        return [value for value in out if value]


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


def create_year(datum: str) -> Optional[int]:
    """Parse a year from the datum field."""
    if datum is None or len(datum) < 4 or not datum[:4].isdigit():
        return None
    jaar = int(datum[:4])
    if 1000 < jaar < 2000:
        return jaar
    return None


class VoornamenDoc(BaseDocument):
    datum: Optional[str] = Text(fields={'keyword': Keyword()})
    voornaam: Optional[str] = Text(fields={'keyword': Keyword()})
    patroniem: Optional[str] = Text(fields={'keyword': Keyword()})
    inhoud: Optional[str] = Text(fields={'keyword': Keyword()})
    bron: Optional[str] = Text(fields={'keyword': Keyword()})
    getuigen: Optional[str] = Text(fields={'keyword': Keyword()})
    bijzonderheden: Optional[str] = Text(fields={'keyword': Keyword()})

    jaar: Optional[int] = Short()

    class Index:
        name: str = 'voornamenindex'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['VoornamenDoc']:
        doc = cls()
        if len(line[0]) == 0:
            return None
        doc.meta.id = int(line[0])
        doc.datum = parse_entry(line[1])
        doc.voornaam = parse_entry(line[2])
        doc.patroniem = parse_entry(line[3])
        doc.inhoud = parse_entry(line[4])
        doc.bron = parse_entry(line[5])
        doc.getuigen = parse_entry(line[6])
        doc.bijzonderheden = parse_entry(line[7])
        if not doc.is_valid():
            return None
        if doc.datum is not None:
            doc.jaar = create_year(str(doc.datum))
        return doc

    def is_valid(self):
        # At the end of a file there may be empty lines, skip them.
        if getattr(self.meta, 'id', None) is None:
            return False
        # Skip row if there is no data except an id. This happens a lot at the end of a file.
        if self.voornaam is None and self.datum is None:
            return False
        return True

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        return ['voornaam^3', 'patroniem^3', 'datum^3', 'inhoud^2', 'getuigen', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return 'Voornamenindex'

    def get_title(self) -> str:
        return '{} {} | {}'.format(self.voornaam or '', self.patroniem or '', self.datum or '')

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [self.inhoud, self.getuigen, self.bijzonderheden]
        return [value for value in out if value]


class JaartallenDoc(BaseDocument):
    datum: Optional[str] = Text()
    inhoud: Optional[str] = Text()
    bron: Optional[str] = Text()
    getuigen: Optional[str] = Text()
    bijzonderheden: Optional[str] = Text()

    jaar: Optional[int] = Short()

    class Index:
        name: str = 'jaartallenindex'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['JaartallenDoc']:
        doc = cls()
        if len(line[0]) == 0:
            return None
        doc.meta.id = int(line[0])
        doc.datum = parse_entry(line[1])
        doc.inhoud = parse_entry(line[2])
        doc.bron = parse_entry(line[3])
        doc.getuigen = parse_entry(line[4])
        doc.bijzonderheden = parse_entry(line[5])
        if not doc.is_valid():
            return None
        if doc.datum is not None:
            doc.jaar = create_year(str(doc.datum))
        return doc

    def is_valid(self):
        # At the end of a file there may be empty lines, skip them.
        if getattr(self.meta, 'id', None) is None:
            return False
        # Skip row if there is no data except an id. This happens a lot at the end of a file.
        if self.datum is None:
            return False
        return True

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        return ['datum^3', 'inhoud^2', 'getuigen', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return 'Jaartallenindex'

    def get_title(self) -> str:
        return '{}'.format(self.datum or '')

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [self.inhoud, self.getuigen, self.bijzonderheden]
        return [value for value in out if value]


class HeemskerkMaatboekDoc(BaseDocument):
    locatie: Optional[str] = Text(fields={'keyword': Keyword()})
    sector: Optional[str] = Text(fields={'keyword': Keyword()})

    eigenaar: Optional[str] = Text(fields={'keyword': Keyword()})
    huurder: Optional[str] = Text(fields={'keyword': Keyword()})

    oppervlakte: Optional[str] = Text(fields={'keyword': Keyword()})
    prijs: Optional[str] = Text(fields={'keyword': Keyword()})

    datum: Optional[str] = Text(fields={'keyword': Keyword()})
    jaar: Optional[int] = Short()

    bron: Optional[str] = Text(fields={'keyword': Keyword()})
    opmerkingen: Optional[str] = Text(fields={'keyword': Keyword()})

    class Index:
        name: str = 'heemskerk_maatboek_index'

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

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        return ['locatie^3', 'sector^3', 'datum^3', 'eigenaar^2', 'huurder^2', 'oppervlakte', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return 'Maatboek Heemskerk'

    def get_title(self) -> str:
        title = self.sector or self.locatie or self.eigenaar or self.huurder or ''
        if self.datum:
            title += ' | ' + self.datum
        return title

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [
            self.locatie,
            self.sector,
            'eigenaar: ' + self.eigenaar if self.eigenaar else None,
            'huurder: ' + self.huurder if self.huurder else None,
            self.oppervlakte,
            self.prijs,
            self.opmerkingen,
        ]
        return [value for value in out if value]


class HeemskerkAktenDoc(BaseDocument):

    class Index:
        name = 'heemskerk_akten_index'

        def __new__(cls):
            return Index(name=cls.name)

    # TODO: finish this stub


def parse_entry(entry: str) -> Optional[str]:
    return entry.strip() or None


def list_doctypes() -> List[Type[BaseDocument]]:
    return [CardNameDoc, VoornamenDoc, JaartallenDoc, HeemskerkMaatboekDoc]


# MAPPING = {
#     doctype.Index.name: doctype
#     for doctype in list_doctypes()
# }
#
#
# def index_to_doctype(index_name: str) -> Type[BaseDocument]:
#     # remove optional timestamp
#     index_name = re.sub(r'_\d{10}', '', index_name)
#     return MAPPING[index_name]
