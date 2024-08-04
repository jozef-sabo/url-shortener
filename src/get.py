from dataclasses import dataclass
from typing import Optional, Union

import flask


@dataclass
class GetContext:
    """
    Data class used as a context for functions, containing information needed when retrieving a link
    """
    alphabet: set


def check_requested_link(link: str, get_ctx: GetContext) -> Optional[tuple]:
    """
    Checks if the inputted value is exactly of a link type

    :param link: Any value received from user
    :param get_ctx: GetContext object with information about local session
    :return: None if value is in the correct format,
        otherwise tuple containing flask response and the status code
    """
    if not isinstance(link, str) or set(link) - get_ctx.alphabet != set():
        return flask.render_template("404.html"), 404

    return None


def get_from_db(cursor, values: dict) -> tuple:
    """
    Executes the SELECT query and retrieves information from the database.
    Returns one line of matched results
    :param cursor: psycopg2 cursor object
    :param values: dictionary containing values which will be parsed to a database query
    :return: tuple containing zero or one element (line) based on the result
    """
    cursor.execute(
        "SELECT url, redirect FROM get_address(%(link)s::varchar);",
        values
    )
    result = cursor.fetchone()

    return result


def get_request(cursor, link: str) -> Union[flask.Response, tuple]:
    """
    Preprocesses the request with the given link
    and executes the query of getting the link from the database.
    Returns tuple or object containing flask response for the user
    :param cursor: psycopg2 cursor object
    :param link: link which real destination address will be retrieved
    :return: flask.Response or tuple containing the response to the user
    """
    sql_values = {"link": link}

    result = get_from_db(cursor, sql_values)
    if result is None or not result:
        return flask.render_template("404.html"), 404

    url, redirect = result

    return flask.redirect(url, code=redirect)
