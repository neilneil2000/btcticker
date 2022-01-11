from typing import List
import os
import logging
import yaml


class Params:
    """Config Class"""

    config_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "config.yaml"
    )

    def __init__(self, filename: str = config_file) -> None:
        self.logger = logging.getLogger("btcticker.config")
        self.config = {}
        self.read_from_file(filename)
        self.parse_config_file()

    def parse_config_file(self) -> None:
        """Parse YAML Config file and store attributes"""
        self.cryptos = self.string_to_list(self.config["ticker"]["currency"])
        self.fiats = self.string_to_list(self.config["ticker"]["fiatcurrency"])
        self.cycle = self.config["display"]["cycle"]
        self.orientation = self.config["display"]["orientation"]
        self.colour = self.config["display"]["colour"]
        self.inverted = self.config["display"]["inverted"]
        self.show_rank = self.config["display"]["showrank"]
        self.show_volume = self.config["display"]["showvolume"]

        self.days = int(self.config["ticker"]["sparklinedays"])
        self.exchange = self.config["ticker"]["exchange"]

        self.update_frequency = max(
            5.0, float(self.config["ticker"]["updatefrequency"])
        )

    def read_from_file(self, filename: str = config_file) -> None:
        """Read YAML file"""
        with open(filename, "r", encoding="utf-8") as file:
            self.config = yaml.load(file, Loader=yaml.FullLoader)
        self.logger.debug(self.config)

    def write_to_file(self, filename: str = config_file) -> None:
        """Write Yaml File to Disk"""
        with open(filename, "w", encoding="utf-8") as file:
            yaml.dump(self.config, file)

    def next_item(self, my_list: List[any], index: int) -> int:
        """Increment pointer and wrap at end of list"""
        next_index = index + 1
        if next_index >= my_list.len():
            next_index = 0
        return next_index

    def string_to_list(self, string: str) -> List[str]:
        """Convert string to list using commas as seperators and stripping whitespace"""
        my_list = string.split(",")
        my_list = [x.strip(" ") for x in my_list]
        return my_list
