import csv
import os
from typing import Iterator

from tqdm import tqdm


def iter_csv_files(path: str = "../collectiegroesbeek-data") -> Iterator[tuple[str, str]]:
    filenames = sorted(filename for filename in os.listdir(path) if filename.endswith(".csv"))
    pbar = tqdm(filenames)
    for filename in pbar:
        pbar.set_postfix(filename=filename)
        filepath = os.path.join(path, filename)
        yield filepath, filename


def iter_csv_file_items(filepath: str) -> Iterator[dict]:
    with open(filepath, encoding="utf-8") as f:
        csvreader = csv.DictReader(f)
        yield from csvreader
