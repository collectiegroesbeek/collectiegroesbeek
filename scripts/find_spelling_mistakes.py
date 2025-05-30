import logging
import re
import string
from collections import defaultdict

from tqdm import tqdm

from collectiegroesbeek.model import SpellingMistakeCandidateDoc
from ingest import logging_setup
from ingest.dataloader import iter_csv_file_items, iter_csv_files
from ingest.elasticsearch_utils import DocProcessor, setup_es_connection

logger = logging.getLogger(__name__)


MIN_WORD_LENGTH = 6
WORD_COUNT_RATIO = 10
MISTAKE_MAX_COUNT = 5


def load_data() -> dict[str, int]:
    words: dict[str, int] = defaultdict(lambda: 0)
    for filepath, filename in iter_csv_files():
        for item in iter_csv_file_items(filepath=filepath):
            for text in item.values():
                # split on any of the characters
                for word in re.split(r"[-,;:.\s]", text):
                    word = word.strip().lower()
                    if word.isalpha() and len(word) > MIN_WORD_LENGTH:
                        words[word] += 1
    return words


def find_mistakes(words: dict[str, int]) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for word, count in tqdm(words.items(), desc="find mistakes", total=len(words)):
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
    for word, candidates in tqdm(errors.items(), desc="filter mistakes", total=len(errors)):
        for candidate in candidates:
            if word_counts[word] < WORD_COUNT_RATIO * word_counts[candidate]:
                continue
            if word_counts[candidate] > MISTAKE_MAX_COUNT:
                continue
            errors_filtered[word].append(candidate)
    return errors_filtered


def store_in_elasticsearch(errors: dict[str, list[str]], word_counts: dict[str, int]):
    processor = DocProcessor()
    processor.register_index(SpellingMistakeCandidateDoc)
    for word, candidates in tqdm(errors.items(), desc="store in ES", total=len(errors)):
        doc = SpellingMistakeCandidateDoc(
            word=word,
            count=word_counts[word],
            length=len(word),
            candidates=candidates,
            candidate_counts=[word_counts[candidate] for candidate in candidates],
        )
        processor.add(doc)
    processor.finalize()


def main():
    logging_setup()
    setup_es_connection()

    data = load_data()
    errors = find_mistakes(words=data)
    errors = filter_mistakes(errors=errors, word_counts=data)
    store_in_elasticsearch(errors=errors, word_counts=data)


if __name__ == "__main__":
    main()
