import flask

app = flask.Flask(__name__)

from . import routes as view  # noqa E402
