import string
import tomllib
from dataclasses import dataclass
from typing import Any

DEFAULT_ALPHABET = string.ascii_letters
DEAFULT_EXTENSIONS = ["_", "-"]
DEFAULT_LINK_LENGTH = 5
DEFAULT_CREATION_TRIES = 10
DEFAULT_DESTINATION_LENGTH = 50


@dataclass
class ConfigValues:
    link_alphabet: set[str]
    extensions_alphabet: set[str]
    link_length: int
    creation_tries: int
    destination_length: int

    def __init__(self, config: dict):
        if not isinstance(config, dict):
            raise TypeError("Config object must be a dictionary (dict)")

        link_alphabet = config.get("shortener", {}).get("utils", {}).get("alphabet", {}).get("link", DEFAULT_ALPHABET)
        extensions_alphabet = config.get("shortener", {}).get("utils", {}).get("alphabet", {}).get(
            "custom_link_extensions", DEAFULT_EXTENSIONS)
        link_length = config.get("shortener", {}).get("utils", {}).get("link_length", DEFAULT_LINK_LENGTH)
        creation_tries = config.get("shortener", {}).get("utils", {}).get("creation_tries", DEFAULT_CREATION_TRIES)
        dest_length = config.get("shortener", {}).get("utils", {}).get("max_destination_length", DEFAULT_DESTINATION_LENGTH)

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


def check_character_list(item: Any, name: str) -> None:
    if not isinstance(item, list) or len(item) == 0:
        raise ValueError(f"{name} must be a list and cannot be empty")

    for character in item:
        if not isinstance(character, str) or len(character) != 1:
            raise TypeError(f"{name} must contain only characters")


def check_number(item: Any, name: str, minimum: int) -> None:
    if not isinstance(item, int) or item < minimum:
        raise ValueError(f"{name} must be a number larger than {minimum - 1}")


def load_toml_conf(filename: str) -> dict:
    with open(filename, "rb") as conf_file:
        conf = tomllib.load(conf_file)

    return conf


def load_conf(filename: str) -> ConfigValues:
    toml_conf = load_toml_conf(filename)
    conf_obj = ConfigValues(toml_conf)

    return conf_obj
