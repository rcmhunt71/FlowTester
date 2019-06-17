#!/usr/bin/env python
import argparse
import os

from flowtester.logging import logger
from flowtester.state_machine.config.yaml_cfg import YamlInputFile
from flowtester.state_machine.engine.engine import StateMachine
from flowtester.state_machine.engine.engine_definition import MachineDefinition
from flowtester.state_machine.paths.path_yaml import StatePathsYaml
from flowtester.state_machine.validation.validate_engine_cfg import ValidateData
from vm_data_model.vm_model.vm_model import VmModel


class CLIArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument(
            "machine_cfg_file",
            help="State Machine Definition File: YAML format")

        self.parser.add_argument(
            "test_file_name",
            help="File containing possible machine paths to traverse")

        self.parser.add_argument(
            "-s", "--test_suite_name", default=None,
            help="Group of tests within test file to use")

        self.parser.add_argument(
            "-t", "--test_case_name", default=None,
            help="Name of test in test suite to execute")

        self.parser.add_argument(
            "--debug", "-d",
            action="store_true", default=False,
            help="Enable debug logging")

        self.parser.add_argument(
            "--list",
            action="store_true", default=False,
            help="List suites and test cases defined in the testfile")

        self.parser.add_argument(
            "--image", '-i',
            action="store_true", default=False,
            help="Generate image of state diagram")

        self.parser.add_argument(
            "--logfile", "-l",
            default=None,
            help="Name of log file to record")

        self.args = self.parser.parse_args()


def display_input_files(
        log: logger.Logger, model_file: str, test_file: str,
        ts_name: str, tc_name: str, log_file: str) -> None:
    """
    Logs configuration information about current execution.

    Args:
        log (logger.Logger) : Instantiated logger
        model_file (str): Name/Path of state machine definition file
        test_file (str): Name/Path of test definition file
        ts_name (str): Name of test suite
        tc_name (str): Name of test case
        log_file (str): Name of log file

    Returns:
        None

    """
    border = f"+{'-' * 100}"
    log.info(border)
    log.info(f"| STATE MODEL: {os.path.abspath(model_file)}")
    log.info(border)
    log.info(f"| TEST FILE:   {os.path.abspath(test_file)}")
    log.info(f"| TEST SUITE:  {ts_name}")
    log.info(f"| TEST CASE:   {tc_name}")
    log.info(border)
    log.info(f"| LOG FILE:   {log_file}")
    log.info(border)


if __name__ == '__main__':

    graph_steps_per_line = 4
    step_log_border_num_stars = 180

    # Parse the CLI arguments
    args = CLIArgs()
    debug = args.args.debug
    machine_cfg_file = args.args.machine_cfg_file
    test_file_name = args.args.test_file_name
    test_suite_name = args.args.test_suite_name
    test_case_name = args.args.test_case_name

    # Set up the logging
    logfile = args.args.logfile
    logging_level = logger.Logger.STR_TO_VAL['debug' if debug else 'info']
    logging = logger.Logger(default_level=logging_level,
                            filename=logfile)
    logging.debug(f"Logging Project: {logging.project}")
    if logfile is not None:
        logfile = os.path.abspath(logfile)

    # Get the selected test case info
    tests = StatePathsYaml(input_file=test_file_name)

    # If requested, display the test suites and test cases based on the
    # CLI input
    if args.args.list:
        print(tests.list_test_info(test_suite=test_suite_name))
        exit()

    # ERROR: no test suite or test case specified
    elif (args.args.test_suite_name is None or
          args.args.test_case_name is None):
        logging.error("Need to specify test_suite_name AND test_case_name.")
        exit(1)

    # List the input files for reference
    display_input_files(log=logging, model_file=machine_cfg_file,
                        test_file=test_file_name, ts_name=test_suite_name,
                        tc_name=test_case_name, log_file=logfile)

    # Parse the state machine definitions
    model_data = MachineDefinition(YamlInputFile(
        machine_cfg_file).data)

    # Validate that the state machine configuration is valid (static assessment)
    validation = ValidateData(model_data)
    if not (validation.validate_all_transitions() and
            validation.validate_initial_state()):
        logging.error("State Machine definitions are not correct.")
        exit()

    # Instantiate the Object model
    server_model = VmModel()

    # Instantiate and build the state machine
    machine = StateMachine(data_model=model_data, object_model=server_model)
    machine.BORDER_LEN = step_log_border_num_stars
    machine.NUM_ELEMS_PER_GRAPH_LINE = graph_steps_per_line
    machine.configure_state_machine()

    # Show a table with all of the state machine state definitions in the
    # specified state machine configuration file
    model_data.describe_model()

    # Get the requested test case
    test_case = tests.build_test_case(
        test_suite=test_suite_name, test_name=test_case_name)
    if not test_case:
        logging.error('Test path does not have any triggers defined.')
        exit()

    # Validate that the test case contains valid transitions
    # (all transitions exist in the state machine)
    if model_data.validate_path(tests.get_traversal_path()):
        logging.info(f"Traversal Path: {tests.get_traversal_path()}")

        # Execute the state machine
        machine.execute_state_machine(
            input_data=test_case,
            description=f"({test_suite_name}:{test_case_name})")

        # Log the results
        logging.info(f"FINAL STATE: {machine.state}")
        logging.info(f"FINAL OBJECT MODEL:\n{machine.object_model}")

        logging.info(f"\n\n{machine.traversal_path()}")
        logging.info(f"\n\n{machine.execution_summary(detailed=True)}")

    # If requested, generate a PNG of the state machine configuration.
    if args.args.image:
        machine.generate_image()
