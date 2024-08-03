# URL shortener

This is a really simple, compact and lightweight implementation of URL shortener using Python, [Flask](https://flask.palletsprojects.com/en/3.0.x/) and PostgreSQL database. It is packed within a Docker container using [uWSGI server](https://uwsgi-docs.readthedocs.io/en/latest/) which makes it easy to use and easy to deploy. The implementation can be used either as a standalone application or as a service behind the bigger server (e.g., load balancer).

## Installation / Deployment
There are, in general, three methods to install / deploy the service. Each of this method needs further configuration, which can be found in the section [Configuration](#Configuration)

### Docker and DockerHub (recommended)
To install the service using this method, you must have Docker installed. The installation steps can be found [here](https://www.docker.com/get-started/).

Then, create [docker compose](https://www.docker.com/get-started/) file `docker-compose.yaml` and use package [`jefinko/url-shortener:latest`](https://hub.docker.com/repository/docker/jefinko/url-shortener). 
```yaml
services:
  url-shortener:
    image: jefinko/url-shortener:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./.env:/url-shortener/.env.
```
The service will be accessible on port `8000`. To change this, the line `- "8000:8000"`
must be changed to 
``` yaml
- "8000:<desired port>"
```
Run the service with
```shell
docker compose up
```

### Docker and self-build
To install the service using this method, you must have Docker installed.

First, you must download the repository from GitHub and build a Docker image by yourself
```shell
# clone the repository from GitHub
git clone https://github.com/jozef-sabo/url-shortener.git
# change directory to the cloned folder
cd url-shortener

# build the image, Docker build tag will be "url-shortener"
docker build . -t url-shortener
```
These steps will create new Docker image with tag `url-shortener`. 

> [!WARNING]  
> The Docker image build builds own Python interpreter and psycopg2 library.  
> Be aware, because this uses some amount of data (around 1GB) and takes some time (around 15 minutes) to build!

After the build, follow the steps in part [Docker and DockerHub](#Docker-and-DockerHub-(recommended)) using the tag `url-shortener` as
```yaml
services:
  url-shortener:
    image: url-shortener
...
```

### Standalone installation
To install the service using this method, you must have Python, version at least `3.11`, installed.

First, you must download the repository from GitHub and create a Python virtual environment
```shell
# clone the repository from GitHub
git clone https://github.com/jozef-sabo/url-shortener.git
# change directory to the cloned folder
cd url-shortener

# crete virtual environment in the folder "venv"
python -m venv venv
# use the newly created Python virtual environment
source ./venv/bin/activate 
# install the requirements
python -m pip install -r requirements.txt
```
Then, change directory to `src` and run `app.py`
```shell
# change directory to src
cd src
# run app.py file
python app.py
```
The service is running on port `8000`. To change this, code in `app.py` must be changed as
```python
app.run(host="0.0.0.0", port=<desired_port>, debug=False, load_dotenv=True)
```

> [!WARNING]  
> Be aware, this method does not use `uWSGI` nor any other WSGI server. This is not recommended as it can be potential security risk!

## Configuration
To configure the service, there are three (two) main files, where you can change the variables to desired values.

### config.toml
This file configures the app itself. Each variable has its own description which helps better to understand the variable

### uwsgi.ini
This file configures the `uWSGI` server (only applicable in Docker installations). It is recommended to configure this server to experienced users only.

The regular user can be interested in two of the variables
```ini
# number of processes on which the service runs (do not be mistaken with threads)
processes = 4
# the local address and port of the service
http = 127.0.0.1:8000
```

### .env
> [!CAUTION]  
> This file contains mainly the credentials, which must stay secret.  
> Do not allow any third person nor user of the service to access this file in any occasion. Otherwise, it is a security risk!

The file must contain at least these variables
```.env
# secret value which Python uses for session-related functions
SECRET_KEY=""

# string in the format of "dbname=name user=user password=password host=host_ip port=port"
# where `dbname` is the name of the database used, `user` is the name of  teh user accessing the database,
# `password` is the secret key to access the database, `host` is the IP address or domain-name-like address of the host
# `port` is usually 5432 for the PostgreSQL database
DB_STRING=""

# secret value used to create custom links
ADMIN_PASS=""
```


In order to use the configuration files, based on the installation method, they need to be bound to (existing) file representations inside the application. For Docker based installations, add the following lines under the `volumes` section into `docker-compose.yaml` file
```yaml
- <path to the folder>/config.toml:/url-shortener/config.toml
- <path to the folder>/uwsgi.ini:/url-shortener/uwsgi.ini
- <path to the folder>/.env:/url-shortener/.env
```
For the standalone installation, edit the existing files and create and add `.env` file

## Database
The application depends on the [PostgreSQL](https://www.postgresql.org/) database service (using `psycopg2` python library). The database must be correctly set up to be accessible from the `app.py` file resp. `uWSGI` service.

The default, initial, scheme can be found in [utils/database.sql](utils/database.sql) file and must be installed before the first application usage. 