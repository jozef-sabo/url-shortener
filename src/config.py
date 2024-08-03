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


@dataclass
class ConfigValues:
    @dataclass
    class Utils:
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

    def __init__(self, config: dict):
        if not isinstance(config, dict):
            raise TypeError("Config object must be a dictionary (dict)")

        self.Utils = self.Utils(config)
        self.Proxy = self.Proxy(config)


def check_character_list(item: Any, name: str) -> None:
    if not isinstance(item, list) or len(item) == 0:
        raise ValueError(f"{name} must be a list and cannot be empty")

    for character in item:
        if not isinstance(character, str) or len(character) != 1:
            raise TypeError(f"{name} must contain only characters")


def check_number(item: Any, name: str, minimum: int) -> None:
    if not isinstance(item, int) or item < minimum:
        raise ValueError(f"{name} must be a number larger than {minimum - 1}")


def check_bool(item: Any, name: str) -> None:
    if not isinstance(item, bool):
        raise ValueError(f"{name} must be a boolean (bool)")


def load_toml_conf(filename: str) -> dict:
    with open(filename, "rb") as conf_file:
        conf = tomllib.load(conf_file)

    return conf


def load_conf(filename: str) -> ConfigValues:
    toml_conf = load_toml_conf(filename)
    conf_obj = ConfigValues(toml_conf)

    return conf_obj


Utils = ConfigValues.Utils
Proxy = ConfigValues.Proxy
