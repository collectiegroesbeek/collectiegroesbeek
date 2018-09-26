# collectiegroesbeek
Flask and Elasticsearch webapp for the Collectie Groesbeek historical index.

## About
Collectie Groesbeek is a Dutch historical index, compiled between 1925 and 1994 by
mr. J.W. Groesbeek. During his lifetime he made notes of deeds and other historical documents
and stored them in his personal card system. He worked on this as a national archivist of the
province of Noord-Holland and has used his system for various publications.

The collection has a broad set-up and contains information about archival documents mainly
from the Noord-Holland region in the Netherlands from the Middle Ages to about 1800.

This project contains a Flask webapp that serves as frontend to the dataset stored in an
Elasticsearch backend.

**Note that both dataset and this project are very early stage and far from complete!**

A development server is running occasionally on https://www.collectiegroesbeek.nl


## Installation

We are running Ubuntu 16.04 LTS on our server. The installation instructions are
fairly specific for this system.

### Elasticsearch
Elasticsearch is a database system. We let it ingest our data and make it available through
a REST API.

[ to be written ]

### Install nginx and uWSGI

nginx is the webserver, uWSGI is the webserver-gateway-interface (it links nginx with Flask).

You can install nginx with `apt`:

`sudo apt install nginx`

Install uWSGI with pip:

`pip install --user uwsgi`

If you're having trouble with this check out the documenation for both:

https://docs.nginx.com/nginx/admin-guide/installing-nginx/installing-nginx-open-source/#prebuilt_ubuntu

https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html#installing-uwsgi-with-python-support


### Python and Flask
Copy this project to your local user folder. Install the needed requirements:

`pip install --user -r /path/to/requirements.txt`


## Systemd services

We use two systemd services: one starts the uWSGI service, the second starts the nginx webserver.

The uWSGI service needs to be created, we call it `collectiegroesbeek-uwsgi.service`:

`sudo nano /etc/systemd/system/collectiegroesbeek-uwsgi.service`

Add the following configuration in the new file, make sure to change the username and path:

```
[Service]
User=username
Group=www-data
WorkingDirectory=/home/username/collectiegroesbeek
ExecStart=/usr/local/bin/uwsgi --ini collectiegroesbeek.ini

[Install]
WantedBy=multi-user.target

```

Now enable and start the service:

```
sudo systemctl daemon-reload
sudo systemctl enable collectiegroesbeek-uwsgi
sudo systemctl start collectiegroesbeek-uwsgi
```

The nginx service is called `nginx.service` and already exists. Just make sure it's enabled.


## nginx website configuration
Create a new configuration file for nginx:

`sudo nano /etc/nginx/sites-available/collectiegroesbeek`

Add the following text, make sure to update the paths:

```
server {
    listen 80;
    server_name www.collectiegroesbeek.nl;
    location / { try_files $uri @app; }
    location @app {
        include uwsgi_params;
        uwsgi_pass unix:/home/username/collectiegroesbeek/collectiegroesbeek.sock;
    }
    location ^~ /static/  {
        include  /etc/nginx/mime.types;
        root /home/username/collectiegroesbeek/collectiegroesbeek/static;
    }
}

server {
    listen 80;
    server_name collectiegroesbeek.nl;
    return 301 $scheme://www.collectiegroesbeek.nl$request_uri;
}
```

In the following section we will use Certbot to add the HTTPS parts to this config file.


## HTTPS

Add a Let's Encrypt certificate using Certbot from EFF. Check out their
documentation for how to do this:
https://certbot.eff.org/lets-encrypt/ubuntuxenial-nginx

You can test your configuration at:

- https://www.ssllabs.com/ssltest/analyze.html?d=collectiegroesbeek.nl
- https://www.ssllabs.com/ssltest/analyze.html?d=www.collectiegroesbeek.nl


## Debugging
Check the status of the uWSGI and nginx services:

`systemctl status collectiegroesbeek-uwsgi`

`systemctl status nginx`

Read the most recent uWSGI and nginx log files:

`less /var/log/uwsgi/uwsgi.log`

`less /var/log/nginx/error.log`


## Contributing

Contributions are welcome! Just open an issue or PR.

