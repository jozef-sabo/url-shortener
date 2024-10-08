import logging
import string
import tomllib
from dataclasses import dataclass
from typing import Any

DEFAULT_ALPHABET = string.ascii_letters
DEAFULT_EXTENSIONS = ["_", "-"]
DEFAULT_LINK_LENGTH = 5
DEFAULT_CREATION_TRIES = 10
DEFAULT_DESTINATION_LENGTH = 50

DEFAULT_PROXY_ENABLED = False
DEFAULT_PROXY_X_FOR = True
DEFAULT_PROXY_X_PROTO = True
DEFAULT_PROXY_X_HOST = False
DEFAULT_PROXY_X_PORT = False
DEFAULT_PROXY_X_PREFIX = False

DEFAULT_RECAPTCHA_ENABLED = False
DEFAULT_RECAPTCHA_MIN_SCORE = 0.5
DEFAULT_RECAPTCHA_VERIFY_IP = True
DEFAULT_RECAPTCHA_SITE_KEY = ""


@dataclass
class ConfigValues:
    """
    Data class containing input values received from user in the request
    """
    @dataclass
    class Utils:
        """
        Data class representing a utils section in the configuration
        """
        link_alphabet: set[str]
        extensions_alphabet: set[str]
        link_length: int
        creation_tries: int
        destination_length: int

        def __init__(self, config):
            link_alphabet = config.get("shortener", {}).get("utils", {}).get("alphabet", {}).get("link",
                                                                                                 DEFAULT_ALPHABET)
            extensions_alphabet = config.get("shortener", {}).get("utils", {}).get("alphabet", {}).get(
                "custom_link_extensions", DEAFULT_EXTENSIONS)
            link_length = config.get("shortener", {}).get("utils", {}).get("link_length", DEFAULT_LINK_LENGTH)
            creation_tries = config.get("shortener", {}).get("utils", {}).get("creation_tries", DEFAULT_CREATION_TRIES)
            dest_length = config.get("shortener", {}).get("utils", {}).get("max_destination_length",
                                                                           DEFAULT_DESTINATION_LENGTH)

            check_character_list(link_alphabet, "Link alphabet")
            check_character_list(extensions_alphabet, "Link extensions")
            check_number(link_length, "Link length", 1)
            check_number(creation_tries, "Creation tries", 1)
            check_number(dest_length, "Destination URL string length", 1)

            self.link_alphabet = set(link_alphabet)
            self.extensions_alphabet = set(extensions_alphabet)
            self.link_length = link_length
            self.creation_tries = creation_tries
            self.destination_length = dest_length

    @dataclass
    class Proxy:
        """
        Data class representing a proxy section in the configuration
        """
        enabled: bool
        x_for: int
        x_proto: int
        x_host: int
        x_port: int
        x_prefix: int

        def __init__(self, config):
            enabled = config.get("network", {}).get("proxy", {}).get("enabled", DEFAULT_PROXY_ENABLED)
            x_for = config.get("network", {}).get("proxy", {}).get("x_for", DEFAULT_PROXY_X_FOR)
            x_proto = config.get("network", {}).get("proxy", {}).get("x_proto", DEFAULT_PROXY_X_PROTO)
            x_host = config.get("network", {}).get("proxy", {}).get("x_host", DEFAULT_PROXY_X_HOST)
            x_port = config.get("network", {}).get("proxy", {}).get("x_port", DEFAULT_PROXY_X_PORT)
            x_prefix = config.get("network", {}).get("proxy", {}).get("x_prefix", DEFAULT_PROXY_X_PREFIX)

            check_bool(enabled, "proxy.enabled")
            check_bool(x_for, "proxy.x_for")
            check_bool(x_proto, "proxy.x_proto")
            check_bool(x_host, "proxy.x_host")
            check_bool(x_port, "proxy.x_port")
            check_bool(x_prefix, "proxy.x_prefix")

            self.enabled = enabled
            self.x_for = 1 if x_for else 0
            self.x_proto = 1 if x_proto else 0
            self.x_host = 1 if x_host else 0
            self.x_port = 1 if x_port else 0
            self.x_prefix = 1 if x_prefix else 0

    @dataclass
    class Recaptcha:
        """
        Data class representing a recaptcha section in the configuration
        """
        enabled: bool
        minimal_score: float
        verify_ip: bool
        site_key: str

        def __init__(self, config):
            enabled = config.get("recaptcha", {}).get("enabled", DEFAULT_RECAPTCHA_ENABLED)
            minimal_score = config.get("recaptcha", {}).get("minimal_score", DEFAULT_RECAPTCHA_MIN_SCORE)
            verify_ip = config.get("recaptcha", {}).get("verify_ip", DEFAULT_RECAPTCHA_VERIFY_IP)
            site_key = config.get("recaptcha", {}).get("site_key", DEFAULT_RECAPTCHA_SITE_KEY)

            check_bool(enabled, "recaptcha.enabled")
            check_float(minimal_score, "recaptcha.minimal_score", 0, 1)
            check_bool(verify_ip, "recaptcha.verify_ip")
            check_string(site_key, "recaptcha.site_key")

            self.enabled = enabled
            self.minimal_score = minimal_score
            self.verify_ip = verify_ip
            self.site_key = site_key

    def __init__(self, config: dict):
        if not isinstance(config, dict):
            raise TypeError("Config object must be a dictionary (dict)")

        self.Utils = self.Utils(config)
        self.Proxy = self.Proxy(config)
        self.Recaptcha = self.Recaptcha(config)


def check_character_list(item: Any, name: str) -> None:
    """
    Checks if the inputted value is exactly of a character list type

    :raises TypeError: on incorrect (non-character) type, even string is not acceptable
    :raises ValueError: if the item is not a list or is empty list
    :param item: Any value received from user
    :param name: Name, with which is the value recognisable in the logs
    :return: None
    """
    if not isinstance(item, list) or len(item) == 0:
        raise ValueError(f"{name} must be a list and cannot be empty")

    for character in item:
        if not isinstance(character, str) or len(character) != 1:
            raise TypeError(f"{name} must contain only characters")


def check_number(item: Any, name: str, minimum: int) -> None:
    """
    Checks if the inputted value is exactly of a float type
    and bigger than given border

    :raises ValueError: if number is not of an integer type or bigger than border
    :param item: Any value received from user
    :param name: Name, with which is the value recognisable in the logs
    :param minimum: minimal accepted value
    :return: None
    """
    if not isinstance(item, int) or item < minimum:
        raise ValueError(f"{name} must be a number larger than {minimum - 1}")


def check_float(item: Any, name: str, minimum: int, maximum: int) -> None:
    """
    Checks if the inputted value is exactly of a float type
    and between given borders

    :raises TypeError: on incorrect (non-float) type
    :raises ValueError: if number is not between borders
    :param item: Any value received from user
    :param name: Name, with which is the value recognisable in the logs
    :param minimum: minimal accepted value
    :param maximum: maximal accepted value
    :return: None
    """
    if not isinstance(item, float):
        raise TypeError(f"{name} must be a float")

    if item < minimum or item > maximum:
        raise ValueError(f"{name} be between {minimum} and {maximum}")


def check_bool(item: Any, name: str) -> None:
    """
    Checks if the inputted value is exactly of a boolean type

    :raises TypeError: on incorrect (non-bool) type
    :param item: Any value received from user
    :param name: Name, with which is the value recognisable in the logs
    :return: None
    """
    if not isinstance(item, bool):
        raise TypeError(f"{name} must be a boolean (bool)")


def check_string(item: Any, name: str) -> None:
    """
    Checks if the inputted value is exactly of a string type

    :raises TypeError: on incorrect (non-string) type
    :param item: Any value received from user
    :param name: Name, with which is the value recognisable in the logs
    :return: None
    """
    if not isinstance(item, str):
        raise TypeError(f"{name} must be a string (str)")


def load_toml_conf(filename: str) -> dict:
    """
    Loads the file represented by filename as byte array

    :exception OSError: same as open() function
    :param filename: name of the file to be read
    :return: byte array containing the contents of the file
    """
    logging.debug("Opening the file '%s'", filename)
    with open(filename, "rb") as conf_file:
        logging.debug("File '%s' opened, fd: %s", filename, conf_file.fileno())
        logging.debug("Parsing contents of '%s' to tomllib", filename)
        conf = tomllib.load(conf_file)
    logging.debug("Config loaded with tomllib, contents: %s", conf)

    return conf


def load_conf(filename: str) -> ConfigValues:
    """
    Loads the config given by the filename and parses it into ConfigValues object

    :exception ValueError: on the incorrect values
    :exception TypeError: on the type mismatch
    :exception OSError: same as open() function
    :param filename: name of the file containing the config
    :return: ConfigValues object containing the config contents
    """
    logging.debug("Going to load toml config from '%s'", filename)
    toml_conf = load_toml_conf(filename)
    logging.debug("TOML config loaded from '%s'", filename)
    conf_obj = ConfigValues(toml_conf)
    logging.info("Config loaded from '%s'", filename)

    return conf_obj


Utils = ConfigValues.Utils
Proxy = ConfigValues.Proxy
Recaptcha = ConfigValues.Recaptcha
