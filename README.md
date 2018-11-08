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

A development server is running on https://collectiegroesbeek.azurewebsites.net/,
but note that the Elasticsearch backend is currently not always enabled.


## Installation part 1: data
The first part of the installation guide sets up the Elasticsearch system and the data.
This is needed for both development and production.

### Elasticsearch with Docker
Elasticsearch is a database system. We let it ingest our data and make it available through
a REST API.

We use Docker to run Elasticsearch in. First install Docker if not already done.
You can also do this on Windows if you're developing the Flask website part.

There is a docker-compose file that you can use to setup Elasticsearch.

`docker-compose up`

We use a Docker image provided by Elasticsearch, create a new volume `esdata` where the
data will be stored, so it can be reused by multiple containers.

You can see that it's working by doing a HTTP GET request with for example `curl`
on `http://localhost:9200`.

### Restarting the Elasticsearch Docker image
You can check if the image is available with `docker ps -a`. Start it with
`docker start elasticsearch`.

### Data ingestion

The data is in a separate Github repository. It needs to be ingested into Elasticsearch.
In the `elasticsearch` folder are two scripts to do that. 

- First run `index_operations.py` to create the needed indices. 
  Note that if the indices already existed, it will delete the data.
- Then run `add_documents.py` to read the csv files and add the data to Elasticsearch.

You can check this by doing a HTTP GET request with for example `curl` on
`http://localhost:9200/_cat/indices?v`.
You will see that an index has been made and that `docs.count` shows data has been added.


## Installation part 2: webserver
At this point you can run the Flask debug server to start developing. The following points are
for a production environment, we're setting up a webserver. Note that these instructions
are for a Ubuntu environment.

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
Copy this project to a local folder. In this guide I'm using `/usr/local/collgroesbeek`.
Install the needed requirements:

`pip install --user -r /path/to/requirements.txt`


### Systemd services

We use two systemd services: one starts the uWSGI service, the second starts the nginx webserver.

The uWSGI service needs to be created, we call it `collgroesbeek-uwsgi.service`:

`sudo nano /etc/systemd/system/collgroesbeek-uwsgi.service`

Add the following configuration in the new file, make sure to change the username and path:

```
[Service]
User=username
Group=www-data
WorkingDirectory=/usr/local/collgroesbeek
ExecStart=/usr/local/bin/uwsgi --ini collectiegroesbeek.ini

[Install]
WantedBy=multi-user.target

```

Now enable and start the service:

```
sudo systemctl daemon-reload
sudo systemctl enable collgroesbeek-uwsgi
sudo systemctl start collgroesbeek-uwsgi
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
        uwsgi_pass unix:/usr/local/collgroesbeek/collectiegroesbeek.sock;
    }
    location ^~ /static/  {
        include  /etc/nginx/mime.types;
        root /usr/local/collgroesbeek/collectiegroesbeek/static;
    }
}

server {
    listen 80;
    server_name collectiegroesbeek.nl;
    return 301 $scheme://www.collectiegroesbeek.nl$request_uri;
}
```

In the following section we will use Certbot to add the HTTPS parts to this config file.

### HTTPS

Add a Let's Encrypt certificate using Certbot from EFF. Check out their
documentation for how to do this:
https://certbot.eff.org/lets-encrypt/ubuntuxenial-nginx

You can test your configuration at:

- https://www.ssllabs.com/ssltest/analyze.html?d=collectiegroesbeek.nl
- https://www.ssllabs.com/ssltest/analyze.html?d=www.collectiegroesbeek.nl

### Debugging
Check the status of the uWSGI and nginx services:

`systemctl status collgroesbeek-uwsgi`

`systemctl status nginx`

Read the most recent uWSGI and nginx log files:

`less /var/log/uwsgi/uwsgi.log`

`less /var/log/nginx/error.log`


## Contributing

Contributions are welcome! Just open an issue or PR.


## Code style guide

- Maximum line width is 100 characters.
- We use PEP8.

### PEP8 exceptions
We have some exceptions to PEP8, and other conventions:

- Comparing booleans may be explicit. E.g. `if variable is True:`.
- Bare exceptions may occur when warranted. You don't have to raise `BaseException`.
- Unused imports may happen to expose a class/function at a certain point.
- Line break _before_ operator. The new line starts with the operator.
  ```
  value = abs(some_long_value_name
              + another_value)
  ```
- Split long strings over multiple lines using parentheses. When in doubt the space comes 
  on the new line.
  ```
  long_string = ('This is a very long'
                 ' string.')
  ```
- There are two allowed ways to split lines:
  ```
  value = some_function(argument1, argument2,
                        argument3)
  ```
  ```
  value = some_function(
      argument1, argument2, argument3,
      argument4, argument5      
  )           
  ```
- Split a function definition over multiple lines as follows. Note the double indentation of
  the arguments. Note how we can add spaces around the `=` operator for setting the default
  values in this case.
  ```
  def long_function_name(
          argument1: Optional[int] = None,
          argument2: str = 'hi there'
  ) -> List[int]:
  ```

### Check code quality

You can check your code quality by running an analysis tool. We use `flake8` to check for PEP8
errors and `Mypy` to check typing. Both are included in the test suite if you are working on
Windows.

### Auto-formatter

`autopep8` is a Python application that makes code PEP8 compliant. 

Add the option `--aggressive` or `-a` for short to also change non-white-space things. 
Add it multiple times to increase the aggressivenes. It seems that above three doesn't matter.

`autopep8 collectiegroesbeek --recursive --in-place -a -a -a`
