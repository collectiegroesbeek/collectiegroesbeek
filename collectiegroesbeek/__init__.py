import flask

app = flask.Flask(__name__)


from . import view  # noqa E402
