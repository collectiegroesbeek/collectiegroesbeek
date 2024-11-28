import re


def extract_location(text: str) -> list[str]:
    suffixen = [
        "straat",
        "straet",
        "steeg",
        "stege",
        "land",
        "poort",
        "graft",
        "gracht",
        "dyck",
        "dijk",
    ]
    regex = re.compile(rf"(\b([A-Z][a-z]+ )?[A-Za-z]+({'|'.join(map(re.escape, suffixen))}))")
    locations = []
    for match_groups in regex.findall(text):
        location = match_groups[0]
        if "holland" in location.lower():
            continue
        location = re.sub(r"^die ", "", location, flags=re.I)
        locations.append(location)
    return locations
