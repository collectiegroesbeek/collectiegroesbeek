import requests
import os
import logging
import sys
import csv

if sys.version_info[0] < 3:
    raise ImportError('Python < 3 is not supported.')


path = r'C:\Users\Frank\Documents\GitHub\collectiegroesbeek-data'


log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

settings = {
    'namenindex': {
        'keys': ['datum', 'naam', 'inhoud', 'bron', 'getuigen', 'bijzonderheden'],
        'url': 'http://localhost:9200/namenindex/doc/{}'
    },
    # 'maatboek_heemskerk': {
    #     'keys': ['gebied', 'sector', 'nummer', 'oppervlakte', 'eigenaar', 'huurder',
    #              'bedrag', 'jaar', 'bron', 'opmerkingen'],
    #     'url': 'http://localhost:9200/maatboek_heemskerk/doc/{}'
    # }
}


class CardNameIndex:
    def __init__(self, line: list):
        assert len(line) == 7
        # todo: strip lines
        self.id: int = int(line[0]) if len(line[0]) > 0 else None
        self.datum: str = line[1] or None
        self.naam: str = line[2] or None
        self.inhoud: str = line[3] or None
        self.bron: str = line[4] or None
        self.getuigen: str = line[5] or None
        self.bijzonderheden: str = line[6] or None
        # placeholders
        self.naam_keyword: str = None

    def create_name_keyword(self) -> None:
        """Get a single keyword from the name field."""
        # todo: fix this one: Albrecht (St), van
        if len(card.naam.split(',')) >= 2:
            self.naam_keyword = card.naam.split(',')[0]
        elif len(card.naam.split('~')) >= 2:
            self.naam_keyword = card.naam.split('~')[0]
        elif len(card.naam.split(' ')) >= 2:
            self.naam_keyword = card.naam.split(' ')[0]
        else:
            self.naam_keyword = card.naam

    def to_dict(self):
        return self.__dict__


session = requests.Session()

for filename in sorted(os.listdir(path)):
    if not filename.endswith('.csv'):
        continue
    if 'maatboek' in filename.lower() and 'heemskerk' in filename.lower():
        keys = settings['maatboek_heemskerk']['keys']
        url = settings['maatboek_heemskerk']['url']
    else:
        keys = settings['namenindex']['keys']
        url = settings['namenindex']['url']
    logging.info('Working on {}.'.format(filename))
    filepath = os.path.join(path, filename)
    with open(filepath, newline='\r\n', encoding='utf-16') as f:
        csvreader = csv.reader(f, dialect=csv.excel_tab)
        count_no_id = 0
        for line in csvreader:
            if line[0] == 'id':
                continue
            card = CardNameIndex(line)
            # if this row is not available go to the next workbook
            if card.id is None:
                count_no_id += 1
                if count_no_id > 10:
                    logging.info(f'Id is None at too many rows, go to next file.')
                    break
            # skip row if there is no data except an id
            if card.naam is None and card.datum is None:
                logging.debug('Skipping card %s because name and date are empty.', card.id)
                continue
            # split name in normal and keyword version
            if isinstance(card, CardNameIndex):
                card.create_name_keyword()
            # start sending data
            resp = session.put(url.format(card.id), json=card.to_dict())
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError:
                logging.warning('HTTP error: code %d in %s.', resp.status_code, filename,
                                exc_info=True)
                break

logging.info("Finished!")
