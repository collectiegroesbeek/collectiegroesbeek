import os

import flask

app = flask.Flask(__name__)
app.config['elasticsearch_host'] = os.environ.get('ELASTICSEARCH_HOST', 'localhost:9200')

from . import view  # noqa E402
