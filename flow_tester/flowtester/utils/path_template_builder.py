#!/usr/bin/env python
import argparse
import pprint
import typing

import yaml

import flowtester.logging.logger as logger
from flowtester.state_machine.paths.path_yaml import YamlPathConsts as Consts


# DEFAULT NUMBER OF TRANSITIONS
NUM_SUITES = 2
NUM_STEPS = 5

# YAML FILE EXTENSION
EXTENSION = '.yaml'


def write_to_file(model_list: list, output_file: str) -> None:
    """
    Write python data structure to file in YAML format

    Args:
        model_list: Data structure to cast into YAML
        output_file: YAML File to create

    Returns:
        None
    """
    if not output_file.lower().endswith(EXTENSION):
        output_file += EXTENSION

    with open(output_file, "w") as yaml_out_fd:
        yaml.dump(model_list, yaml_out_fd)

    logging.info(f"Wrote to: '{output_file}'\n")


def build_model(num_suites: int, num_test_cases: int, num_steps: int) -> list:
    """
    Build the path definition structure (nested, native python structures)
    Args:
        num_suites: Number of test suites to build
        num_test_cases: Number of test cases per suite
        num_steps: Number of steps per test case

    Returns:
        List of testsuites (nested, native data structures)

    """
    # Define root model
    model_dict = {}

    # Build Test Suite
    for ts_num in range(1, num_suites + 1):
        ts_name = f"<test_suite_{ts_num}>"
        model_dict[ts_name] = {}

        # Create specified number of test cases, and add to definition
        for tc_num in range(1, num_test_cases + 1):

            tc_name = f"<test_name_{tc_num}>"
            tc_definition = {tc_name: {Consts.DESCRIPTION: "<description>"}}

            # Build steps for test case (step = dictionary)
            step_dict = {Consts.STEPS: []}
            for step_num in range(1, num_steps + 1):
                step_name = f'<step_name_{step_num}>'
                step_def = {
                    step_name:
                        {Consts.ID: "<unique_step_id>",
                         Consts.DATA: [f'<arg_{i}>' for i in range(1, 3)],
                         Consts.EXPECTATIONS:
                             {f'<validation_id_{i}>': '<boolean result>'
                              for i in range(1, 3)}
                         }
                }

                # Add step to test case steps
                step_dict[Consts.STEPS].append(step_def)

            # Add tc_case steps to test case:
            #    tc_case steps = list of dictionaries
            tc_definition[tc_name].update(step_dict)

            model_dict[ts_name].update(tc_definition)

    logging.debug(f"\nYAML TEMPLATE:\n{pprint.pformat(model_dict)}\n")

    # model dictionary is a list of dictionaries.
    return [model_dict]


def get_args() -> typing.Tuple[int, str, bool]:
    """
    Parse the CLI args

    Returns:
        Tuple of number of test cases, name of output file, debug flag

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("num_test_cases",
                        type=int,
                        help="Number of test cases in each test suite "
                             "in the path file")
    parser.add_argument("yaml_out_file",
                        type=str,
                        help="Name of yaml template file to create")
    parser.add_argument('-d', '--debug',
                        action="store_true", default=False,
                        help="Enable debug logging")

    args = parser.parse_args()

    return int(args.num_test_cases), args.yaml_out_file, args.debug


if __name__ == '__main__':

    # Parse Args
    number_of_test_cases, yaml_file, debug = get_args()

    # Setup logging
    logging_level = logger.Logger.STR_TO_VAL['debug' if debug else 'info']
    project = logger.Logger.determine_project()
    logging = logger.Logger(project=project, default_level=logging_level)

    # Build model
    model = build_model(num_suites=NUM_SUITES,
                        num_test_cases=number_of_test_cases,
                        num_steps=NUM_STEPS)

    # Write the template to file
    write_to_file(model_list=model, output_file=yaml_file)
