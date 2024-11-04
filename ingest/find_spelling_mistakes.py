import logging
import re
import string
from collections import defaultdict

from tqdm import tqdm

from ingest.ingest_pkg import logging_setup
from ingest.ingest_pkg.dataloader import iter_csv_files, iter_csv_file_items


logger = logging.getLogger(__name__)


def load_data() -> dict[str, int]:
    words: dict[str, int] = defaultdict(lambda: 0)
    for filepath, filename in iter_csv_files():
        for item in iter_csv_file_items(filepath=filepath):
            try:
                bron = item["bron"]
            except KeyError:
                continue
            # split on any of the characters
            for word in re.split(r"[-,;:.\s]", bron):
                word = word.strip().lower()
                if word.isalpha() and len(word) > 2:
                    words[word] += 1
    return words


def find_mistakes(words: dict[str, int]) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for word, count in tqdm(words.items(), total=len(words)):
        candidates = find_edit_distance_1(word=word, all_words=words)
        if not candidates:
            continue
        errors[word] = list(candidates)
    return errors


def find_edit_distance_1(word: str, all_words: dict[str, int]) -> set[str]:
    candidates: set[str] = set()
    for i in range(len(word)):
        left = word[:i]
        right = word[i + 1 :]
        for letter in string.ascii_lowercase:
            new_word = left + letter + right
            if new_word in all_words:
                candidates.add(new_word)
    candidates.remove(word)
    return candidates


def filter_mistakes(
    errors: dict[str, list[str]], word_counts: dict[str, int]
) -> dict[str, list[str]]:
    errors_filtered: dict[str, list[str]] = defaultdict(list)
    for word, candidates in errors.items():
        for candidate in candidates:
            if len(word) < 4:
                continue
            if word_counts[word] < 5 * word_counts[candidate]:
                continue
            errors_filtered[word].append(candidate)
    return errors_filtered


def main():
    logging_setup()

    data = load_data()
    errors = find_mistakes(words=data)
    errors = filter_mistakes(errors=errors, word_counts=data)


if __name__ == "__main__":
    main()
