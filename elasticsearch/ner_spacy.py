import os
import pickle
import re

import spacy
from tqdm import tqdm


PATH_DATASET = "dataset_text_pairs.p"


def create_dataset():
    path = "../collectiegroesbeek-data"
    filenames = sorted(filename for filename in os.listdir(path) if filename.endswith('.csv'))
    texts = []
    pbar = tqdm(filenames)
    for filename in pbar:
        if not filename.startswith(("Coll Gr 1", "Coll Gr 2")):
            continue
        pbar.set_postfix(filename=filename)
        filepath = os.path.join(path, filename)
        with open(filepath, encoding="utf-8") as f:
            csvreader = csv.DictReader(f)
            for item in csvreader:
                if filename.startswith("Coll Gr 1"):
                    field1 = item.get("naam")
                    field2 = item.get("inhoud")
                elif filename.startswith("Coll Gr 2"):
                    field1 = (item.get("voornaam", "") + " " + item.get("patroniem", "")).strip()
                    field2 = item.get("inhoud")
                if field1 and field2:
                    texts.append((field1, field2))

    with open(PATH_DATASET, "wb") as f:
        pickle.dump(texts, f)

    print(f"Saved {len(texts)} text pairs to {PATH_DATASET}")


def run_ner():
    nlp = spacy.load("nl_core_news_lg")

    with open(PATH_DATASET, "rb") as f:
        text_pairs = pickle.load(f)

    names = set()
    locations = set()
    for pair in tqdm(text_pairs
                     ):
        name = pair[0]
        if "," in name:
            name = put_van_der_in_front(name)
        names.add(name)

        doc = nlp(pair[1])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                names.add(ent.text)
            elif ent.label_ == "GPE" or ent.label_ == "LOC":
                locations.add(ent.text)

    with open("names.txt", "w", encoding="utf-8") as f:
        for name in sorted(names):
            print(name, file=f)
    with open("locations.txt", "w", encoding="utf-8") as f:
        for location in sorted(locations):
            print(location, file=f)

    print(f"Exported {len(names)} names and {len(locations)} locations")


def put_van_der_in_front(name: str) -> str:
    return ' '.join(name.split(",")[::-1]).strip()


def clean():
    with open("names_org.txt", "r", encoding="utf-8") as f:
        names = f.readlines()
    names = [re.sub(r"\s+", " ", name).strip() for name in names]
    titles_to_remove = (
        "jvr ", "jhr", "jonker ", "jonge ", "jonkheer ", "jonkvrouw ",
        "juffr ", "jonghe ", "hertog ", "hertogin ", "here ", "heren ", "heere ", "heer ",
        "grote ", "gravin ", "graaf ", "frère ", "fils de ", "filius ", "filii ", "filie ",
        "dr "
    )
    names = [' '.join(name.split(' ')[1:]) if name.startswith(titles_to_remove) else name
             for name in names]
    names = [re.sub(r"\s+", " ", name).strip() for name in names]
    names = [name for name in names if name and name_starts_with_capital_letter(name)]
    names = [re.sub(r"\s+", " ", name).strip() for name in names]
    names = sorted(set(names))
    with open("names.txt", "w", encoding="utf-8") as f:
        for name in names:
            print(name, file=f)


def name_starts_with_capital_letter(name: str) -> bool:
    if not name[0].islower():
        return True
    voorvoegsels = ("van ", "von ", "der ", "den ", "de ", "d' ")
    if name.startswith(voorvoegsels):
        name = ' '.join(name.split(' ')[1:])
        return name_starts_with_capital_letter(name)
    return False


if __name__ == '__main__':
    create_dataset()
    run_ner()
    clean()
