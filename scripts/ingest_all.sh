#!/bin/bash

source .venv/bin/activate

echo "Running add_documents.py"
PYTHONPATH=. python scripts/add_documents.py

echo "Running find_spelling_mistakes.py"
PYTHONPATH=. python scripts/find_spelling_mistakes.py

echo "Running generate_bronnen.py"
PYTHONPATH=. python scripts/generate_bronnen.py

echo "Running generate_locations.py"
PYTHONPATH=. python scripts/generate_locations.py

echo "Running ner_spacy.py"
PYTHONPATH=. python scripts/ner_spacy.py

echo "All scripts completed"
