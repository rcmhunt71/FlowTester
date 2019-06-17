#!/usr/bin/env python
import argparse
from copy import deepcopy
import logging
import pprint
import typing

import yaml

import flowtester.logging.logger as logger
from flowtester.state_machine.config.constants \
    import StateMachineConstants as SMConsts


# DEFAULT NUMBER OF TRANSITIONS
NUM_TRANSITIONS = 4

# YAML FILE EXTENSION
EXTENSION = '.yaml'

# NUMBER OF MULTI_TRIGGER YAML TEMPLATES TO INCLUDE (IF REQUESTED)
NUM_MULTI_TRIGGERS = 2

# NUMBER OF MULTI_TRIGGER YAML TEMPLATES TO INCLUDE (IF REQUESTED)
NUMBER_TRANSITIONS_PER_STATE = 2


def write_to_file(model_dict: dict, output_file: str) -> None:
    """
    Write the data structure to file in a YAML format.
    Args:
        model_dict (dict): data structure of template
        output_file (str): Name of file to write.

    Returns:
        None

    """
    # Check the file extension, add if necessary
    if not output_file.lower().endswith(EXTENSION):
        output_file += EXTENSION

    # Write to file
    with open(output_file, "w") as yaml_out_fd:
        yaml.dump(model_dict, yaml_out_fd)
    logging.info(f"Wrote to: '{output_file}'\n")


def build_model(
        num_states: int, num_transitions: int,
        multi_trigger: bool = False) -> dict:
    """
    Builds the required data structure that will be translated into YAML.

    Args:
        num_states (int): Number of states to template
        num_transitions (int): Number of transitions to template for each state
        multi_trigger (bool): Add the multi-template form to the data structure

    Returns:
        (dict) data structure that will be translated into YAML.

    """
    # Define template strings (used as descriptive text in the template)
    api_str = "<dotted.path.to.api.reference>"
    description = "<description>"
    entity_name = "<name>"
    model_description = "<model description>"
    source_states = '<Wildcard ("*") or list of states>'
    state_name = "<state_name>"
    trigger_name = "<trigger_name>"

    # Root model definition
    model_dict = {SMConsts.MODEL_NAME: entity_name,
                  SMConsts.DESCRIPTION: model_description,
                  SMConsts.INITIAL_STATE: state_name,
                  SMConsts.DEFINITION: []}

    # Basic validation definition
    validation_template = {
        SMConsts.NAME: entity_name,
        SMConsts.ROUTINE: api_str
    }

    # Basic transition definition
    transition_definition = {
        SMConsts.TRIGGER_NAME: trigger_name,
        SMConsts.DESTINATION_STATE: state_name,
        SMConsts.CHANGE_STATE_ROUTINE: api_str,
    }

    # Basic multi-trigger definition
    multi_trigger_def = {
        SMConsts.TRIGGER_NAME: trigger_name,
        SMConsts.DESCRIPTION: description,
        SMConsts.CHANGE_STATE_ROUTINE: api_str,
        SMConsts.DESTINATION_STATE: state_name,
        SMConsts.SOURCE_STATES: source_states
    }

    # Create specified number of states and append to definition
    for state_num in range(1, num_states + 1):
        state_id = f"STATE_{state_num}"
        state_definition = {
            state_id: {
                SMConsts.DESCRIPTION: description,
                SMConsts.VALIDATIONS: [
                    deepcopy(validation_template) for _ in
                    range(NUMBER_TRANSITIONS_PER_STATE)],

                SMConsts.TRANSITIONS: [
                    deepcopy(transition_definition) for _ in
                    range(num_transitions)
                ]
            }
        }
        model_dict[SMConsts.DEFINITION].append(state_definition)

    # If multi_trigger is requested/enabled...
    if multi_trigger:

        # Build the special trigger 'state' name
        special_trigger = (f"{SMConsts.NON_STATE_PREFIX}"
                           f"{SMConsts.MULTI_TRIGGERS}"
                           f"{SMConsts.NON_STATE_PREFIX}")

        # Define the trigger template and add it to the data structure
        mt_def = {
            special_trigger:
                [deepcopy(multi_trigger_def) for _ in
                 range(NUM_MULTI_TRIGGERS)]
        }
        model_dict[SMConsts.DEFINITION].append(mt_def)

    logging.debug(f"\nYAML TEMPLATE:\n{pprint.pformat(model_dict)}\n")

    return model_dict


def get_args() -> typing.Tuple[int, str, bool, bool]:
    """
    Parse the CLI options.

    Returns:
        Tuple of args:
          (int) Number of states to create
          (str) Name of YAML file to create
          (bool) Add multi-trigger definition to template
          (bool) Enable debugging logging

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("num_states",
                        type=int,
                        help="Number of states in the state machine")
    parser.add_argument("yaml_out_file",
                        type=str,
                        help="Name of the YAML template file to create")
    parser.add_argument('-m', '--multi_trigger',
                        action="store_true", default=False,
                        help="Add a multi-trigger definition to the template")
    parser.add_argument('-d', '--debug',
                        action="store_true", default=False,
                        help="Enable debug logging")

    args = parser.parse_args()

    # Disallow zero/negative number of states
    if args.num_states < 1:
        args.num_states = 1

    return (int(args.num_states),
            args.yaml_out_file,
            args.multi_trigger,
            args.debug)


if __name__ == '__main__':

    # Parse Args
    number_of_states, yaml_file, multi_trig, debug = get_args()

    # Setup logging
    logging_level = logger.Logger.STR_TO_VAL['debug' if debug else 'info']
    project = logger.Logger.determine_project()
    logging = logger.Logger(project=project, default_level=logging_level)

    if multi_trig:
        logging.info("Multi-trigger definitions to be added to the template.")

    # Build model
    model = build_model(num_states=number_of_states,
                        num_transitions=NUM_TRANSITIONS,
                        multi_trigger=multi_trig)

    # Write the template to file
    write_to_file(model_dict=model, output_file=yaml_file)
