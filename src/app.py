import ipaddress
import logging
import os
import sys
from typing import Optional
from os import environ

from flask import Flask, render_template, request
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv

from create import CreateValues, insert_request, InsertContext
from get import check_requested_link, get_request, GetContext
from config import load_conf
from utils import json_response
import proxy
import recaptcha
from recaptcha import RecaptchaContext, RecaptchaValues

loglevel = os.environ.get("PY_LOGGING", "WARNING")
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

logging.basicConfig(
    handlers=[
        # logging.FileHandler("syslog.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ],
    level=numeric_level,
    format='%(asctime)s:%(levelname)s:%(name)s@%(threadName)s:%(message)s'
)

logging.info("Loading dotenv")
load_dotenv()

logging.info("Trying to import postfork, detecting uWSGI")
CONNECTION_POOL: Optional[ThreadedConnectionPool] = None
# parameters can be customized for uWSGI and non-uWSGI installation separately
try:
    # on non existing import (uWSGI is not running), it fails
    from uwsgidecorators import postfork
    logging.info("uWSGI detected, applying postfork")

    # https://stackoverflow.com/questions/44476678/uwsgi-lazy-apps-and-threadpool
    @postfork
    def _make_thread_pool():
        """
        If uWSGI server is available, ensures that database connection will be opened
        after the process forking.
        This is needed due to the parallelism and shared variable memory
        """
        global CONNECTION_POOL
        logging.info("Opening database connection")
        CONNECTION_POOL = ThreadedConnectionPool(1, 10, environ.get("DB_STRING"))
        logging.debug("Database connection opened with parameters minconn=%s, maxconn=%s",
                      CONNECTION_POOL.minconn, CONNECTION_POOL.maxconn)
except ImportError as _:
    logging.info("uWSGI not detected, opening database connection")
    CONNECTION_POOL = ThreadedConnectionPool(1, 10, environ.get("DB_STRING"))
    logging.debug("Database connection opened with parameters minconn=%s, maxconn=%s",
                  CONNECTION_POOL.minconn, CONNECTION_POOL.maxconn)

app = Flask(__name__, template_folder="template", static_folder="static")
app.config["SECRET_KEY"] = environ.get("SECRET_KEY")
app.config["RECAPTCHA_SECRET_KEY"] = environ.get("RECAPTCHA_SECRET_KEY")


@app.errorhandler(404)
def not_found(e):
    """
    Returns not-found flask response

    Inbuilt function which takes error as parameter
    :param e: Error
    :return: flask.Response
    """
    return render_template("404.html"), 404


@app.route("/", methods=["GET"])
def index():
    """
    Returns rendered index template
    :return: flask.Response
    """
    return render_template(
        template_name_or_list="index.html",
        **{"recaptcha": app.config["RECAPTCHA_CTX"].enabled,
           "recaptcha_site_key": app.config["RECAPTCHA_CTX"].site_key})


@app.route("/", methods=["POST"])
def create():
    """
    Route for link creation
    :return: flask.Response
    """
    logging.info("Opening new create request")
    if not request.is_json:
        logging.info("Non-JSON request")
        return json_response({"error": "Request is not in the correct format"}, 400)

    body: dict = request.json
    create_values = CreateValues(body, app.config["INSERT_CTX"])
    if not create_values:
        logging.debug("Request with incorrect values")
        return create_values.response

    recaptcha_values = RecaptchaValues(body, app.config["RECAPTCHA_CTX"])
    if not recaptcha_values:
        return recaptcha_values.response

    request_ip_str = request.remote_addr
    recaptcha_response = recaptcha.verify(recaptcha_values, app.config["RECAPTCHA_CTX"],
                                          app.config["RECAPTCHA_SECRET_KEY"], request_ip_str)
    if recaptcha_response is not None:
        return recaptcha_response

    request_ip = ipaddress.ip_address(request_ip_str)

    logging.debug("Requesting connection from connection pool")
    connection = CONNECTION_POOL.getconn()
    logging.debug("Opening the cursor")
    cursor = connection.cursor()

    response = insert_request(connection, cursor, create_values, int(request_ip), app.config["INSERT_CTX"])

    cursor.close()
    logging.debug("Cursor closed")
    CONNECTION_POOL.putconn(connection)
    logging.debug("Connection put to connection pool")

    return response


@app.route("/<redirect_url>/", methods=["GET"])
@app.route("/<redirect_url>", methods=["GET"])
def redirect(redirect_url: str):
    """
    Route for link redirection
    :param redirect_url: requested URL
    :return: flask.Response
    """
    logging.info("Opening new get request")
    resp = check_requested_link(redirect_url, app.config["GET_CTX"])
    if resp is not None:
        return resp

    logging.debug("Requesting connection from connection pool")
    connection = CONNECTION_POOL.getconn()
    logging.debug("Opening the cursor")
    cursor = connection.cursor()

    response = get_request(cursor, redirect_url)

    cursor.close()
    logging.debug("Cursor closed")
    CONNECTION_POOL.putconn(connection)
    logging.debug("Connection put to connection pool")

    return response


def main():
    """
    The main function, ensures that the application is configured correctly
    """
    logging.info("Loading config")
    conf = load_conf("config.toml")
    proxy.init(app, conf.Proxy)

    allowed_alphabet = conf.Utils.link_alphabet.union(conf.Utils.extensions_alphabet)
    app.config["INSERT_CTX"] = InsertContext(conf.Utils.link_alphabet, list(conf.Utils.link_alphabet), allowed_alphabet,
                                             conf.Utils.link_length, conf.Utils.destination_length,
                                             conf.Utils.creation_tries)
    app.config["GET_CTX"] = GetContext(allowed_alphabet)
    app.config["RECAPTCHA_CTX"] = RecaptchaContext(conf.Recaptcha.enabled, conf.Recaptcha.minimal_score,
                                                   conf.Recaptcha.verify_ip, conf.Recaptcha.site_key)
    logging.debug(
        "Using link_alphabet=%s, allowed alphabet=%s, link length=%s, destination length=%s, creation tries=%s, "
        "recaptcha enabled=%s, recaptcha minimal score=%s, recaptcha verify IP=%s, recaptcha site key=%s",
        conf.Utils.link_alphabet, allowed_alphabet, conf.Utils.link_length, conf.Utils.destination_length,
        conf.Utils.creation_tries, conf.Recaptcha.enabled, conf.Recaptcha.minimal_score, conf.Recaptcha.verify_ip,
        conf.Recaptcha.site_key)


if __name__ == "__main__":
    main()
    app.run(host="0.0.0.0", port=8000, debug=False, load_dotenv=True)


main()
