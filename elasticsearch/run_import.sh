#!/bin/bash
export PYTHONPATH=~/collgroesbeek:$PYTHONPATH

. ~/venv-collgroesbeek/bin/activate

python elasticsearch/import_dropbox.py && python elasticsearch/add_documents.py
