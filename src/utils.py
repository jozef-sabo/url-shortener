import json
import random
from typing import Union
from urllib.parse import urlparse, ParseResult

import flask


def json_response(body: Union[dict, str], status_code: int) -> flask.Response:
    """
    Returns Flask response consisting of body in JSON format with given status code
    :param body: dictionary containing body which will be converted to JSON
    :param status_code: response status code
    :return: Flask response of JSON Content-Type
    """
    if isinstance(body, dict):
        body = json.dumps(body)

    resp = flask.Response(body)
    resp.status_code = status_code
    resp.headers.add_header("Content-Type", "application/json")

    return resp


def generate_string(alphabet: list, length: int) -> str:
    """
    Generates pseudo-random string from the given alphabet with specific length
    :param alphabet: a list of characters to be used for string creation
    :param length: length of the created string
    :return: resulting string
    """
    return ''.join(random.choice(alphabet) for _ in range(length))


def remove_url_part(parsed_url: ParseResult, index: int) -> ParseResult:
    """
    Removes a part of the url from urllib.ParseResult object
    :param parsed_url: ParseResult of already parsed url string
    :param index: (0: scheme, 1: netloc, 2: path, 3: params, 4: query, 5: fragment)
    index of removed part
    :return: a ParseResult object with removed part
    """
    extracted_values = list(parsed_url)
    extracted_values[index] = ""  # removing item at index (part of url)
    dest_parsed_wo_part = ParseResult(*extracted_values)

    return dest_parsed_wo_part


def remove_scheme_url(parsed_url: ParseResult) -> ParseResult:
    """
    Removes the scheme from urllib.ParseResult object if
    any and fills the other ParseResult parts correctly
    :param parsed_url: ParseResult of already parsed url string
    :return: a ParseResult object with removed scheme
    """
    new_url = remove_url_part(parsed_url, 0)
    url_wo_scheme = new_url.geturl().lstrip("/")
    return urlparse(url_wo_scheme)
