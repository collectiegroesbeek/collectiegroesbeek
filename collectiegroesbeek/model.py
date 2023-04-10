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

    @staticmethod
    def get_description() -> str:
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
        return 'Achternamenindex'

    def get_title(self) -> str:
        return '{} | {}'.format(self.naam or '', self.datum or '')

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [self.inhoud, self.getuigen, self.bijzonderheden]
        return [value for value in out if value]

    @staticmethod
    def get_description() -> str:
        return "Nederlandse achternamen vanaf middeleeuwen tot ± 1800, zie ook de knop Namenlijst"


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

    @staticmethod
    def get_description() -> str:
        return (
            "(Nederlandse voornamen met patroniem, meestal zonder geslachtsnaam, vanaf "
            "middeleeuwen tot ± 1800, zie ook de knop namenlijst"
        )



class JaartallenDoc(BaseDocument):
    datum: Optional[str] = Text(fields={'keyword': Keyword()})
    locatie: Optional[str] = Text(fields={'keyword': Keyword()})
    inhoud: Optional[str] = Text()
    bron: Optional[str] = Text(fields={'keyword': Keyword()})
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
        doc.locatie = parse_entry(line[2])
        doc.inhoud = parse_entry(line[3])
        doc.bron = parse_entry(line[4])
        doc.getuigen = parse_entry(line[5])
        doc.bijzonderheden = parse_entry(line[6])
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
        return ['datum^3', 'locatie^3', 'inhoud^2', 'getuigen', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return 'Jaartallenindex'

    def get_title(self) -> str:
        return '{} | {}'.format(self.datum or '', self.locatie or '')

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [self.inhoud, self.getuigen, self.bijzonderheden]
        return [value for value in out if value]

    @staticmethod
    def get_description() -> str:
        return (
            "(akten vanaf middeleeuwen tot ongeveer 1800, gerangschikt op datum, vooral Hollandse "
            "akten, uit archieven van Noord-Holland, Zuid-Holland, Zeeland, en in mindere mate "
            "Utrecht, Zwolle, Arnhem etc, nog niet gereed"
        )



class MaatboekHeemskerkDoc(BaseDocument):
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
    def from_csv_line(cls, line: List[str]) -> Optional['MaatboekHeemskerkDoc']:
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

    @staticmethod
    def get_description() -> str:
        return (
            "Het volledige belastingquohier Heemskerk is verwerkt: 10 e penning 1539, 1561 en 1570,"
            " gerangschikt op sector"
        )


class MaatboekHeemstedeDoc(BaseDocument):
    ligging: Optional[str] = Text(fields={'keyword': Keyword()})
    eigenaar: Optional[str] = Text(fields={'keyword': Keyword()})
    huurder: Optional[str] = Text(fields={'keyword': Keyword()})
    prijs: Optional[str] = Text(fields={'keyword': Keyword()})
    datum: Optional[str] = Text(fields={'keyword': Keyword()})
    jaar: Optional[int] = Short()
    bron: Optional[str] = Text(fields={'keyword': Keyword()})
    opmerkingen: Optional[str] = Text(fields={'keyword': Keyword()})

    class Index:
        name: str = 'maatboek_heemstede_index'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['MaatboekHeemstedeDoc']:
        # Return early, we'll discard it later using `is_valid`.
        if not any(parse_entry(value) for value in line[1:]):
            return None
        doc = cls()
        doc.meta.id = line[0]
        doc.ligging = parse_entry(line[1])
        doc.eigenaar = parse_entry(line[2])
        doc.huurder = parse_entry(line[3])
        doc.prijs = parse_entry(line[4])
        doc.datum = parse_entry(line[5])
        doc.bron = parse_entry(line[6])
        doc.opmerkingen = parse_entry(line[7])
        doc.jaar = cls.parse_year(doc.datum)
        return doc

    @staticmethod
    def parse_year(datum: Optional[str]) -> Optional[int]:
        res = re.search(r'\d{4}', datum or '')
        return int(res[0]) if res else None

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        return ['liggng^3', 'datum^3', 'eigenaar^2', 'huurder^2', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return 'Maatboek Heemstede'

    def get_title(self) -> str:
        title = self.ligging or self.eigenaar or self.huurder or ''
        if self.datum:
            title += ' | ' + self.datum
        return title

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [
            self.ligging,
            'eigenaar: ' + self.eigenaar if self.eigenaar else None,
            'huurder: ' + self.huurder if self.huurder else None,
            self.prijs,
            self.opmerkingen,
        ]
        return [value for value in out if value]

    @staticmethod
    def get_description() -> str:
        return (
            "Maatboek 1544 en Register 10 e penning 1561, eigenaren en huurders van land en huizen"
        )


class MaatboekBroekInWaterlandDoc(BaseDocument):
    sector: Optional[str] = Text(fields={'keyword': Keyword()})
    ligging: Optional[str] = Text(fields={'keyword': Keyword()})
    oppervlakte: Optional[str] = Text(fields={'keyword': Keyword()})
    eigenaar: Optional[str] = Text(fields={'keyword': Keyword()})
    datum: Optional[str] = Text(fields={'keyword': Keyword()})
    jaar: Optional[int] = Short()
    bron: Optional[str] = Text(fields={'keyword': Keyword()})
    opmerkingen: Optional[str] = Text(fields={'keyword': Keyword()})

    class Index:
        name: str = 'maatboek_broek_in_waterland_index'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['MaatboekBroekInWaterlandDoc']:
        # Return early, we'll discard it later using `is_valid`.
        if not any(parse_entry(value) for value in line[1:]):
            return None
        doc = cls()
        doc.meta.id = line[0]
        doc.sector = parse_entry(line[1])
        doc.ligging = parse_entry(line[2])
        doc.oppervlakte = parse_entry(line[3])
        doc.eigenaar = parse_entry(line[4])
        doc.datum = parse_entry(line[5])
        doc.bron = parse_entry(line[6])
        doc.opmerkingen = parse_entry(line[7])
        doc.jaar = cls.parse_year(doc.datum)
        return doc

    @staticmethod
    def parse_year(datum: Optional[str]) -> Optional[int]:
        res = re.search(r'\d{4}', datum or '')
        return int(res[0]) if res else None

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        return ['sector^3', 'ligging^3', 'datum^3', 'eigenaar^2', 'oppervlakte', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return 'Maatboek Broek in Waterland'

    def get_title(self) -> str:
        title = self.sector or self.ligging or self.eigenaar or ''
        if self.datum:
            title += ' | ' + self.datum
        return title

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [
            self.sector,
            self.ligging,
            self.oppervlakte,
            'eigenaar: ' + self.eigenaar if self.eigenaar else None,
            self.opmerkingen,
        ]
        return [value for value in out if value]

    @staticmethod
    def get_description() -> str:
        return "Inventaris Hoogheemraadschap Waterland no 63, 1589, in sectoren"


class MaatboekSuderwoude(BaseDocument):
    sector: Optional[str] = Text(fields={'keyword': Keyword()})
    ligging: Optional[str] = Text(fields={'keyword': Keyword()})
    oppervlakte: Optional[str] = Text(fields={'keyword': Keyword()})
    eigenaar: Optional[str] = Text(fields={'keyword': Keyword()})
    datum: Optional[str] = Text(fields={'keyword': Keyword()})
    jaar: Optional[int] = Short()
    bron: Optional[str] = Text(fields={'keyword': Keyword()})
    opmerkingen: Optional[str] = Text(fields={'keyword': Keyword()})

    class Index:
        name: str = 'maatboek_suderwoude_index'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['MaatboekSuderwoude']:
        # Return early, we'll discard it later using `is_valid`.
        if not any(parse_entry(value) for value in line[1:]):
            return None
        doc = cls()
        doc.meta.id = line[0]
        doc.sector = parse_entry(line[1])
        doc.ligging = parse_entry(line[2])
        doc.oppervlakte = parse_entry(line[3])
        doc.eigenaar = parse_entry(line[4])
        doc.datum = parse_entry(line[5])
        doc.bron = parse_entry(line[6])
        doc.opmerkingen = parse_entry(line[7])
        doc.jaar = cls.parse_year(doc.datum)
        return doc

    @staticmethod
    def parse_year(datum: Optional[str]) -> Optional[int]:
        res = re.search(r'\d{4}', datum or '')
        return int(res[0]) if res else None

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        return ['sector^3', 'ligging^3', 'datum^3', 'eigenaar^2', 'oppervlakte', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return 'Maatboek Suderwoude'

    def get_title(self) -> str:
        title = self.sector or self.ligging or self.eigenaar or ''
        if self.datum:
            title += ' | ' + self.datum
        return title

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [
            self.sector,
            self.ligging,
            self.oppervlakte,
            'eigenaar: ' + self.eigenaar if self.eigenaar else None,
            self.opmerkingen,
        ]
        return [value for value in out if value]

    @staticmethod
    def get_description() -> str:
        return "Inventaris Hoogheemraadschap Waterland no 63, 1589, in sectoren"



class EigendomsaktenHeemskerk(BaseDocument):
    datum: Optional[str] = Text(fields={'keyword': Keyword()})
    plaats: Optional[str] = Text(fields={'keyword': Keyword()})
    verkoper: Optional[str] = Text(fields={'keyword': Keyword()})
    koper: Optional[str] = Text(fields={'keyword': Keyword()})
    omschrijving: Optional[str] = Text(fields={'keyword': Keyword()})
    belending: Optional[str] = Text(fields={'keyword': Keyword()})
    bron: Optional[str] = Text(fields={'keyword': Keyword()})
    opmerkingen: Optional[str] = Text(fields={'keyword': Keyword()})

    jaar: Optional[int] = Short()

    class Index:
        name: str = 'eigendomsakten_heemskerk_index'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['EigendomsaktenHeemskerk']:
        # Return early, we'll discard it later using `is_valid`.
        if not any(parse_entry(value) for value in line[1:]):
            return None
        doc = cls()
        doc.meta.id = line[0]
        doc.datum = parse_entry(line[1])
        doc.plaats = parse_entry(line[2])
        doc.verkoper = parse_entry(line[3])
        doc.koper = parse_entry(line[4])
        doc.omschrijving = parse_entry(line[5])
        doc.belending = parse_entry(line[6])
        doc.bron = parse_entry(line[7])
        doc.opmerkingen = parse_entry(line[7])
        doc.jaar = cls.parse_year(doc.datum)
        return doc

    @staticmethod
    def parse_year(datum: Optional[str]) -> Optional[int]:
        res = re.search(r'\d{4}', datum or '')
        return int(res[0]) if res else None

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        return ['datum^3', 'plaats^3', 'verkoper', 'koper', 'omschrijving', 'belending', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return 'Eigendomsakten Heemskerk'

    def get_title(self) -> str:
        title = self.datum or ''
        return title

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [
            'verkoper: ' + self.verkoper if self.verkoper else None,
            'koper: ' + self.koper if self.koper else None,
            self.omschrijving,
            'belending: ' + self.belending if self.belending else None,
            self.opmerkingen,
        ]
        return [value for value in out if value]

    @staticmethod
    def get_description() -> str:
        return (
            "Uit Rijksarchief Haarlem, eigenaren, kopers en verkopers van land, huizen in "
            "Heemskerk in de 16e eeuw"
        )


class TiendeEnHonderdstePenning(BaseDocument):
    datum: str = Text(fields={'keyword': Keyword()})
    inhoud: str = Text(fields={'keyword': Keyword()})
    folio_nr: str = Text(fields={'keyword': Keyword()})
    vervolg_nr: Optional[str] = Text(fields={'keyword': Keyword()})
    bron: str = Text(fields={'keyword': Keyword()})
    bijzonderheden: Optional[str] = Text(fields={'keyword': Keyword()})

    jaar: Optional[int] = Short()

    class Index:
        name: str = 'tiende_en_honderdste_penning'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['TiendeEnHonderdstePenning']:
        # Return early, we'll discard it later using `is_valid`.
        if not any(parse_entry(value) for value in line[1:]):
            return None
        doc = cls()
        doc.meta.id = line[0]
        doc.datum = parse_entry(line[1])
        doc.inhoud = parse_entry(line[2])
        doc.folio_nr = parse_entry(line[3])
        doc.vervolg_nr = parse_entry(line[4])
        doc.bron = parse_entry(line[5])
        doc.bijzonderheden = parse_entry(line[6])
        doc.jaar = cls.parse_year(doc.datum)
        return doc

    @staticmethod
    def parse_year(datum: Optional[str]) -> Optional[int]:
        res = re.search(r'\d{4}', datum or '')
        return int(res[0]) if res else None

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        return ['datum^3', 'inhoud', 'folio_nr', 'vervolg_nr', 'bron']

    @staticmethod
    def get_index_name_pretty():
        return '10e en 100e Penning Bloemendaal'

    def get_title(self) -> str:
        title = self.datum or ''
        return title

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [
            self.inhoud,
            'folio nummer: ' + self.folio_nr,
            'vervolg nummer: ' + self.vervolg_nr if self.vervolg_nr else None,
            self.bijzonderheden,
        ]
        return [value for value in out if value]

    @staticmethod
    def get_description() -> str:
        return (
            "Belastingregister uit Algemeen Rijksarchief betreffende Aelbrechtsberg, Tetrode, "
            "Overveen, Vogelensang, de jaren 1542, 1544, 1558, 1562, 1569"
        )


class BaseTransportregisterDoc(BaseDocument):
    datum: Optional[str] = Text(fields={'keyword': Keyword()})
    inhoud: Optional[str] = Text()
    bron: Optional[str] = Text(fields={'keyword': Keyword()})
    getuigen: Optional[str] = Text()
    bijzonderheden: Optional[str] = Text()

    jaar: Optional[int] = Short()

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['BaseTransportregisterDoc']:
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

    def get_title(self) -> str:
        return '{}'.format(self.datum or '')

    def get_subtitle(self) -> str:
        return self.bron or ''

    def get_body_lines(self) -> List[str]:
        out = [self.inhoud, self.getuigen, self.bijzonderheden]
        return [value for value in out if value]


class TransportRegisterEgmondDoc(BaseTransportregisterDoc):

    class Index:
        name: str = 'transportregister_egmond'

        def __new__(cls):
            return Index(name=cls.name)

    @staticmethod
    def get_index_name_pretty():
        return 'Transportregister Egmond'

    @staticmethod
    def get_description() -> str:
        return (
            "Uit Rijksarchief Haarlem, transport van huizen en landen, vooral in Egmond, "
            "± 1580-1625"
        )


class TransportRegisterBloemendaalDoc(BaseTransportregisterDoc):

    class Index:
        name: str = 'transportregister_bloemendaal'

        def __new__(cls):
            return Index(name=cls.name)

    @staticmethod
    def get_index_name_pretty():
        return 'Transportregister Bloemendaal'

    @staticmethod
    def get_description() -> str:
        return (
            "Uit Rijksarchief Haarlem, transport van huizen en landen Aelbrechtsberg, Tetrode, "
            "Overveen, Vogelensang, ± 1580-1800"
        )


class TransportRegisterZijpeDoc(BaseTransportregisterDoc):

    class Index:
        name: str = 'transportregister_zijpe'

        def __new__(cls):
            return Index(name=cls.name)

    @staticmethod
    def get_index_name_pretty():
        return 'Transportregister Zijpe'

    @staticmethod
    def get_description() -> str:
        return "Uit Rijksarchief Haarlem, transport van huizen en land, 17e eeuw"


class TransportRegisterHaarlemDoc(BaseDocument):
    datum: str = Text(fields={'keyword': Keyword()})
    inhoud: str = Text(fields={'keyword': Keyword()})
    folio_nr: str = Text(fields={'keyword': Keyword()})
    register_nr: str = Text(fields={'keyword': Keyword()})
    vervolg_nr: str = Text(fields={'keyword': Keyword()})
    bijzonderheden: Optional[str] = Text(fields={'keyword': Keyword()})

    jaar: Optional[int] = Short()

    class Index:
        name: str = 'transportregister_haarlem'

        def __new__(cls):
            return Index(name=cls.name)

    @classmethod
    def from_csv_line(cls, line: List[str]) -> Optional['TransportRegisterHaarlemDoc']:
        # Return early, we'll discard it later using `is_valid`.
        if not any(parse_entry(value) for value in line[1:]):
            return None
        doc = cls()
        doc.meta.id = line[0]
        doc.datum = parse_entry(line[1])
        doc.inhoud = parse_entry(line[2])
        doc.folio_nr = parse_entry(line[3])
        doc.register_nr = parse_entry(line[4])
        doc.vervolg_nr = parse_entry(line[5])
        # Skip 'bron' column
        doc.bijzonderheden = parse_entry(line[7])
        doc.jaar = cls.parse_year(doc.datum)
        return doc

    @staticmethod
    def parse_year(datum: Optional[str]) -> Optional[int]:
        res = re.search(r'\d{4}', datum or '')
        return int(res[0]) if res else None

    @staticmethod
    def get_multimatch_fields() -> List[str]:
        return ['datum^3', 'inhoud', 'folio_nr', 'vervolg_nr']

    @staticmethod
    def get_index_name_pretty():
        return 'Transportregister Haarlem'

    def get_title(self) -> str:
        return self.datum or ''

    def get_subtitle(self) -> str:
        return f"folio {self.folio_nr} {self.vervolg_nr} {self.register_nr}"

    def get_body_lines(self) -> List[str]:
        out = [
            self.inhoud,
            self.bijzonderheden,
        ]
        return [value for value in out if value]

    @staticmethod
    def get_description() -> str:
        return (
            "Uit Noord-Hollands Archief Collectie Groesbeek, transport van huizen en landen in "
            "Haarlem en een enkele in Noord-Holland, 1471-1473, 1485-1501, 1558-1562, "
            "nog niet gereed"
        )


def parse_entry(entry: str) -> Optional[str]:
    return entry.strip() or None


index_number_to_doctype = {
    1: CardNameDoc,
    2: VoornamenDoc,
    3: JaartallenDoc,
    4: MaatboekHeemskerkDoc,
    5: EigendomsaktenHeemskerk,
    6: TransportRegisterEgmondDoc,
    7: TransportRegisterBloemendaalDoc,
    9: TransportRegisterHaarlemDoc,
    10: TiendeEnHonderdstePenning,
    11: TransportRegisterZijpeDoc,
    12: MaatboekBroekInWaterlandDoc,
    13: MaatboekHeemstedeDoc,
    14: MaatboekSuderwoude,
}


def list_doctypes() -> List[Type[BaseDocument]]:
    return list(index_number_to_doctype.values())


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
