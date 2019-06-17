
import os
import traceback
import typing

import yaml
from yaml.parser import ParserError

from flowtester.logging.logger import Logger


logging = Logger()


class YamlInputFile:
    def __init__(self, input_file):
        self.input_file = input_file
        self.data = self.read_file()

    def read_file(self) -> typing.Dict:
        """
        Read contents of YAML file from disk.

        Returns:
            (dict) - Nested dictionary of data from file
                   - Empty dict if unable to read YAML from file
        """
        data = {}
        if self.does_input_file_exist():
            with open(self.input_file, "r") as input_file:
                try:
                    data = yaml.safe_load(input_file)
                except yaml.parser.ParserError:
                    logging.error("Malformed YAML file.")
                    logging.error(traceback.format_exc())
        else:
            logging.error(f"Error: '{self.input_file}' was not found.")

        return data

    def does_input_file_exist(self) -> bool:
        """
        Determine if provided file exists (full path)

        Returns:
           (bool) True: file/path exists, False: file/path does not exist

        """
        return os.path.exists(self.input_file)
