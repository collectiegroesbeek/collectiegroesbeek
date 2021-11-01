import itertools
import re
from typing import List, Set

equivalents = [
    ('aa', 'ae'),
    ('uu', 'ue'),
    # ('c', 'k', 'ck'),  # niet ch
    ('ch', 'g'),
    ('v', 'f', 'ff'),
    ('y', 'ij', 'ey', 'ei', 'eij'),
    # ('hy', 'y'),  # medeklinker ervoor
    ('ui', 'uy', 'uij'),
]

equivalents_end_of_word = [
    ('ss', 'sz', 'ssen', 'sses'),
    ('je', 'ge'),
    ('jen', 'gen'),
    ('d', 'dt', 't'),
]


def extract_names(text: str) -> List[str]:
    names = set()
    name = None
    for word in text.split():
        if word.istitle():
            if not name:
                name = word
            else:
                name += ' ' + word
        elif name:
            names.add(name)
            name = None
    return sorted(names)


def generate_phrase_variants(phrase: str) -> List[str]:
    variants = [generate_word_variants(word) for word in phrase.split()]
    return [' '.join(x) for x in itertools.product(*variants)]


def generate_word_variants(word: str) -> List[str]:
    variants = set()
    to_check = {word.lower(), }
    while to_check:
        _word = to_check.pop()
        _variants = _generate_word_variants(_word)
        to_check.update(_variants.difference(variants))
        variants.update(_variants)
    return sorted(variants)


def _generate_word_variants(word: str) -> Set[str]:
    variants = {word, }
    for _equivalents in equivalents:
        pattern = rf'{"|".join(re.escape(x) for x in _equivalents)}'
        for match in re.finditer(pattern, word):
            for _option in _equivalents:
                if word[:match.span()[0] + len(_option)] != _option:
                    variants.add(word[:match.span()[0]] + _option + word[match.span()[1]:])
    for _equivalents in equivalents_end_of_word:
        pattern = rf'({"|".join(re.escape(x) for x in _equivalents)})$'
        for match in re.finditer(pattern, word):
            for _option in _equivalents:
                if word[:match.span()[0] + len(_option)] != _option:
                    variants.add(word[:match.span()[0]] + _option + word[match.span()[1]:])
    for option in ('c', 'k', 'ck'):
        match = re.search(rf'{re.escape(option)}(?=[^h])', word)
        if match:
            for _option in ('c', 'k', 'ck'):
                variants.add(word[:match.span()[0]] + _option + word[match.span()[1]:])
    return variants
