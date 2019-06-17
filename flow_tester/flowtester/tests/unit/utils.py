import os
import re
from typing import List, Pattern, Tuple

from flowtester.state_machine.config.constants \
    import StateMachineConstants as SMConsts
from flowtester.logging.logger import Logger
from flowtester.state_machine.config.yaml_cfg import YamlInputFile
from flowtester.state_machine.engine.engine_definition import MachineDefinition

logging = Logger()


def get_data_dir(
        test_dir_name: str = 'tests', data_dir_name: str = 'data') -> str:
    """

    Uses path of this file to determine location of the data directory
    required for testing YAML files

    Args:
        test_dir_name (str): NAME (not full path) of tests subdirectory
        data_dir_name (str): NAME (not full path) of data subdirectory

    Returns:
        (str) Path to the test data directory

    """
    path = ''

    # Get the current path and reduce to a list
    path_parts = os.path.abspath(__file__).split(os.path.sep)

    # Try to find the tests directory.
    # If not found, log an error and return an empty string
    try:
        tests_subdir = path_parts.index(test_dir_name)

    except ValueError:
        logging.error("Unable to determine test directory")

    # If found, rebuild path up to the tests directory and add the data
    # subdirectory to the path
    else:
        tests_dir = os.path.sep.join(path_parts[:tests_subdir + 1])
        path = os.path.sep.join([tests_dir, data_dir_name])

    return path


def get_data_file(
        filename: str, test_dir_name: str = 'tests',
        data_dir_name: str = 'data') -> str:
    """
    Get the name/filespec for the test/data file.

    Args:
        filename (str): name of data file
        test_dir_name (str) : NAME (not full path) of tests subdirectory
        data_dir_name (str): NAME (not full path) of data subdirectory

    Returns:
        Full/absolute path to specified data file
    """
    data_path = get_data_dir(
        test_dir_name=test_dir_name, data_dir_name=data_dir_name)
    return os.path.sep.join([data_path, filename])


def get_model_name_from_raw_file(yaml_file: str) -> str:
    """
    Get the model name directly from the YAML file
    Args:
        yaml_file: full name/file spec of state machine config yaml file

    Returns:
        Returned the name defined in the file. There is only model name,
        so return the first element of the list.

    """
    pattern = re.compile(r'^model:\s*(?P<model>\w+)')
    entries = find_all_entries(
        yaml_file=yaml_file, pattern=pattern, pattern_keyword='model')

    if not entries:
        logging.error(f"Unable to find the model name in {yaml_file}")
        entries.append('')

    return entries[0]


def get_states_from_raw_file(yaml_file):
    """
    Looks for states, as defined in the state machine definition YAML FILE

    Args:
        yaml_file: full name/file spec of state machine config yaml file

    Returns:
        list of states defined in the file.
          States cannot be prefixed and suffixed with '__' <- reserved for
          special non-state keywords.
          Prefix defined in StateMachineConstants.NON_STATE_PREFIX

    """
    # SEARCH PATTERN:
    # At the beginning of the line:
    # - <STATE>:
    # targeting text within the STATE
    pattern = re.compile(r'^-\s*(?P<state>\w+)\s*:')
    matches = find_all_entries(
        yaml_file=yaml_file, pattern=pattern, pattern_keyword='state')
    return [x for x in matches if not x.startswith(SMConsts.NON_STATE_PREFIX)
            and not x.endswith(SMConsts.NON_STATE_PREFIX)]


def get_triggers_from_raw_file(yaml_file: str) -> List[str]:
    """
    Looks for all triggers, as defined in the state machine definition YAML FILE

    Args:
        yaml_file: full name/file spec of state machine config yaml file

    Returns:
        list of triggers defined in the file.

    """
    # SEARCH PATTERN:
    # At the beginning of the line:
    # - <TRIGGER>:
    # targeting text within the TRIGGER
    pattern = re.compile(r'trigger_name:\s*(?P<trigger>[\w_]+)\s*')
    return find_all_entries(
        yaml_file=yaml_file, pattern=pattern, pattern_keyword='trigger')


def find_all_entries(
        yaml_file: str, pattern: Pattern, pattern_keyword: str) -> List[str]:
    """
    Search the YAML file for specific data patterns and return all matches

    Args:
        yaml_file (str): Full path/filespec for yaml file
        pattern: Regexp pattern to search (should be the results of
            re.compile())
        pattern_keyword: Keyword/name within pattern to identify specific match
             pattern (?P<name>pattern)

    Returns:
        List of pattern matches

    """
    matches = []
    with open(yaml_file, 'r') as data:
        lines = data.readlines()

    for idx, line in enumerate(lines):
        match = re.search(pattern, line)
        if match is not None:
            matches.append(match.group(pattern_keyword))
    return matches


def setup_state_machine_definitions(
        def_file: str) -> Tuple[str, YamlInputFile, MachineDefinition]:
    """
    Load the configuration from file and creates a state machine definition.

    Returns:
        Tuple of model_definition_file (str), model_cfg (YamlInputFile Obj),
        and MachineDefinition obj.

    """
    # Determine the data directory ad build the config file's absolute path
    model_definition_path = get_data_dir()
    model_definition_filename = os.path.sep.join(
        [model_definition_path, def_file])

    logging.info(f"State Machine Config File: {model_definition_filename}")

    # Read and parse the state machine definition YAML file
    model_cfg = YamlInputFile(input_file=model_definition_filename)
    logging.info(f"Model Definition: {model_cfg.data}")

    # Create the model definition
    model_def = MachineDefinition(data=model_cfg.data)

    return model_definition_filename, model_cfg, model_def
