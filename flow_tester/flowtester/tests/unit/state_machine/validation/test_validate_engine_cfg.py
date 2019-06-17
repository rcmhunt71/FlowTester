import copy

from flowtester.logging.logger import Logger
from flowtester.state_machine.config.constants \
    import StateMachineConstants as SMConsts
from flowtester.state_machine.validation.validate_engine_cfg \
    import (ValidateData, BadMultiTriggerDefinition)
from flowtester.tests.unit.utils import (
    setup_state_machine_definitions)

from nose.tools import assert_true, assert_false, assert_is_none, raises


logging = Logger()


class TestValidateData:

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
    MULTI_TRIGGER_DEFS = [
        {
            SMConsts.TRIGGER_NAME: 'test1',
            SMConsts.DESCRIPTION: 'test1_description',
            SMConsts.CHANGE_STATE_ROUTINE: "test1_callback",
            SMConsts.DESTINATION_STATE: 'STATE_3',
            SMConsts.SOURCE_STATES: '*'
        },
        {
            SMConsts.TRIGGER_NAME: 'test2',
            SMConsts.DESCRIPTION: 'test2_description',
            SMConsts.CHANGE_STATE_ROUTINE: "test2_callback",
            SMConsts.DESTINATION_STATE: 'STATE_5',
            SMConsts.SOURCE_STATES: '*'
        }
    ]

    def test_validate_all_transitions_with_no_states(self):
        model_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        # Remove all states (and transitions)
        model_def.data[SMConsts.DEFINITION] = {}

        # Validate the transitions (there are none!), should return False
        assert_false(ValidateData(model_def).validate_all_transitions())

    def test_validate_all_transitions_with_an_invalid_transition(self):
        bogus_transition = {
            SMConsts.CHANGE_STATE_ROUTINE: 'object_model.unlock_server',
            SMConsts.DESTINATION_STATE: self.INVALID_TEST_STATE,
            SMConsts.TRIGGER_NAME: 'BOGUS'
        }

        # Not pretty, but to meet PEP-8 line length, save to a tuple,
        # and then assign vars based on the tuple
        model_tuple = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        (model_file, model_cfg, model_def) = model_tuple

        # Add a transition (to any state) that points to an
        # unknown/undefined state
        state_def = model_def.data[SMConsts.DEFINITION][
            self.VALID_TEST_STATE_INDEX]
        state_def[self.VALID_TEST_STATE][SMConsts.TRANSITIONS].append(
            bogus_transition)

        # Validate the transitions, should return False
        assert_false(ValidateData(model_def).validate_all_transitions())

    def test_validate_all_transitions(self):
        model_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        assert_true(ValidateData(model_def).validate_all_transitions())

    def test_validate_initial_state(self):
        model_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        assert_true(ValidateData(model_def).validate_initial_state())

    def test_validate_initial_state_with_invalid_state(self):
        model_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        # Set initial state to an invalid state
        model_def.data[SMConsts.INITIAL_STATE] = self.INVALID_TEST_STATE

        # Validate the initial state, should return False
        assert_false(ValidateData(model_def).validate_initial_state())

    def test_validate_initial_state_with_none_value(self):
        model_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        # Set the initial state to None (should be equivalent
        # to invalid state)
        model_def.data[SMConsts.INITIAL_STATE] = None

        # Validate the initial state, should return False
        assert_false(ValidateData(model_def).validate_initial_state())

    def test_validate_initial_state_that_does_not_have_transitions(self):
        model_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)
        model_def.data[SMConsts.INITIAL_STATE] = self.VALID_TEST_STATE

        # Remove all transitions from initial_state definition
        state_def = model_def.data[SMConsts.DEFINITION][
            self.VALID_TEST_STATE_INDEX]
        state_def[self.VALID_TEST_STATE][SMConsts.TRANSITIONS] = []

        # Validate the initial state, should return False
        assert_false(ValidateData(model_def).validate_initial_state())

    def test_validate_multi_trigger_def_with_wildcard(self):
        assert_is_none(
            ValidateData.validate_multi_trigger_defs(
                list_of_trigger_defs=self.MULTI_TRIGGER_DEFS,
                defined_states=self.MULTI_TRIGGER_STATES
            )
        )

    def test_validate_multi_trigger_def_with_source_state_list(self):
        trigger_defs = copy.deepcopy(self.MULTI_TRIGGER_DEFS)
        state_set_1 = [x for index, x in enumerate(self.MULTI_TRIGGER_STATES)
                       if index % 2 == 0]
        state_set_2 = [x for index, x in enumerate(self.MULTI_TRIGGER_STATES)
                       if index % 2 == 1]

        trigger_defs[0][SMConsts.SOURCE_STATES] = state_set_1
        trigger_defs[1][SMConsts.SOURCE_STATES] = state_set_2

        assert_is_none(
            ValidateData.validate_multi_trigger_defs(
                list_of_trigger_defs=trigger_defs,
                defined_states=self.MULTI_TRIGGER_STATES
            )
        )

    @raises(BadMultiTriggerDefinition)
    def test_validate_multi_trigger_def_with_invalid_state(self):
        trigger_defs = copy.deepcopy(self.MULTI_TRIGGER_DEFS)
        state_set_1 = [x for index, x in enumerate(self.MULTI_TRIGGER_STATES)
                       if index % 2 == 0]
        state_set_1.append(self.INVALID_TEST_STATE)

        trigger_defs[0][SMConsts.SOURCE_STATES] = state_set_1

        ValidateData.validate_multi_trigger_defs(
            list_of_trigger_defs=trigger_defs,
            defined_states=self.MULTI_TRIGGER_STATES)

    @raises(BadMultiTriggerDefinition)
    def test_validate_multi_trigger_def_with_empty_state_list(self):
        trigger_defs = copy.deepcopy(self.MULTI_TRIGGER_DEFS)
        trigger_defs[0][SMConsts.SOURCE_STATES] = []

        ValidateData.validate_multi_trigger_defs(
            list_of_trigger_defs=trigger_defs,
            defined_states=self.MULTI_TRIGGER_STATES)

    @raises(BadMultiTriggerDefinition)
    def test_validate_multi_trigger_def_without_dest_state_defined(self):
        trigger_defs = copy.deepcopy(self.MULTI_TRIGGER_DEFS)
        del trigger_defs[0][SMConsts.DESTINATION_STATE]

        ValidateData.validate_multi_trigger_defs(
            list_of_trigger_defs=trigger_defs,
            defined_states=self.MULTI_TRIGGER_STATES)

    @raises(BadMultiTriggerDefinition)
    def test_validate_multi_trigger_def_with_unknown_wildcard(self):
        trigger_defs = copy.deepcopy(self.MULTI_TRIGGER_DEFS)
        trigger_defs[0][SMConsts.SOURCE_STATES] = '+'

        ValidateData.validate_multi_trigger_defs(
            list_of_trigger_defs=trigger_defs,
            defined_states=self.MULTI_TRIGGER_STATES)

    @raises(BadMultiTriggerDefinition)
    def test_validate_multi_trigger_def_without_callback_element(self):
        trigger_defs = copy.deepcopy(self.MULTI_TRIGGER_DEFS)
        del trigger_defs[0][SMConsts.CHANGE_STATE_ROUTINE]

        ValidateData.validate_multi_trigger_defs(
            list_of_trigger_defs=trigger_defs,
            defined_states=self.MULTI_TRIGGER_STATES)

    @raises(BadMultiTriggerDefinition)
    def test_validate_multi_trigger_def_without_callback_defined(self):
        trigger_defs = copy.deepcopy(self.MULTI_TRIGGER_DEFS)
        trigger_defs[0][SMConsts.CHANGE_STATE_ROUTINE] = None

        ValidateData.validate_multi_trigger_defs(
            list_of_trigger_defs=trigger_defs,
            defined_states=self.MULTI_TRIGGER_STATES)

    # TODO: Update utility script for creating machine templated to
    #      support multi-source triggers
