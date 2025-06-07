[![Mypy](https://github.com/collectiegroesbeek/collectiegroesbeek/actions/workflows/mypy.yml/badge.svg)](https://github.com/collectiegroesbeek/collectiegroesbeek/actions/workflows/mypy.yml)
[![Ruff](https://github.com/collectiegroesbeek/collectiegroesbeek/actions/workflows/ruff.yml/badge.svg)](https://github.com/collectiegroesbeek/collectiegroesbeek/actions/workflows/ruff.yml)
[![Tests](https://github.com/collectiegroesbeek/collectiegroesbeek/actions/workflows/pytest.yml/badge.svg)](https://github.com/collectiegroesbeek/collectiegroesbeek/actions/workflows/pytest.yml)

# Collectie Groesbeek
Flask and Elasticsearch webapp for the Collectie Groesbeek historical index.

https://www.collectiegroesbeek.nl/


## About
Collectie Groesbeek is a Dutch historical index, compiled between 1925 and 1994 by
mr. J.W. Groesbeek. During his lifetime he made notes of deeds and other historical documents
and stored them in his personal card system. He worked on this as a national archivist of the
province of Noord-Holland and has used his system for various publications.

The collection has a broad set-up and contains information about archival documents mainly
from the Noord-Holland region in the Netherlands from the Middle Ages to about 1800.

This project contains a Flask webapp that serves as frontend to the dataset stored in an
Elasticsearch backend.


## Installation part 1: data
The first part of the installation guide sets up the Elasticsearch system and the data.
This is needed for both development and production.

### Setting up Elasticsearch
Elasticsearch is a database system. We let it ingest our data and make it available through
a REST API.

For info on how to install Elasticsearch on your system, please refer to https://www.elastic.co/.

### Data ingestion

The data is in a separate Github repository. It needs to be ingested into Elasticsearch.
In the `scripts` folder there is a script to do that:

`add_documents.py` will read the csv files and add the data to Elasticsearch.

You can check this by doing a HTTP GET request with for example `curl` on
`http://localhost:9200/_cat/indices?v`.
You will see that an index has been made and that `docs.count` shows data has been added.


## Installation part 2: webserver
At this point you can run the Flask debug server to start developing. The following points are
for a production environment, we're setting up a webserver. Note that these instructions
are for an Ubuntu environment.

In the `deployment` folder are the necessary files and scripts to set this up. We assume
you have a user with sudo-rights on the server, and you can SSH into it.

1. Run the commands from `initial_setup.sh` in the remote SSH session to create the required folder
   `/opt/collgroesbeek`.
2. Copy `deployment/.env.example` to `deployment/.env` and fill in the correct values.
3. Copy the repository to `/opt/collgroesbeek`. 
4. Manually download an Elasticsearch .deb file to `/opt/collgroesbeek/deployment/`
5. Run the `install.sh` script on the server.


### Remote logs
Check the status of the uWSGI and nginx services:

`systemctl status collgroesbeek`

`systemctl status nginx`

Read the most recent uWSGI and nginx log files:

`less /var/log/uwsgi/collgroesbeek.log`

`less /var/log/nginx/error.log`


## Contributing

Contributions are welcome! Just open an issue or PR.
