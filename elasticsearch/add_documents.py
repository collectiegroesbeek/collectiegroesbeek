import requests
import os
import logging
import sys
import csv
import typing
from posixpath import join as urljoin

if sys.version_info[0] < 3:
    raise ImportError('Python < 3 is not supported.')


address = 'http://localhost:9200'
path_data = r'C:\Users\Frank\Documents\GitHub\collectiegroesbeek-data'


class CardNameIndex:
    def __init__(self, line: list):
        self._line: list = line
        self.valid = False  # Assume invalid unless end is reached.
        if line[0] == 'id':  # First line contains header
            return
        self.id: typing.Optional[int] = int(line[0]) if len(line[0]) > 0 else None
        self.datum: typing.Optional[str] = self.parse_entry(line[1])
        self.naam: typing.Optional[str] = self.parse_entry(line[2])
        self.inhoud: typing.Optional[str] = self.parse_entry(line[3])
        self.bron: typing.Optional[str] = self.parse_entry(line[4])
        self.getuigen: typing.Optional[str] = self.parse_entry(line[5])
        self.bijzonderheden: typing.Optional[str] = self.parse_entry(line[6])
        self.naam_keyword: typing.Optional[str] = None  # placeholder
        # At the end of a file there may be empty lines, skip them.
        if self.id is None:
            return
        # Skip row if there is no data except an id. This happens a lot at the end of a file.
        if self.naam is None and self.datum is None:
            return
        self.valid = True

    @staticmethod
    def parse_entry(entry) -> typing.Optional[str]:
        return entry.strip() or None

    def create_name_keyword(self) -> None:
        """Get a single keyword from the name field."""
        # todo: fix this one: Albrecht (St), van
        if len(self.naam.split(',')) >= 2:
            self.naam_keyword = self.naam.split(',')[0]
        elif len(self.naam.split('~')) >= 2:
            self.naam_keyword = self.naam.split('~')[0]
        elif len(self.naam.split(' ')) >= 2:
            self.naam_keyword = self.naam.split(' ')[0]
        else:
            self.naam_keyword = self.naam

    def to_dict(self):
        return self.__dict__


def logging_setup():
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def run(path):
    session = requests.Session()
    for filename in sorted(os.listdir(path)):
        if not filename.endswith('.csv'):
            continue
        logging.info('Working on {}.'.format(filename))
        filepath = os.path.join(path, filename)
        with open(filepath, newline='\r\n', encoding='utf-16') as f:
            csvreader = csv.reader(f, dialect=csv.excel_tab)
            for line in csvreader:
                card = CardNameIndex(line)
                if not card.valid:
                    continue
                # split name in normal and keyword version
                if isinstance(card, CardNameIndex):
                    card.create_name_keyword()
                # start sending data
                url = urljoin(address, 'namenindex', 'doc', str(card.id))
                resp = session.put(url, json=card.to_dict())
                try:
                    resp.raise_for_status()
                except requests.exceptions.HTTPError:
                    logging.warning('HTTP error: code %d for card %d.', resp.status_code, card.id,
                                    exc_info=True)
                    break


if __name__ == '__main__':
    assert requests.get(address).status_code == 200
    logging_setup()
    run(path=path_data)
    logging.info("Finished!")
