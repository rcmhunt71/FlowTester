import pprint
import typing

from flowtester.logging.logger import Logger
from flowtester.state_machine.config.constants \
    import StateMachineConstants as SMConsts

logging = Logger()


class BadMultiTriggerDefinition(Exception):
    pass


class ValidateData:
    def __init__(self, model_data):
        self.model_data = model_data

    VALID_MULTISOURCE_WILDCARDS = ['*', '=']

    def validate_all_transitions(self) -> bool:
        """
        Validate all transitions within the model defintion to make sure they
        point to a known, defined state.

        Returns:
            (bool) - True = all transitions point to known/defined state

        """
        result = None

        # Get a list of all defined states
        states = self.model_data.get_list_of_states()
        if not states:
            result = False

        # Get list of all transitions for each state
        for state in states:
            possible_state_changes = self.model_data.get_transitions(state)

            # No transitions, so move to the next state
            if possible_state_changes is None:
                continue

            # Found transitions, check each destination state to known states
            for state_change in possible_state_changes:
                target_state = state_change[SMConsts.DESTINATION_STATE]
                if target_state not in states:
                    logging.error(
                        f"ERROR: {state} has a state change to an undefined "
                        f"state: '{target_state}'")
                    result = False

        logging.info(f"Transition definitions are valid: {result is None}")
        return result is None

    def validate_initial_state(self) -> bool:
        """
        Verifies the initial state is defined and is a valid state based
        on the model definition (exists and has transitions defined).

        Returns: (bool) True: Initial state is defined and is valid.

        """

        # Get list of known/defined states
        states = self.model_data.get_list_of_states()

        # Get the declared initial state
        initial_state = self.model_data.data.get(SMConsts.INITIAL_STATE, None)
        result = None

        # Initial state is unknown
        if initial_state not in states:
            logging.error(f"ERROR: Initial state: {initial_state} not "
                          f"in defined states: {states}")
            result = False

        # Check if state has transitions defined. If an initial state
        # does not have any transitions, the initial state is also the
        # terminal state and is not a state machine.
        if not self.model_data.get_transitions(initial_state):
            logging.error(f"ERROR: Initial state: {initial_state} cannot "
                          f"transition to any downstream paths.")
            result = False

        # Return results
        logging.info(f"Initial state is a valid starting state: "
                     f"{result is None}")
        return result is None

    @classmethod
    def validate_multi_trigger_defs(
            cls, list_of_trigger_defs: typing.List[dict],
            defined_states: typing.List[str]) -> None:
        """
        Validate the specifics of multi-trigger definitions.

        Args:
            list_of_trigger_defs (dict): List of multi-source state
               trigger definitions
            defined_states  (List[str]): List of known/defined states in
               state machine.

        Returns:
            None

        Raises:
            BadMultiTriggerDefinition

        """
        errors = list()

        # For each multi-source-state trigger...
        for trigger in list_of_trigger_defs:

            # Get the required trigger information
            # ------------------------------------
            trigger_name = trigger.get(SMConsts.TRIGGER_NAME, None)
            target_states = trigger.get(SMConsts.SOURCE_STATES, None)
            callback_routine = trigger.get(SMConsts.CHANGE_STATE_ROUTINE, None)
            destination_state = trigger.get(SMConsts.DESTINATION_STATE, None)

            logging.debug(f"'{trigger_name}' Definition:\n"
                          f"{pprint.pformat(trigger)}")
            logging.debug(f"'{trigger_name}': SOURCE STATES: {target_states}")

            # Verify the destination state is defined
            # ---------------------------------------
            if destination_state not in defined_states:
                msg = (f"ERROR: '{trigger_name}' has a destination state that "
                       f"is not recognized: '{destination_state}'.")
                logging.error(msg)
                errors.append(msg)

            else:
                logging.debug(f"'{trigger_name}' has a valid destination "
                              f"state.")

            # Verify the callback routine is specified
            # ----------------------------------------
            if callback_routine is None:
                msg = (f"ERROR: '{trigger_name}' does not have a callback "
                       f"defined to execute state change (YAML field: "
                       f"{callback_routine})")
                logging.error(msg)
                errors.append(msg)

            # Verify all source states are defined
            # ------------------------------------
            if isinstance(target_states, list) and target_states:
                target_states = set(target_states)
                matches = target_states.intersection(set(defined_states))

                logging.debug(f"Target (proposed vs. defined) Intersection:"
                              f" {matches}")

                if matches != target_states:
                    diff = target_states - matches
                    msg = (f"The following multi-trigger states were "
                           f"not defined in the state machine: "
                           f"{', '.join(diff)} for trigger: {trigger_name}")
                    logging.error(msg)
                    errors.append(msg)

            # If target states are not a list of states
            # check for valid wildcards
            # -----------------------------------------
            elif target_states not in cls.VALID_MULTISOURCE_WILDCARDS:
                msg = f"Unrecognized wildcard: '{target_states}'"
                logging.error(msg)
                errors.append(msg)

            # If everything passes and is valid...
            # ------------------------------------
            if not errors:
                logging.info(
                    f"No errors found in the '{trigger_name}' multi-source "
                    f"trigger definition.")

        # D'oh!! Stop here if State Machine is not defined correctly
        # -----------------------------------------------------------
        if errors:
            raise BadMultiTriggerDefinition("\n".join(errors))
