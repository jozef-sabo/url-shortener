from dataclasses import dataclass
from os import environ
from typing import Optional, Any
from urllib.parse import urlparse, ParseResult

import flask

import utils
from utils import json_response


@dataclass
class InsertContext:
    """
    Data class used as a context for functions,
    containing information needed when creating a link <-> destination pair
    """
    link_alphabet: set
    link_alphabet_l: list
    allowed_alphabet: set
    link_length: int
    destination_length: int
    tries: int


@dataclass
class CreateValues:
    """
    Data class containing input values received from user in the request
    """
    protocol: str
    destination: ParseResult
    status_code: int
    requested_link: Optional[str]
    admin: Optional[str]
    response: Optional[flask.Response] = None

    def __init__(self, body: dict, ctx: InsertContext):
        destination = body.get("destination", None)  # redirection url
        status_code = body.get("redirect", 301)  # status code with which redirect
        requested_link = body.get("requested_link", None)  # own link
        admin = body.get("admin", None)  # password for own links

        resp = check_destination(destination, ctx.destination_length)
        if resp is not None:
            self.response = resp
            return

        resp = check_status_code(status_code)
        if resp is not None:
            self.response = resp
            return

        if requested_link is not None:
            resp = check_requested_link(admin, requested_link, ctx.allowed_alphabet)
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
    """
    Checks if the inputted value is exactly of a status code type
    :param input_value: Any value received from user
    :return: None if value is in the correct format,
        otherwise flask.Response with detailed information about incorrect value
    """
    if not isinstance(input_value, int):
        return json_response({"error": "Status code must be of a numeric type"}, 400)

    if input_value > 399 or input_value < 300:
        return json_response({"error": "Status code must be of a redirection type"}, 400)

    return None


def check_destination(input_value: Any, destination_length: int) \
        -> Optional[flask.Response]:
    """
    Checks if the inputted value is exactly of a destination type
    :param input_value: Any value received from user
    :param destination_length: Integer representing the maximal length of a destination
    :return: None if value is in the correct format,
        otherwise flask.Response with detailed information about incorrect value
    """
    if not isinstance(input_value, str):
        return json_response({"error": "Destination address must of a text type"}, 400)

    dest_parsed = urlparse(input_value, allow_fragments=True)
    if dest_parsed.scheme not in ("http", "https"):
        return json_response({"error": "Destination address must have a correct protocol"}, 400)

    if not dest_parsed.netloc:
        return json_response(
            {"error": "Destination address must have a correct network location"}, 400)

    if len(utils.remove_scheme_url(dest_parsed).geturl()) > destination_length:
        return json_response({"error": "Destination address must be shorter"}, 400)

    return None


def check_requested_link(admin: Any, input_value: Any, allowed_alphabet: set) \
        -> Optional[flask.Response]:
    """
    Checks if the inputted value is exactly of a requested link type
    :param admin: None or string value representing an admin password
    :param input_value: Any value received from user
    :param allowed_alphabet: set containing the characters of an alphabet
    link to be checked against
    :return: None if value is in the correct format,
        otherwise flask.Response with detailed information about incorrect value
    """
    if admin != environ.get("ADMIN_PASS"):
        return json_response({"error": "Unauthorized"}, 401)

    if not isinstance(input_value, str):
        return json_response({"error": "Requested link must of a text type"}, 400)

    if (set(input_value) - allowed_alphabet) != set():
        return json_response(
            {"error": "Requested link contains not allowed characters"}, 400)

    return None


def insert_into_db(cursor, values: dict) -> Optional[str]:
    """
    Executes the INSERT query and retrieves information from the database.
    Returns one line of matched results or None
    :param cursor: psycopg2 cursor object
    :param values: dictionary containing values which will be parsed to a database query
    :return: string containing the result or None
    """
    cursor.execute(
        "SELECT insert_link "
        "FROM insert_link(%(link)s::varchar, %(protocol)s::varchar, "
        "%(dest)s::varchar, %(redirect)s::integer, %(ip_address)s::bigint);",
        values
    )
    result = cursor.fetchone()

    return result[0]


def insert_existing(connection, cursor, values: dict):
    """
    Inserts the destination given by the user along
    with the user defined shortened link to the database.
    If the link cannot be inserted int database, user is notified in the response
    If the generation is unsuccessful, returns response with the error to the user
    :param connection: psycopg2 connection object (used for commiting the changes)
    :param cursor: psycopg2 cursor object
    :param values: dictionary with preprocessed information about the entry
    :return: flask.Response containing the response for the user
    """
    inserted_value = insert_into_db(cursor, values)
    if inserted_value is None:
        return json_response(
            {"error": "Requested link was already taken", "type": "exists"}, 409)

    connection.commit()
    # SUCCESSFUL
    return json_response({"status": "created", "link": inserted_value}, 201)


def insert_generating(connection, cursor, values: dict, ctx: InsertContext):
    """
    Inserts the destination given by the user along
    with the randomly generated shortened link to the database.

    The link is generated ctx.tries number of times;
    this value can be changed in config.
    If the generation is unsuccessful, returns response with the error to the user
    :param connection: psycopg2 connection object (used for commiting the changes)
    :param cursor: psycopg2 cursor object
    :param values: dictionary with preprocessed information about the entry
    :param ctx: InsertContext object with information about local session
    :return: flask.Response containing the response for the user
    """
    for try_number in range(ctx.tries):
        values["link"] = utils.generate_string(ctx.link_alphabet_l, ctx.link_length)
        inserted_value = insert_into_db(cursor, values)

        if inserted_value is None:
            continue

        connection.commit()
        # SUCCESSFUL
        return json_response({"status": "created", "link": inserted_value}, 201)

    return json_response(
        {
            "error": "Cannot generate link, the whole pool is already taken",
            "type": "not_enough_values"},
        503)


def insert_request(connection, cursor, values: CreateValues, ip_address: int,
                   insert_ctx: InsertContext) -> flask.Response:
    """
    Preprocesses the request with the given values
    and executes the query of the link insertion to the database.

    Returns object containing flask response to the user.
    :param connection: psycopg2 connection object (used for commiting the changes)
    :param cursor: psycopg2 cursor object
    :param values: CreateValues object with information parsed by user
    :param ip_address: integer representation (32 bit) of user IP address
    :param insert_ctx: InsertContext object with information about local session
    :return: flask.Response containing the response for the user
    """
    sql_values = {
        "link": values.requested_link,
        "protocol": values.protocol,
        "dest": values.destination.geturl(),
        "redirect": values.status_code,
        "ip_address": ip_address
    }

    if values.requested_link is None:
        resp = insert_generating(connection, cursor, sql_values, insert_ctx)
    else:
        resp = insert_existing(connection, cursor, sql_values)

    return resp
