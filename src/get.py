from typing import Optional, Union
import flask


def check_requested_link(link: str, alphabet: set) -> Optional[tuple]:
    if not isinstance(link, str) or set(link) - alphabet != set():
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

    url, redirect = get_from_db(cursor, sql_values)
    if url is None or redirect is None:
        return flask.render_template("404.html"), 404

    return flask.redirect(url, code=redirect)
