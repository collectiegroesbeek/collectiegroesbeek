import re


def extract_date_from_filename_prefix(filename: str) -> tuple[str, str]:
    match = re.search(r"^\d{4}(?:-\d{2}){0,2}", filename)
    if match:
        parts = match.group(0).split("-")
        year = parts[0]
        filename = filename[len(match.group(0)) :]
    else:
        year = ""
    return filename, year
