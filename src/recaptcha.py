import logging
from dataclasses import dataclass
from typing import Optional, Any

import flask
import requests

from utils import json_response


@dataclass
class RecaptchaContext:
    """
    Data class containing information about reCAPTCHA service used as a context for functions
    """
    enabled: bool
    minimal_score: float
    verify_ip: bool
    site_key: str


@dataclass
class RecaptchaValues:
    """
    Data class containing input values received from user in the request

    Contains FEATURE SWITCH
    """
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
    """
    Checks if the inputted value is exactly of a token type
    :param input_value: Any value received from user
    :return: None if value is in the correct format,
        otherwise flask.Response with detailed information about incorrect value
    """
    if input_value is None:
        logging.debug("Recaptcha token not provided")
        return json_response({"error": "Recaptcha token was not provided"}, 401)

    if not isinstance(input_value, str):
        logging.debug("Recaptcha token is not a of a str type, it is %s", type(input_value))
        return json_response({"error": "Recaptcha token must be of a text type"}, 400)

    return None


def unsuccessful_verify(error_codes: list) -> flask.Response:
    """
    Checks the error code of the unsuccessfully verified state of reCAPTCHA response
    :param error_codes: received error codes
    :return: flask.Response with the meaningful information for the user
    """
    if "timeout-or-duplicate" in error_codes:
        logging.debug("Recpatcha unsuccessful, timeout or duplicate")
        return json_response(
            {"error": "Recaptcha challenge failed, duplicate or timed out request"}, 400)

    logging.debug("Recpatcha unsuccessful, error codes=%s", error_codes)
    return json_response({"error": "Recaptcha challenge failed, check the token parsed"}, 400)


# https://developers.google.com/recaptcha/docs/verify
def verify(user_input: RecaptchaValues, ctx: RecaptchaContext, secret_key: str, user_ip: str) \
        -> Optional[flask.Response]:
    """
    Verifies the token retrieved by user.

    Contains FEATURE SWITCH
    Checks for correctness and verifies the human-like behavior
    :param user_input: RecaptchaValues object with retrieved information
    :param ctx: RecaptchaContext object with information about local reCAPTCHA session
    :param secret_key: reCAPTCHA secret key
    :param user_ip: string containing user IP address of the reqeust
    :return: None if the values and behavior were verified successfully,
        otherwise flask.Response with detailed information about error
    """
    logging.info("Verifying recaptcha, state %s", ctx.enabled)
    # FEATURE SWITCH
    if not ctx.enabled:
        return None

    request_data = {
        "secret": secret_key,
        "response": user_input.token,
    }

    if ctx.verify_ip:
        request_data["remoteip"] = user_ip

    logging.debug("Sending POST request to siteverify")
    request = requests.post("https://www.google.com/recaptcha/api/siteverify", data=request_data)
    logging.debug("Response %s", request)

    # recaptcha servers are unavailable or internal error
    if request.status_code != 200:
        logging.error("Error communicating with siteverify, status code=%s", request.status_code)
        return json_response({"error": "Recaptcha token must be of a text type"}, 503)

    response_data: dict = request.json()
    logging.debug("Siteverify response data=%s", response_data)

    success = response_data.get("success", False)
    if not success:
        error_codes = response_data.get("error-codes", [])
        return unsuccessful_verify(error_codes)

    action = response_data.get("action", None)
    if action != "submit":
        logging.debug("Recaptcha unsuccessful, action!=submit, action=%s", action)
        return json_response(
            {"error": "Recaptcha verification observed malformed request"}, 400)

    score = response_data.get("score", -1)
    if score < ctx.minimal_score:
        logging.debug("Recaptcha unsuccessful, score is low, score=%s", score)
        return json_response(
            {"error": "Recaptcha verification observed a non human behaviour. Try again."}, 400)

    logging.info("Recaptcha successful")
    return None
