import argparse

from dotenv import dotenv_values
from elasticsearch_dsl.connections import connections

from collectiegroesbeek import app


_config = dotenv_values(".env")
app.config["elasticsearch_host"] = _config["elasticsearch_host"]

connections.create_connection("default", hosts=[app.config["elasticsearch_host"]])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    options = parser.parse_args()

    app.run(debug=options.debug)
