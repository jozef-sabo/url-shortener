from os import environ
from typing import Optional, Any
from urllib.parse import urlparse, ParseResult
import flask
import utils
from utils import json_response
from dataclasses import dataclass


@dataclass
class CreateValues:
    protocol: str
    destination: ParseResult
    status_code: int
    requested_link: Optional[str]
    admin: Optional[str]
    response: Optional[flask.Response] = None

    def __init__(self, body: dict, link_alphabet: set):
        destination = body.get("destination", None)  # redirection url
        status_code = body.get("status_code", 301)  # status code with which redirect
        requested_link = body.get("requested_link", None)  # own link
        admin = body.get("admin", None)  # password for own links

        resp = check_destination(destination)
        if resp is not None:
            self.response = resp
            return

        resp = check_status_code(status_code)
        if resp is not None:
            self.response = resp
            return

        if requested_link is not None:
            resp = check_requested_link(admin, requested_link, link_alphabet)
            if resp is not None:
                self.response = resp
                return

        destination_parsed = urlparse(destination, allow_fragments=True)
        self.protocol = str(destination_parsed.scheme)
        self.destination = utils.remove_scheme_url(destination_parsed)
        self.status_code = status_code
        self.requested_link = requested_link
        self.admin = admin

    def __bool__(self):
        return self.response is None


def check_status_code(input_value: Any) -> Optional[flask.Response]:
    if not isinstance(input_value, int):
        return json_response({"error": "Status code must be of a numeric type"}, 400)

    if input_value > 399 or input_value < 300:
        return json_response({"error": "Status code must be of a redirection type"}, 400)

    return None


def check_destination(input_value: Any) -> Optional[flask.Response]:
    if not isinstance(input_value, str):
        return json_response({"error": "Destination address must of a text type"}, 400)

    dest_parsed = urlparse(input_value, allow_fragments=True)
    if dest_parsed.scheme not in ("http", "https"):
        return json_response({"error": "Destination address must have a correct protocol"}, 400)

    if not dest_parsed.netloc:
        return json_response({"error": "Destination address must have a correct network location"}, 400)

    if len(utils.remove_scheme_url(dest_parsed).geturl()) > 50:
        return json_response({"error": "Destination address must be shorter"}, 400)

    return None


def check_requested_link(admin: Any, input_value: Any, link_alphabet: set) -> Optional[flask.Response]:
    if admin != environ.get("ADMIN_PASS"):
        return json_response({"error": "Unauthorized"}, 401)

    if not isinstance(input_value, str):
        return json_response({"error": "Requested link must of a text type"}, 400)

    if (set(input_value) - link_alphabet) != set():
        return json_response({"error": "Requested link contains not allowed characters"}, 400)

    return None


def insert_into_db(cursor, values: dict) -> Optional[str]:
    cursor.execute(
        "SELECT * from insert_link(%(link)s, %(protocol)s, %(dest)s, %(redirect)s, %(ip_address)s);",
        values
    )
    result = cursor.fetchone()

    return result[0]


def insert_existing(connection, cursor, values: dict):
    inserted_value = insert_into_db(cursor, values)
    if inserted_value is None:
        return json_response({"error": "Requested link was already taken", "type": "exists"}, 409)

    connection.commit()
    return json_response({"status": "created", "link": inserted_value}, 201)  # SUCCESSFUL


def insert_generating(connection, cursor, values: dict, alphabet: list):
    for TRY_NUMBER in range(10):
        values["link"] = utils.generate_string(alphabet, 5)
        inserted_value = insert_into_db(cursor, values)

        if inserted_value is None:
            continue

        connection.commit()
        return json_response({"status": "created", "link": inserted_value}, 201)  # SUCCESSFUL

    return json_response(
        {"error": "Cannot generate link, the whole pool is already taken", "type": "not_enough_values"}, 503)


def insert_request(connection, cursor, values: CreateValues, ip_address: int, alphabet: list) -> flask.Response:
    sql_values = {
        "link": values.requested_link,
        "protocol": values.protocol,
        "dest": values.destination.geturl(),
        "redirect": values.status_code,
        "ip_address": ip_address
    }

    if values.requested_link is None:
        resp = insert_generating(connection, cursor, sql_values, alphabet)
    else:
        resp = insert_existing(connection, cursor, sql_values)

    return resp
