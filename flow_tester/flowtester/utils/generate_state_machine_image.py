#!/usr/bin/env python
import argparse

import flowtester.logging.logger as logger
from flowtester.state_machine.config.yaml_cfg import YamlInputFile
from flowtester.state_machine.engine.engine import StateMachine
from flowtester.state_machine.engine.engine_definition import MachineDefinition
from flowtester.state_machine.validation.validate_engine_cfg import ValidateData


class CLIArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument(
            "machine_cfg_file",
            help="State Machine Definition File: YAML format")

        self.parser.add_argument(
            '-f', '--filename', default=None,
            help="Filename to save as. Default: '<Model Name>.png'")

        self.parser.add_argument(
            "--debug", "-d",
            action="store_true", default=False,
            help="Enable debug logging")

        self.args = self.parser.parse_args()


if __name__ == '__main__':

    args = CLIArgs()

    debug = args.args.debug

    machine_cfg_file = args.args.machine_cfg_file

    logging_level = logger.Logger.STR_TO_VAL['debug' if debug else 'info']
    project = logger.Logger.determine_project()
    logging = logger.Logger(project=project, default_level=logging_level)

    model_data = MachineDefinition(YamlInputFile(
        machine_cfg_file).data)

    validation = ValidateData(model_data)
    if not (validation.validate_all_transitions() and
            validation.validate_initial_state()):
        logging.error("State Machine definitions are not correct. "
                      "Cannot generate image.")
        exit()

    machine = StateMachine(data_model=model_data, object_model=None)
    machine.configure_state_machine()
    model_data.describe_model()
    machine.generate_image(filename=args.args.filename)
