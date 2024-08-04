import json
import random
from typing import Union
from urllib.parse import urlparse, ParseResult

import flask


def json_response(body: Union[dict, str], status_code: int) -> flask.Response:
    if isinstance(body, dict):
        body = json.dumps(body)

    resp = flask.Response(body)
    resp.status_code = status_code
    resp.headers.add_header("Content-Type", "application/json")

    return resp


def generate_string(alphabet: list, length: int) -> str:
    return ''.join(random.choice(alphabet) for _ in range(length))


def remove_url_part(parsed_url: ParseResult, index: int) -> ParseResult:
    extracted_values = list(parsed_url)
    extracted_values[index] = ""  # removing item at index (part of url)
    dest_parsed_wo_part = ParseResult(*extracted_values)

    return dest_parsed_wo_part


def remove_scheme_url(parsed_url: ParseResult) -> ParseResult:
    new_url = remove_url_part(parsed_url, 0)
    url_wo_scheme = new_url.geturl().lstrip("/")
    return urlparse(url_wo_scheme)
