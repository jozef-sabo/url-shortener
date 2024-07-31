from dataclasses import dataclass
from typing import Optional, Union
import flask


def check_requested_link(link: str, alphabet: set) -> Optional[tuple]:
    if not isinstance(link, str) or set(link) - alphabet != set():
@dataclass
class GetContext:
    alphabet: set


        return flask.render_template("404.html"), 404

    return None


def get_from_db(cursor, values: dict) -> tuple:
    cursor.execute(
        "SELECT url, redirect FROM get_address(%(link)s);",
        values
    )
    result = cursor.fetchone()

    return result


def get_request(cursor, link: str) -> Union[flask.Response, tuple]:
    sql_values = {"link": link}

    result = get_from_db(cursor, sql_values)
    if result is None or not result:
        return flask.render_template("404.html"), 404

    url, redirect = result

    return flask.redirect(url, code=redirect)
