import re


def split_multibron(multibron: str) -> list[str]:
    bronnen = [bron.strip() for bron in multibron.split(";")]
    # remove subbron
    bronnen = [re.split(r"/\s?(?=\w)", bron)[0].strip() for bron in bronnen]
    # remove comments
    bronnen = [re.sub(r"\s\([\w\d\s]+\)(\s|$)", "", bron, flags=re.I).strip() for bron in bronnen]
    # remove numbers
    words = [
        "fol",
        "p",
        "regest",
        "bl",
        "reg",
        "dossier",
        "inv",
        "jg",
        "post",
        "voor",
        "vóór",
        "doos",
        "no",
        "dl",
        "noot",
        "lade",
    ]
    regex = re.compile(
        rf"( ((en|copie) )?({'|'.join(map(re.escape, words))})?\b( no )?([\d\s,v-]|(?-i:[IVXLC]))+([abc],?)?( copie(en)?)?)+$",
        flags=re.IGNORECASE,
    )
    bronnen = [re.sub(regex, "", bron).strip() for bron in bronnen]
    return bronnen
