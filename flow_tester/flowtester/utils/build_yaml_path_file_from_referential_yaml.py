#!/usr/bin/env python
import argparse
import pprint
import typing
import yaml

from flowtester.logging import logger
from flowtester.state_machine.paths.path_yaml import StatePathsYaml
from flowtester.state_machine.paths.path_consts import YamlPathConsts as Consts


class CLIArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument(
            "relative_yaml_path_file",
            help="File containing possible machine paths to traverse")

        self.parser.add_argument(
            "output_file",
            help="Name of output YAML file")

        self.parser.add_argument(
            "--full", "-f",
            action="store_true", default=False,
            help="Write full YAML file (includes modification directives.")

        self.parser.add_argument(
            "--debug", "-d",
            action="store_true", default=False,
            help="Enable debug logging")

        self.args = self.parser.parse_args()


def check_output_file(filename, extension='yaml') -> str:
    """
    Check the output file extension to assure correct format extension
    Args:
        filename (str): Filespec of output file
        extension (str): File extension (DEFAULT: yaml)

    Returns:
        (str) Updated/corrected filespec (filename extension only)

    """
    if not filename.lower().endswith(extension):
        filename = f"{filename}.{extension}"

    logging.debug(f"Output file name: {filename}")
    return filename


def process_referential_yaml(data: typing.List[dict]) -> None:
    """
    Remove referential data elements from YAML, so that it reflcts a
    standard path YAML format.

    Args:
        data (List[dict]): Final YAML file contents

    Returns:
        None (Dictionary is directly updated in memory)
    """
    elements_to_be_removed = [Consts.REFERENCE, Consts.ADD_STEPS,
                              Consts.DEL_STEPS, Consts.MOD_STEPS]

    # Go through each test suite (list of dictionaries)
    for ts_data in data:

        # Each test suite value is a test suite definition
        test_suites = ts_data.values()
        logging.debug(f"\n\nTEST SUITES:\n{pprint.pformat(list(test_suites))}")

        # Get the test cases for the current test suite
        for tc_data in test_suites:
            logging.debug(f"\n\n TEST CASE DATA:\n"
                          f"{pprint.pformat(list(tc_data.values()))}")

            # Each value is a test case definition
            for tc in tc_data.values():
                logging.debug(f"\n\nEACH TEST CASE:\n{pprint.pformat(tc)}")

                # Remove each specified element from the dictionary
                # (if it is present)
                for attr in elements_to_be_removed:
                    if attr in tc:
                        del tc[attr]

    # The final product should not have any of the 'elements_to_be_removed'
    # keys in the dictionaries
    logging.debug(f"\n\nFINAL:\n{pprint.pformat(data)}")


def output_data_as_yaml(data: typing.List[dict], filename: str) -> None:
    """
    Output the data to a YAML file.

    Args:
        data (List[dict]): Test suite configurations.
        filename (str): Name of file to write data.

    Returns:
        None

    """
    with open(filename, "w") as yaml_file:
        yaml.dump(data, yaml_file)
        logging.info(f"Wrote fully constructed YAML file to: {filename}.")


def main() -> None:
    """
    Primary execution routine.

    Returns:
        None

    """
    # Get the selected test case info
    tests = StatePathsYaml(input_file=args.args.relative_yaml_path_file).data
    if not args.args.full:
        process_referential_yaml(tests)

    # Write the data to file
    output_file = check_output_file(filename=args.args.output_file)
    output_data_as_yaml(data=tests, filename=output_file)

    logging.info("Done.\n")


if __name__ == '__main__':
    args = CLIArgs()
    debug = args.args.debug

    logging_level = logger.Logger.STR_TO_VAL[
        'debug' if args.args.debug else 'info']

    logging = logger.Logger(default_level=logging_level)
    logging.debug(f"Logging Project: {logging.project}")

    main()
