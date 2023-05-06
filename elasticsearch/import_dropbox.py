import os
from typing import Iterator
from io import BytesIO
from typing import Tuple

import dropbox
import xlsx2csv
from dotenv import dotenv_values
from tqdm import tqdm


def iter_dropbox_xlsx_files() -> Iterator[Tuple[str, bytes]]:
    with dropbox.Dropbox(dotenv_values(".env")['dropbox_token']) as dbx:
        for entry in dbx.files_list_folder("").entries:
            if entry.path_display.startswith("/Coll Gr "):
                _, resp = dbx.files_download(path=entry.path_display)
                yield entry.name, resp.content


def xlsx_bytes_to_csv_file(xlsx_bytes: bytes, filename_csv: str):
    xlsx_stream = BytesIO(xlsx_bytes)
    converter = xlsx2csv.Xlsx2csv(xlsx_stream, outputencoding='utf-8', skip_empty_lines=True)
    converter.convert(filename_csv)


def main():
    for filename, xlsx_bytes in tqdm(iter_dropbox_xlsx_files(), 'download from dropbox'):
        filename_csv = os.path.join('../collectiegroesbeek-data', filename.replace('.xlsx', '.csv'))
        xlsx_bytes_to_csv_file(xlsx_bytes, filename_csv)


if __name__ == '__main__':
    main()
