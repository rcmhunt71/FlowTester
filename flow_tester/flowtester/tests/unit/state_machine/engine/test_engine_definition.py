import pprint
from typing import Any, Dict

from mock import patch
import prettytable

from flowtester.logging.logger import Logger
from flowtester.state_machine.config.constants \
    import StateMachineConstants as SMConsts
from flowtester.state_machine.engine.engine_definition import MachineDefinition
from flowtester.tests.unit.utils import (
    get_triggers_from_raw_file,
    get_states_from_raw_file,
    setup_state_machine_definitions)

from nose.tools import (assert_equals, assert_true, assert_false,
                        assert_is_none, assert_in)

logging = Logger()


class TestMachineDefinition:

    MACHINE_DEFINITION_FILE = 'general_sample.yaml'
    TRIGGER_NAME = 'TEST'
    VALID_TEST_STATE = 'ACTIVE'
    VALID_TEST_STATE_INDEX = 3
    VALID_TEST_STATE_DESCRIPTION = "STATE: Server is in ACTIVE state."
    VALID_TRANSITION_NAME = 'REBOOT'
    VALID_TRANSITION_INDEX = 3
    NUMBER_OF_TRANSITIONS = 6

    INVALID_TEST_STATE = 'DoesNOtexistz'
    MULTI_TRIGGER_STATES = [f'STATE_{x}' for x in range(8)]

    def test_get_model_name(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        model_name = model_def.get_model_name()
        assert_equals(model_name, model_cfg.data[SMConsts.MODEL_NAME])

    def test_get_initial_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        init_state = model_def.get_initial_state()
        assert_equals(init_state, model_cfg.data[SMConsts.INITIAL_STATE])

    def test_get_initial_state_is_none(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        model_def.data[SMConsts.INITIAL_STATE] = None

        init_state = model_def.get_initial_state()
        assert_is_none(init_state)

    def test_get_state_definitions(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        defs = model_def.get_state_definitions()

        # Get all of the states (but remove the entries prefixed with
        # the StateMachineConstants.NON_STATE_PREFIX)
        test_model = model_cfg.data[SMConsts.DEFINITION]
        test_model = [x for x in test_model if
                      not list(x.keys())[0].startswith(
                          SMConsts.NON_STATE_PREFIX)]

        num_states = len(test_model)
        logging.debug(f"\nExpected Number of States: {num_states}:\n"
                      f"{test_model}")
        logging.debug(f"Received: {len(defs)}:\n{defs}")

        assert_true(defs, isinstance(defs, list))
        assert_equals(len(defs), num_states)

    def test_get_state_definition_with_existing_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        state_def = model_def.get_state_definition(state=self.VALID_TEST_STATE)

        logging.info(f"STATE NAME: {self.VALID_TEST_STATE}")
        logging.info(f"EXPECTED STATE DESCRIPTION: "
                     f"{self.VALID_TEST_STATE_DESCRIPTION}")
        logging.info(state_def)

        assert_true(isinstance(state_def, dict))
        assert_equals(state_def[SMConsts.DESCRIPTION],
                      self.VALID_TEST_STATE_DESCRIPTION)

    def test_get_state_definition_with_non_existing_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        state_def = model_def.get_state_definition(
            state=self.INVALID_TEST_STATE)

        assert_true(isinstance(state_def, dict))
        assert_equals(state_def, {})

    def test_get_list_of_states(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        expected_states = get_states_from_raw_file(yaml_file=cfg_file)
        returned_states = model_def.get_list_of_states()

        logging.info(f"Expected States: {expected_states}")
        logging.info(f"Returned States: {returned_states}")

        assert_equals(set(expected_states) ^ set(returned_states), set())

    def test__is_state_valid_with_valid_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        assert_true(model_def._is_state_valid(self.VALID_TEST_STATE))

    def test__is_state_valid_with_invalid_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        assert_false(model_def._is_state_valid(self.INVALID_TEST_STATE))

    def test_get_state_validation_methods_valid_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        validations = model_def.get_state_validation_methods(
            self.VALID_TEST_STATE)

        assert_true(isinstance(validations, list))
        assert_equals(len(validations), 2)
        assert_true(isinstance(validations[0], dict))
        assert_equals(validations[0][SMConsts.NAME],
                      self.VALID_TEST_STATE.lower())

    def test_get_state_validation_methods_invalid_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        validations = model_def.get_state_validation_methods(
            self.INVALID_TEST_STATE)
        assert_equals(validations, [])

    def test_get_transitions_for_invalid_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        transitions = model_def.get_transitions(self.INVALID_TEST_STATE)
        assert_equals(transitions, [])

    def test_get_transitions_for_valid_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        transitions = model_def.get_transitions(self.VALID_TEST_STATE)
        assert_equals(len(transitions), self.NUMBER_OF_TRANSITIONS)
        assert_true(isinstance(transitions[0], dict))
        assert_in(self.VALID_TRANSITION_NAME,
                  [x[SMConsts.TRIGGER_NAME] for x in transitions])

    def test_get_transitions_for_none_state(self):
        _, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        transitions = model_def.get_transitions(None)
        assert_equals(transitions, [])

    def test_get_all_triggers(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        expected_triggers = get_triggers_from_raw_file(cfg_file)
        reported_triggers = model_def.get_all_triggers()

        logging.info(f"EXPECTED TRIGGERS: {expected_triggers}")
        logging.info(f"REPORTED TRIGGERS: {reported_triggers}")

        assert_equals(set(expected_triggers) ^ set(reported_triggers), set())

    def test_describe_model_does_not_crash(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        assert_true(isinstance(model_def.describe_model(), str))

    def test_get_transition_info_for_valid_state(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        transitions = model_def.get_transitions(self.VALID_TEST_STATE)
        trans_tuple = (t_name, t_dest, t_method) = \
            model_def.get_transition_info(transitions[0])
        logging.info(f"Expected transition Data (not in order): "
                     f"{set(list(transitions[0].values()))}")
        logging.info(f"Received transition Data tuple: {set(trans_tuple)}")

        assert_equals(t_name, transitions[0][SMConsts.TRIGGER_NAME])
        assert_equals(t_dest, transitions[0][SMConsts.DESTINATION_STATE])
        assert_equals(t_method, transitions[0][SMConsts.CHANGE_STATE_ROUTINE])

    def test_get_transition_info_for_invalid_state(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        transitions = model_def.get_transitions(self.INVALID_TEST_STATE)
        assert_equals(transitions, [])

    def test_get_transition_info_for_undefined_transition(self):
        error_msg = 'Not Found'

        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        transitions = model_def.get_transitions(self.VALID_TEST_STATE)
        transitions[0] = {}

        trans_tuple = model_def.get_transition_info(transitions[0])
        logging.info(f"Expected transition Data (not in order): "
                     f"{[error_msg for _ in range(3)]}")
        logging.info(f"Received transition Data tuple: {set(trans_tuple)}")

        for msg in trans_tuple:
            assert_equals(msg, error_msg)

    def test_get_transition_info_by_name_valid_state_and_name(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        trigger_info = model_def.get_transition_info_by_name(
            state_name=self.VALID_TEST_STATE,
            trigger_name=self.VALID_TRANSITION_NAME)

        transitions = model_def.get_transitions(
            self.VALID_TEST_STATE)[self.VALID_TRANSITION_INDEX]
        for key, value in transitions.items():
            assert_true(key in trigger_info)
            assert_equals(value, trigger_info[key])

    def test_get_transition_info_by_name_valid_state_and_invalid_name(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        trigger_info = model_def.get_transition_info_by_name(
            state_name=self.VALID_TEST_STATE,
            trigger_name=self.INVALID_TEST_STATE)

        assert_equals(trigger_info, {})

    def test_get_transition_info_by_name_invalid_state_and_name(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        trigger_info = model_def.get_transition_info_by_name(
            state_name=self.INVALID_TEST_STATE,
            trigger_name=self.INVALID_TEST_STATE)

        assert_equals(trigger_info, {})

    def test_validate_path_with_valid_path(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        path = get_triggers_from_raw_file(yaml_file=cfg_file)
        assert_true(model_def.validate_path(path))

    def test_validate_path_with_invalid_path(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        path = get_states_from_raw_file(yaml_file=cfg_file)
        assert_false(model_def.validate_path(path))

    def test_validate_multi_triggers(self):
        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        triggers = model_def.get_multi_triggers()
        validated_triggers = model_def.validate_multi_triggers(triggers)

        assert_true(isinstance(validated_triggers, list))
        assert_true(validated_triggers)

    def test_get_multi_triggers(self):
        expected_trigger_names = [
            'multi_trigger_test_from_all',
            'multi_trigger_test_from_select_states']

        cfg_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        triggers = model_def.get_multi_triggers()
        trigger_names = [x.get(SMConsts.TRIGGER_NAME) for x in triggers]

        assert_true(isinstance(triggers, list))
        assert_true(triggers)
        assert_equals(expected_trigger_names, trigger_names)

    def test__add_trigger_to_table_valid_with_wc(self):
        wildcard = '*'
        multi_trigger_defs_source_wc = {
            SMConsts.TRIGGER_NAME: 'test1',
            SMConsts.DESCRIPTION: 'test1_description',
            SMConsts.CHANGE_STATE_ROUTINE: "test1_callback",
            SMConsts.DESTINATION_STATE: 'STATE_3',
            SMConsts.SOURCE_STATES: wildcard
        }

        table = self.__add_trigger_to_table_content(
            trigger_def=multi_trigger_defs_source_wc)
        assert_true(isinstance(table, prettytable.PrettyTable))
        assert_in(wildcard, table.get_string())

    def test__add_trigger_to_table_valid_with_source_state_list(self):
        source_states = ['STATE_1', 'STATE_2', 'STATE_3', 'STATE_40']
        multi_trigger_defs_source_list = {
            SMConsts.TRIGGER_NAME: 'test1',
            SMConsts.DESCRIPTION: 'test1_description',
            SMConsts.CHANGE_STATE_ROUTINE: "test1_callback",
            SMConsts.DESTINATION_STATE: 'STATE_3',
            SMConsts.SOURCE_STATES: source_states
        }

        table = self.__add_trigger_to_table_content(
            trigger_def=multi_trigger_defs_source_list)
        assert_true(isinstance(table, prettytable.PrettyTable))

        # Verify each source state is diplayed in the table
        table_str = table.get_string()
        for state in source_states:
            assert_in(state, table_str)

    def test__add_trigger_to_table_empty(self):
        table = self.__add_trigger_to_table_content(trigger_def=dict())
        assert_true(isinstance(table, prettytable.PrettyTable))

    def test__add_trigger_to_table_is_none(self):
        table = self.__add_trigger_to_table_content(trigger_def=None)
        assert_true(isinstance(table, prettytable.PrettyTable))

    @patch('flowtester.state_machine.engine.engine_definition.'
           'MachineDefinition.get_state_validation_methods',
           return_value=[{
               SMConsts.NAME: "id",
               SMConsts.ROUTINE: "routine"}
           ])
    @patch('flowtester.state_machine.engine.engine_definition.'
           'MachineDefinition.get_transitions', return_value=[])
    def __add_trigger_to_table_content(
            self, mocked_validation: patch, mocked_trans: patch,
            trigger_def: Dict[str, Any]) -> prettytable.PrettyTable:
        """
        Add the data to the table content. Single routine to assist with the
        testing.

        Args:
            mocked_validation (patch): Mocked get_state_validation call
            mocked_trans (patch): Mocked get_transitions
            trigger_def (dict): Dictionary of multi-source trigger definition

        Returns:
            Populated table (prettytable.PrettyTable)
        """
        col_dict = {
            MachineDefinition.STATE: 'Origin State',
            MachineDefinition.TRIGGER: 'Trigger',
            MachineDefinition.DESTINATION: 'Expected State',
            MachineDefinition.TRIGGER_METHOD: 'Trigger Method',
            MachineDefinition.VALIDATION_ID: 'Validation ID',
            MachineDefinition.VALIDATION_ROUTINE: 'Validation Routine',
            MachineDefinition.NOTES: 'Notes'
        }

        # Build table
        table = prettytable.PrettyTable()
        table.field_names = list(col_dict.values())

        # Build machine definition for table output
        model_def = MachineDefinition(data={})
        updated_table = model_def._add_trigger_to_table(
            table_obj=table, col_dict=col_dict,
            trigger=trigger_def)

        # Display results (on failure or debugging)
        logging.debug(pprint.pformat(updated_table.get_string()))
        return table
