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

### Security
Newer versions of ELasticsearch have some security features by default. Since we are running only
a single node,  without any critical data, we'll make it easier by disabling some of those.

`sudo nano /etc/elasticsearch/elasticsearch.yml`

Here disable HTTP encryption by setting `xpack.security.http.ssh` `enabled` to false.

Next, add the following to allow anonymous access to everything:

```
xpack.security.authc:
  anonymous:
    username: anonymous_user
    roles: superuser
    authz_exception: false
```


### Data ingestion

The data is in a separate Github repository. It needs to be ingested into Elasticsearch.
In the `elasticsearch` folder there is a script to do that:

`add_documents.py` will read the csv files and add the data to Elasticsearch. It has an option
to delete and create the index first.

You can check this by doing a HTTP GET request with for example `curl` on
`http://localhost:9200/_cat/indices?v`.
You will see that an index has been made and that `docs.count` shows data has been added.


## Installation part 2: webserver
At this point you can run the Flask debug server to start developing. The following points are
for a production environment, we're setting up a webserver. Note that these instructions
are for a Ubuntu environment.

### Users and permission
I'm assuming you created a non-root user for yourself that you are using. Nginx uses a `www-data`
user and group.

Add your user to the `www-data` group:

`sudo adduser <username> www-data`

You may have to give permission on your user folder to execute for other users, such that
Nginx can see what files exist there:

`sudo chmod o+x /home/<username>`

### Python

Make sure your system has Python 3.10 or higher.
In this guide I'm using `pip`, but that may be `pip3` on your system.

### Install nginx
nginx is the webserver we'll use. You can install nginx with `apt`:

`sudo apt install nginx`

### Create a Python virtual environment
We'll create a virtual environment to install our Python packages. First install `virtualenv`:

`sudo apt install virtualenv`

Now we create the actual virtual environment. It's a folder that will be placed in our current
directory, I'm calling it 'venv-collgroesbeek':

`virtualenv venv-collgroesbeek`

Now activate the virtual environment:

`source venv-collgroesbeek/bin/activate`

### Install Python packages
When you install Python packages make sure the virtual environment is activated.

uWSGI is the webserver-gateway-interface (it links nginx with Flask). Install uWSGI with pip:

`pip install uwsgi`

Copy this project to a local folder. In this guide I'm using my user directory `~/collgroesbeek`.
Install the needed requirements:

`pip install -r ~/collgroesbeek/requirements.txt`

### Logging
You may have to create a folder in which uWSGI can put its logs:

`sudo mkdir /var/log/uwsgi`

And give ownership to your user:

`sudo chown <username> /var/log/uwsgi`

### Systemd services

We use two systemd services: one starts the uWSGI service, the second starts the nginx webserver.

First find out what the path to your uWSGI executable is:

`which uwsgi`

The uWSGI service needs to be created, we call it `collgroesbeek.service`:

`sudo nano /etc/systemd/system/collgroesbeek.service`

Add the following configuration in the new file, make sure to change the username and path:

```
[Service]
User=<username>
Group=www-data
WorkingDirectory=/home/<username>/collgroesbeek
ExecStart=/home/<username>/venv-collgroesbeek/bin/uwsgi --ini collectiegroesbeek.ini

[Install]
WantedBy=multi-user.target

```

Now enable and start the service:

```
sudo systemctl daemon-reload
sudo systemctl enable collgroesbeek
sudo systemctl start collgroesbeek
```

The nginx service is called `nginx.service` and already exists. Just make sure it's enabled.


### nginx website configuration
Create a new configuration file for nginx:

`sudo nano /etc/nginx/sites-available/collgroesbeek`

Add the following text, make sure to update the paths if needed:

```
server {
    listen 80;
    server_name www.collectiegroesbeek.nl;
    location / { try_files $uri @app; }
    location @app {
        include uwsgi_params;
        uwsgi_pass unix:<path to project>/collectiegroesbeek.sock;
    }
    location ^~ /static/  {
        include  /etc/nginx/mime.types;
        root <path to project>/collectiegroesbeek;
    }
    location = /robots.txt {
        alias <path to project>/collectiegroesbeek/static/robots.txt;
    }
}

server {
    listen 80;
    server_name collectiegroesbeek.nl;
    return 301 $scheme://www.collectiegroesbeek.nl$request_uri;
}

```

Enable this configuration by creating a symbolic link to it:

`sudo ln -s /etc/nginx/sites-available/collgroesbeek /etc/nginx/sites-enabled/`


In the following section we will use Certbot to add the HTTPS parts to this config file.

### HTTPS
Add a Let's Encrypt certificate using Certbot from EFF. Check out their
documentation for how to do this:
https://certbot.eff.org/instructions

You can test your configuration at:

- https://www.ssllabs.com/ssltest/analyze.html?d=collectiegroesbeek.nl
- https://www.ssllabs.com/ssltest/analyze.html?d=www.collectiegroesbeek.nl

### Debugging
Check the status of the uWSGI and nginx services:

`systemctl status collgroesbeek`

`systemctl status nginx`

Read the most recent uWSGI and nginx log files:

`less /var/log/uwsgi/uwsgi.log`

`less /var/log/nginx/error.log`


## Contributing

Contributions are welcome! Just open an issue or PR.
