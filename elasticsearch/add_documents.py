import os
import logging
import sys
import csv
import argparse

from elasticsearch_dsl import connections

from collectiegroesbeek.model import CardNameIndex


if sys.version_info[0] < 3:
    raise ImportError('Python < 3 is not supported.')


connections.create_connection()


def logging_setup():
    log_format = '%(asctime)s - %(levelname)-8s - %(name)s - %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)


def run(path):
    for filename in sorted(os.listdir(path)):
        if not filename.endswith('.csv'):
            continue
        logging.info('Working on {}.'.format(filename))
        filepath = os.path.join(path, filename)
        with open(filepath, newline='\r\n', encoding='utf-16') as f:
            csvreader = csv.reader(f, dialect=csv.excel_tab)
            for line in csvreader:
                if line[0] == 'id':  # First line contains header
                    continue
                card = CardNameIndex.from_csv_line(line)
                if not card.valid:
                    continue
                card.save()


if __name__ == '__main__':
    logging_setup()
    assert connections.get_connection().ping()
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default='../collectiegroesbeek-data',
                        help='Folder with the CSV data files.')
    options = parser.parse_args()
    run(path=options.path)
    logging.info("Finished!")
