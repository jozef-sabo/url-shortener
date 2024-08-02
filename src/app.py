import ipaddress
from typing import Optional
from flask import Flask, render_template, request
from os import environ
from create import CreateValues, insert_request, InsertContext
from get import check_requested_link, get_request, GetContext
from config import load_conf
from utils import json_response
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv

load_dotenv()

connection_pool = ThreadedConnectionPool(1, 5, environ.get("DB_STRING"))

app = Flask(__name__, template_folder="template", static_folder="static")
app.config["SECRET_KEY"] = environ.get("SECRET_KEY")

# inbuilt function which takes error as parameter
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def create():
    if not request.is_json:
        return json_response({"error": "Request is not in the correct format"}, 400)

    body: dict = request.json
    create_values = CreateValues(body, app.config["INSERT_CTX"])
    if not create_values:
        return create_values.response

    request_ip = ipaddress.ip_address(request.remote_addr)

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()

    response = insert_request(connection, cursor, create_values, int(request_ip), app.config["INSERT_CTX"])

    cursor.close()
    CONNECTION_POOL.putconn(connection)

    return response


@app.route("/<redirect_url>/", methods=["GET"])
@app.route("/<redirect_url>", methods=["GET"])
def redirect(redirect_url: str):
    resp = check_requested_link(redirect_url, app.config["GET_CTX"])
    if resp is not None:
        return resp

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()

    response = get_request(cursor, redirect_url)

    cursor.close()
    CONNECTION_POOL.putconn(connection)

    return response


def main():
    conf = load_conf("config.toml")

    allowed_alphabet = conf.link_alphabet.union(conf.extensions_alphabet)
    app.config["INSERT_CTX"] = InsertContext(conf.link_alphabet, list(conf.link_alphabet), allowed_alphabet,
                                             conf.link_length, conf.destination_length, conf.creation_tries)
    app.config["GET_CTX"] = GetContext(allowed_alphabet)


if __name__ == "__main__":
    main()
    app.run(host="0.0.0.0", port=8000, debug=False, load_dotenv=True)


main()
