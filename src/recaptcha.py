from dataclasses import dataclass
from typing import Optional, Any

import flask
import requests

from utils import json_response


@dataclass
class RecaptchaContext:
    enabled: bool
    minimal_score: float
    verify_ip: bool
    site_key: str


@dataclass
class RecaptchaValues:
    token: str
    response: Optional[flask.Response] = None

    def __init__(self, body: dict, ctx: RecaptchaContext):
        # FEATURE SWITCH
        if not ctx.enabled:
            return

        token = body.get("recaptcha", None)
        resp = check_token(token)
        if resp is not None:
            self.response = resp
            return

        self.token = token

    def __bool__(self):
        return self.response is None


def check_token(input_value: Any) -> Optional[flask.Response]:
    if input_value is None:
        return json_response({"error": "Recaptcha token was not provided"}, 401)

    if not isinstance(input_value, str):
        return json_response({"error": "Recaptcha token must be of a text type"}, 400)

    return None


def unsuccessful_verify(error_codes: list) -> flask.Response:
    if "timeout-or-duplicate" in error_codes:
        return json_response({"error": "Recaptcha challenge failed, duplicate or timed out request"}, 400)

    return json_response({"error": "Recaptcha challenge failed, check the token parsed"}, 400)


# https://developers.google.com/recaptcha/docs/verify
def verify(user_input: RecaptchaValues, ctx: RecaptchaContext, secret_key: str, user_ip:str) -> Optional[flask.Response]:
    # FEATURE SWITCH
    if not ctx.enabled:
        return None

    request_data = {
        "secret": secret_key,
        "response": user_input.token,
    }

    if ctx.verify_ip:
        request_data["remoteip"] = user_ip

    request = requests.post("https://www.google.com/recaptcha/api/siteverify", data=request_data)

    # recaptcha servers are unavailable or internal error
    if request.status_code != 200:
        return json_response({"error": "Recaptcha token must be of a text type"}, 503)

    response_data: dict = request.json()

    success = response_data.get("success", False)
    if not success:
        error_codes = response_data.get("error-codes", [])
        return unsuccessful_verify(error_codes)

    action = response_data.get("action", None)
    if action != "submit":
        return json_response({"error": "Recaptcha verification observed malformed request"}, 400)

    score = response_data.get("score", -1)
    if score < ctx.minimal_score:
        return json_response({"error": "Recaptcha verification observed a non human behaviour. Try again."}, 400)

    return None
