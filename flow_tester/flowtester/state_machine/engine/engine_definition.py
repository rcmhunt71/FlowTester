import copy
import pprint
import typing

import prettytable

from flowtester.logging import logger
from flowtester.state_machine.config.constants \
    import StateMachineConstants as SMConsts
from flowtester.state_machine.validation.validate_engine_cfg import ValidateData

logging = logger.Logger()


class MachineDefinition:
    """

    Using the StateMachineConstants, a well defined state machine should be
    defined (see flowtester.utils.template_builder for additional information
    about the data structure.

    """
    BLANK = ''
    END_STATE = 'END STATE'
    INITIAL_STATE = 'INITIAL STATE'
    NO_VALUE = '--'

    STATE = 'state'
    NOTES = 'notes'
    DESTINATION = 'dest'
    TRIGGER = 'trigger'
    TRIGGER_METHOD = 'trigger_method'
    VALIDATION_ID = 'validation_id'
    VALIDATION_ROUTINE = 'validation_routine'

    def __init__(self, data: dict) -> None:
        self.data = data

    def get_model_name(self) -> str:
        """ Gets the model name as specified in the definition's data
        structure.

        Returns:
            (str) The model name
        """
        return self.data.get(SMConsts.MODEL_NAME)

    def get_initial_state(self) -> str:
        """ Gets the initial state as specified in the definition's data
        structure.

        Returns:
            (str) Name of initial state
        """
        return self.data.get(SMConsts.INITIAL_STATE)

    def get_state_definitions(self) -> typing.List[dict]:
        """ Gets the definitions for ALL defined states.

        Returns:
            List of dictionaries, where each dictionary defines one state.

        """
        data = self.data.get(SMConsts.DEFINITION, {})
        data = [x for x in data if not list(x.keys())[0].startswith(
            SMConsts.NON_STATE_PREFIX)]

        logging.debug(f"STATE DEFINITIONS:\n{pprint.pformat(data)}")
        return data

    def get_state_definition(self, state: str) -> dict:
        """ Gets the definition for the specified state.

        Args:
            state (str): State to retrieve definition

        Returns:
            (dict) - Definition of the specified state

        """
        definition = {}
        if self._is_state_valid(state):
            state_def = [list(s_def.values())[0] for s_def in
                         self.get_state_definitions() if
                         list(s_def.keys())[0] == state]

            logging.debug(f"State Definitions matching {state}:\n"
                          f"{pprint.pformat(state_def)}")

            # There should only be 1 record in the list, but either way,
            # get the first element.
            definition = state_def[0]

        return definition

    def get_list_of_states(self) -> typing.List[str]:
        """ Gets a list defined state names. Do not include states that match
        the nomenclature <_state_>. These are reserved "state directive" names

        Returns:
            (list) - List of defined state names

        """
        state_definitions = self.get_state_definitions()
        states = [list(x.keys())[0] for x in state_definitions]
        states = [x for x in states if
                  not x.startswith(SMConsts.NON_STATE_PREFIX) and
                  not x.endswith(SMConsts.NON_STATE_PREFIX)]
        return states

    def _is_state_valid(self, state: str) -> bool:
        """ Check if specified state is defined in the model.

        Args:
            state (str): Name of state to validate

        Returns:
            (bool) - State is defined (True) or undefined (False)

        """
        result = state in self.get_list_of_states()
        if not result:
            logging.error(f"Unrecognized state '{state}'. "
                          f"Possible states: {self.get_list_of_states()}")
        return result

    def get_state_validation_methods(self, state: str) \
            -> typing.List[typing.Dict[str, str]]:
        """ Get the validation definitions for the specified state

        Args:
            state (str): State to get validations

        Returns:
            List of Dicts: Each element is a dictionary
              name: identifier of validation
              routine: name of routine to perform validation

        """
        state_def = self.get_state_definition(state=state)
        return state_def.get(SMConsts.VALIDATIONS, list())

    def get_transitions(self, state: str) -> typing.List[dict]:
        """ Get a list of the transitions for the specified state

        Args:
            state (str): The state to retrieve the designated transitions

        Returns:
            List of transition definitions (dictionary)

        """
        transition_list = []

        logging.debug(f"Finding state data for '{state}'")
        for state_definition_dict in self.get_state_definitions():

            # Get the name and definition of the current state
            state_name = list(state_definition_dict.keys())[0]
            list_state_definitions = list(state_definition_dict.values())

            # If the state does not match, continue scanning...
            if state != state_name:
                continue

            # If you are here, you found the correct state.
            # Iterate through the state and the transition definitions
            for state_def_dict in list_state_definitions:
                logging.debug(f"'{state_name}' --> State definition dictionary:"
                              f"\n{pprint.pformat(state_def_dict)}\n")

                transition_list = state_def_dict.get(SMConsts.TRANSITIONS)
                logging.debug(f"'{state_name}' --> Transitions:\n"
                              f"{pprint.pformat(transition_list)}\n")

        return transition_list

    def get_all_triggers(self) -> typing.List[str]:
        """ Get a list of all the defined triggers (across all states)

        Returns:
            List of all triggers (assumes every trigger is uniquely named)

        """
        triggers = []

        # Iterate through tall states
        for state_definition_dict in self.get_state_definitions():

            state_name = list(state_definition_dict.keys())[0]
            transition_list = self.get_transitions(state_name)

            # If there are transitions, get the names of the triggers
            if transition_list is not None:
                for trans in transition_list:
                    state_trigger = trans[SMConsts.TRIGGER_NAME]
                    logging.debug(f"'{state_name}' - Triggers:\n"
                                  f"{state_trigger}\n")

                    triggers.append(state_trigger)

        # Get all of the multi-trigger definitions (trigger names)
        multi_triggers = []
        for trigger in self.get_multi_triggers():
            logging.debug(f"CURRENT MULTI_TRIGGER_DEF: {trigger}")
            multi_triggers.append(trigger.get(SMConsts.TRIGGER_NAME, None))

        logging.debug(f"MULTI_TRIGGERS: {multi_triggers}")
        triggers.extend(multi_triggers)

        # Return a list of all unique trigger names
        return list(set(triggers))

    def get_multi_triggers(self) -> typing.List[dict]:
        """
        Get the multi-trigger definitions

        Returns:
            List of multi-trigger definitions
        """
        multi_trigger_name = (f"{SMConsts.NON_STATE_PREFIX}"
                              f"{SMConsts.MULTI_TRIGGERS}"
                              f"{SMConsts.NON_STATE_PREFIX}")

        multi_trigger_defs = [
            v for elem in self.data.get(SMConsts.DEFINITION) for k, v
            in elem.items() if k == multi_trigger_name]

        # Multi_trigger_defs, if defined, are a single element list with the
        # trigger data list stored at [0]. If multi-trigger data is found,
        # get the [0]th element.
        if multi_trigger_defs:
            multi_trigger_defs = multi_trigger_defs[0]
        return multi_trigger_defs

    def validate_multi_triggers(
            self, multi_trigger_defs: typing.List[dict]) -> typing.List[dict]:
        """
        Validates all multi-source trigger definitions.
        Args:
            multi_trigger_defs (list of dicts): definitions of each
            multi-source trigger

        Returns:
            None

        Raises:
            ValidateData will raise various exceptions based on the error

        """
        logging.debug(f"MULTI_TRIGGER_DATA:\n"
                      f"{pprint.pformat(multi_trigger_defs)}")

        ValidateData(self.data).validate_multi_trigger_defs(
            list_of_trigger_defs=multi_trigger_defs,
            defined_states=self.get_list_of_states())

        return multi_trigger_defs

    def describe_model(self):
        """ Create a table displaying all defined state changes, triggers, and
        validations

        Returns:
            (str) Table of all defined state changes, triggers, and validations

        """
        # Column Headers
        col_dict = {
            self.STATE: 'Origin State',
            self.TRIGGER: 'Trigger',
            self.DESTINATION: 'Expected State',
            self.TRIGGER_METHOD: 'Trigger Method',
            self.VALIDATION_ID: 'Validation ID',
            self.VALIDATION_ROUTINE: 'Validation Routine',
            self.NOTES: 'Notes'
        }
        headers = list(col_dict.values())

        # Define the table
        table = prettytable.PrettyTable()
        table.field_names = headers
        table.align[col_dict[self.VALIDATION_ROUTINE]] = 'l'
        description = f"\nModel Description: {self.get_model_name()}"

        # Iterate through the states, gleaning the info
        table = self._build_model_table_contents(
            table_obj=table, col_dict=col_dict,
            states=self.get_list_of_states())

        for idx, source in enumerate(self.get_multi_triggers()):
            source_copy = copy.deepcopy(source)

            if not isinstance(source[SMConsts.SOURCE_STATES], list):
                source_copy[self.STATE] = source[SMConsts.SOURCE_STATES]

            table = self._add_trigger_to_table(
                table_obj=table, col_dict=col_dict,
                trigger=source_copy)

        rendered_table = f"\n{description}\n{table.get_string()}\n"
        logging.info(rendered_table)
        return rendered_table

    def _add_trigger_to_table(
            self, table_obj: prettytable.PrettyTable,
            col_dict: typing.Dict[str, str],
            trigger: dict) -> prettytable.PrettyTable:
        """
        Add multi-source trigger definitions to the table

        Args:
            table_obj (prettytable.PrettyTable): Table to add data
            col_dict (dict): Column keys and corresponding headers
            trigger (dict): Single multi-source trigger definition

        Returns:
            (prettytable.PrettyTable) Populated table object

        """
        logging.debug(f"TRIGGER:\n{trigger}")

        headers = list(col_dict.values())
        validation_blank_row = {col: self.BLANK for col in headers}

        # No data provided, so just return the table
        if trigger is None:
            return table_obj

        states = trigger.get(SMConsts.SOURCE_STATES, {})

        # If source state is a wildcard, put it into a list for ease
        # of implementation within a consistent routine
        if not isinstance(states, list):
            states = list(states)

        for state in states:

            # Aggregate data
            # --------------
            column_data = {
                self.STATE: state,
                self.DESTINATION: trigger[SMConsts.DESTINATION_STATE],
                self.TRIGGER_METHOD: trigger[SMConsts.CHANGE_STATE_ROUTINE],
                self.TRIGGER: trigger[SMConsts.TRIGGER_NAME],
                self.NOTES: '',
            }
            destination = column_data[self.DESTINATION]

            # Build data row based on current transition data
            # ------------------------------------------------
            data_dict = {col: self.NO_VALUE for col in headers}
            for data_element, data_value in column_data.items():
                data_dict[col_dict[data_element]] = data_value

            # Add registered transitions for destination state
            # ------------------------------------------------
            transition_list = self.get_transitions(destination)
            logging.debug(
                f"{destination} TRANSITIONS: {pprint.pformat(transition_list)}")
            if not transition_list:
                data_dict[col_dict[self.NOTES]] = self.END_STATE

            # Add registered validations for destination state
            # ------------------------------------------------
            validations = self.get_state_validation_methods(destination)
            logging.debug(
                f"{destination} VALIDATIONS: {pprint.pformat(validations)}")

            # If there are validations, add them to the table. The first one
            # can go on same line, remaining are added to rows below, but only
            # with validation data (does not duplicate all information).
            # -----------------------------------------------------------------
            if validations:
                for idx, v in enumerate(validations):
                    data_dict[col_dict[self.VALIDATION_ID]] = v[SMConsts.NAME]
                    data_dict[col_dict[self.VALIDATION_ROUTINE]] = \
                        v[SMConsts.ROUTINE]

                    if idx > 0:
                        zero = [self.NOTES, self.STATE, self.TRIGGER,
                                self.TRIGGER_METHOD, self.DESTINATION]
                        for elem in zero:
                            data_dict[col_dict[elem]] = self.BLANK

                    table_obj.add_row([data_dict[col] for col in headers])

            else:
                table_obj.add_row([data_dict[col] for col in headers])

            # Add data to table and 1 separation (blank) row
            table_obj.add_row([validation_blank_row[col] for col in headers])

        return table_obj

    def _build_model_table_contents(
            self, table_obj: prettytable.PrettyTable,
            col_dict: typing.Dict[str, str],
            states: typing.List[str]) -> prettytable.PrettyTable:

        """
        Add primary state configuration information to table.

        Args:
            table_obj (prettytable.PrettyTable): Table to populate
            col_dict (dict): Column keys and corresponding headers
            states (list[str]): State definitions to add to the table

        Returns:
            (prettyTable) - Updated table object

        """

        headers = list(col_dict.values())

        # Special values for specific entries
        validation_blank_row = {col: self.BLANK for col in headers}

        for source_state in states:
            data_dict = {col: self.NO_VALUE for col in headers}
            data_dict[col_dict[self.STATE]] = source_state

            # This state is the initial state (entry point into the machine)
            if source_state == self.get_initial_state():
                data_dict[col_dict[self.NOTES]] = self.INITIAL_STATE

            # Get validation and transition definitions for the current state
            validations = self.get_state_validation_methods(source_state)
            transition_list = self.get_transitions(source_state)

            # If there are no transitions, this is a TERMINAL state.
            # Process and go to the next state.
            if transition_list is None:
                data_dict[col_dict[self.NOTES]] = self.END_STATE

                # Only add validations if defined
                if validations:
                    v = validations[0]
                    data_dict[col_dict[self.VALIDATION_ID]] = v[SMConsts.NAME]
                    data_dict[col_dict[self.VALIDATION_ROUTINE]] = \
                        v[SMConsts.ROUTINE]

                    if transition_list is None:
                        data_dict[col_dict[self.NOTES]] = self.END_STATE

                table_obj.add_row([data_dict[col] for col in headers])

                # Create a "blank row" and only add other validation methods for
                # the current state.
                if validations and len(validations) > 1:
                    for v in validations[1:]:

                        validation_blank_row[col_dict[self.VALIDATION_ID]] = \
                            v[SMConsts.NAME]
                        validation_blank_row[
                            col_dict[self.VALIDATION_ROUTINE]] = \
                            v[SMConsts.ROUTINE]

                        table_obj.add_row([validation_blank_row[col] for col
                                           in headers])

                # Put blank spacer row after last validation
                validation_blank_row[col_dict[self.VALIDATION_ID]] = self.BLANK
                validation_blank_row[col_dict[self.VALIDATION_ROUTINE]] = \
                    self.BLANK
                table_obj.add_row(
                    [validation_blank_row[col] for col in headers])

                continue

            # For all transitional states (can progress to other states)
            for state_change in transition_list:

                # Get the trigger name, dest state, and trigger. Stored in a
                # dictionary, so table column order is set by a list and the
                # dictionary automatically adjusts (order is not important).
                data_dict[col_dict[self.TRIGGER]], \
                    data_dict[col_dict[self.DESTINATION]], \
                    data_dict[col_dict[self.TRIGGER_METHOD]] \
                    = self.get_transition_info(state_change)

                validations = self.get_state_validation_methods(
                    state=data_dict[col_dict[self.DESTINATION]])

                # Only add validations if defined
                if validations:
                    v = validations[0]
                    data_dict[col_dict[self.VALIDATION_ID]] = v[SMConsts.NAME]
                    data_dict[col_dict[self.VALIDATION_ROUTINE]] = \
                        v[SMConsts.ROUTINE]

                row_data = [data_dict[col] for col in headers]
                table_obj.add_row(row_data)

                # Add a blank row and only list other state validation methods
                if validations and len(validations) > 1:
                    for v in validations[1:]:

                        validation_blank_row[col_dict[self.VALIDATION_ID]] = \
                            v[SMConsts.NAME]
                        validation_blank_row[
                            col_dict[self.VALIDATION_ROUTINE]] = \
                            v[SMConsts.ROUTINE]
                        table_obj.add_row([validation_blank_row[col] for
                                           col in headers])

                # Put blank spacer row after last validation
                validation_blank_row[col_dict[self.VALIDATION_ID]] = self.BLANK
                validation_blank_row[col_dict[self.VALIDATION_ROUTINE]] = \
                    self.BLANK
                table_obj.add_row(
                    [validation_blank_row[col] for col in headers])

        return table_obj

    @staticmethod
    def get_transition_info(trigger_dict: typing.Dict[str, dict]):
        """ Get information from the trigger data structure provided

        Args:
            trigger_dict: Dictionary defining a transition

        Returns:
            Tuple of trigger name, destination state, and trigger methods

        """
        error_msg = 'Not Found'
        trigger_name = trigger_dict.get(SMConsts.TRIGGER_NAME, error_msg)
        destination = trigger_dict.get(SMConsts.DESTINATION_STATE, error_msg)
        method = trigger_dict.get(SMConsts.CHANGE_STATE_ROUTINE, error_msg)
        return trigger_name, destination, method

    def get_transition_info_by_name(
            self, state_name: str, trigger_name: str) -> dict:
        """
        Retrieve the dictionary definition for the state:trigger

        Args:
            state_name (str): Name of State
            trigger_name (str): Name of Trigger

        Returns:
            Dictionary definition of the state:trigger

        """
        error_msg = 'Not Found'
        transitions = self.get_transitions(state=state_name)
        for trans_def in transitions:
            if trans_def[SMConsts.TRIGGER_NAME] == trigger_name:
                return trans_def

        possible_triggers = [tr.get(SMConsts.TRIGGER_NAME, error_msg) for tr
                             in transitions]
        logging.warning(f"The trigger ('{trigger_name} was not found in for "
                        f"the state '{state_name}.")
        logging.warning(f"Defined triggers: {possible_triggers}")
        return {}

    def validate_path(self, path: typing.List[str]) -> bool:
        """ Check if path if valid based on state machine triggers

        Args:
            path: list of triggers to try to execute

        Note:
            This routine will not execute the path, it only verifies all
            requested triggers exist in the state machine model.)

        Returns:
            (bool) Valid Path = True, Invalid Path = False

        """
        triggers = self.get_all_triggers()
        diff = set(path) - set(triggers)
        for trigger in diff:
            logging.error(f"Requested path ({path}) has unrecognized "
                          f"step/trigger: '{trigger}'")
        return len(diff) == 0
