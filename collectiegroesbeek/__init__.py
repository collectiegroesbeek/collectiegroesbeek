import flask
from dotenv import dotenv_values


app = flask.Flask(__name__)

_config = dotenv_values(".env")
app.config["elasticsearch_host"] = _config["elasticsearch_host"]

from . import routes as view  # noqa E402
