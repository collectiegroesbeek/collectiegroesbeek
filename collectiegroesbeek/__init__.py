import flask

app = flask.Flask(__name__)
app.jinja_env.filters['zip'] = zip

from . import routes as view  # noqa E402
