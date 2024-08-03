# URL shortener

This is a really simple, compact and lightweight implementation of URL shortener using Python, [Flask](https://flask.palletsprojects.com/en/3.0.x/) and PostgreSQL database. It is packed within a Docker container using [uWSGI server](https://uwsgi-docs.readthedocs.io/en/latest/) which makes it easy to use and easy to deploy. The implementation can be used either as a standalone application or as a service behind the bigger server (e.g., load balancer).

## Installation / Deployment
There are, in general, three methods to install / deploy the service. Each of this method needs further configuration, which can be found in the section [Configuration](#Configuration)

### Docker and DockerHub (recommended)
> To install the service using this method, you must have Docker installed. The installation steps can be found [here](https://www.docker.com/get-started/).

Create [docker compose](https://www.docker.com/get-started/) file `docker-compose.yaml` and use package [`jefinko/url-shortener:latest`](https://hub.docker.com/repository/docker/jefinko/url-shortener). 
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
> To install the service using this method, you must have Docker installed.

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

After the build, follow the steps in part [Docker and DockerHub](#Docker-and-DockerHub-recommended) using the tag `url-shortener` as
```yaml
services:
  url-shortener:
    image: url-shortener
...
```

### Standalone installation
> To install the service using this method, you must have Python, version at least `3.11`, installed.

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

## Features
The software is written in accordance with extensibility and modularity. 
Because of that, it also contains some features, which can be turned on or off depending on your needs. 
Those features have so-called __feature switch__, state of which can be customized completely on deployment.

From now, features are labeled by _(feature)_.

## Reverse proxy _(feature)_
> __disabled__ by default, [network.proxy] section in config.

The service can be accessed directly as a webserver publishing the `8000` port in container as port `80` on host. 
This is not recommended in practice, because it can open the doors to many security risks.
To minimize those risks, the service called [reverse proxy](https://www.cloudflare.com/learning/cdn/glossary/reverse-proxy/) can be used. 
One, most commonly used is with the help of [nginx](https://nginx.org/), a reverse proxy HTTP server.

### Nginx setup
> To set up the service using this method, you must have nginx installed.

Firstly, you need to create a new site within nginx. E.g., `example.com` can be used instead of <your_domain>. 
```shell
# create empty nginx configuration file 
touch /etc/nginx/sites-available/<your_domain>
# then, reserve the space on the disk to the service by creating new directory
mkdir /var/www/<your_domain>
mkdir /var/www/<your_domain>/public_html
mkdir /var/www/<your_domain>/log
```
Then, put the following configuration into the newly created file 
```nginx
server {
    # service files will be stored here
    root /var/www/<your_domain>/public_html;
    
    # use port 80 to access the site (IPv4 and IPv6)
     listen 80 ;
     listen [::]:80 ;

    
    # domain
    server_name <your_domain> www.<your_domain>;
    
    # logs
    error_log /var/www/<your_domain>/log/error.log;
    access_log /var/www/<your_domain>/log/access.log;

    # this files will be searched for first in order to serve the index page
    index index.html index.htm index.nginx-debian.html;

    # the configuration itself
    location / {
        # address and port, where is the service running
        # most probably the IP will be 127.0.0.1 and port 8000 
        proxy_pass http://<ip_address>:<port>/;
        proxy_set_header   Host $http_host;
        proxy_set_header   Upgrade $http_upgrade;
        
        # this following lines are for Flask to be informed about users IP address, etc.
        # also, those need to be enabled in the further service config
        # x-for
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # x-proto
        proxy_set_header X-Forwarded-Proto $scheme;
        # x-host
        proxy_set_header X-Forwarded-Host $host;
        
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
After inserting the contents to the file and putting the correct values instead of placeholders, the domain must be enabled and the nginx service must be restarted
```shell
# put the symlink into sites-enabled folder for nginx to register
ln -s /etc/nginx/sites-enabled/<your_domain> /etc/nginx/sites-available/<your_domain>
# restart nginx service
systemctl restart nginx
```
Now, the site should be enabled and running. The reverse proxy should work.

### Service setup
The reverse proxy should be running flawlessly; however, it cannot recognize the user's IP addresses. 
To solve this problem, the __reverse proxy__ feature must be enabled in the service config. 
To do this, change the following lines in `config.toml`
```toml
[network.proxy]
# tell the service it is running behind the reverse proxy
enabled = true
# select which headers are sent to the service from nginx
x_for = true
x_proto = true
x_host = true
x_port = false
x_prefix = false
```
The entries set to `true` were set up in nginx config already.
To enable more entries, add the corresponding lines to the [nginx configuration file](#nginx-setup).