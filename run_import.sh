#!/bin/bash
export PYTHONPATH=~/collgroesbeek:$PYTHONPATH

sleep 30  # wait for more files to potentially update

. ~/venv-collgroesbeek/bin/activate

python elasticsearch/import_dropbox.py && python elasticsearch/add_documents.py

exit 0
