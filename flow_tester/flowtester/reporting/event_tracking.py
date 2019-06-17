
import pprint

import prettytable

from flowtester.logging.logger import Logger

logging = Logger()


class EventTracker:
    """
    The purpose of this class is to provide a mechanism for recording the
    progression of the state machine based on the API called.

    There is a hierarchy to the class call structure, where subsequent calls
    are valid or invalid based on current call stack and state.

    PRIMARY CALL: EventTracker.add_state()
    Registers the current state. All API operations invoked will record
    against this (current) state, until another add_state() call is made,
    at which point that state becomes the "current" state.

    SECONDARY CALL: EventTracker.add_transition
    Stores the name of transition/trigger executed against the current state.
    If API is called again for the current state, it will overwrite the
    existing transition and validation data.

    TERTIARY CALLS:
    + EventTracker.add_validation
       Registers a validation routine to be executed against the system to
       verify current conditions are/not met. Result can also be provided at
       time of call.

    + EventTracker.add_result
       Add result to latest validation to be registered for current state.

    + EventTracker.add_error
       If error or exception is caught, can be stored. Kept at state level of
       heirarchy.


    DATA_STRUCTURE
    [ <list of state_definitions> ]

    State Definition:
    {
      state: <state_name>
      transition: <transition_name>
      errors: [<error_msg>, <error_msg>]
      validations:
        [
          {name: <name_of_validation_1>,
           result: <result>},

          {name: <name_of_validation_2>,
           result: <result>},

           ...
        ]
    }

    """

    # Definition Dictionary Keywords
    ACTUAL = 'actual'
    ERRORS = 'errors'
    EXPECTATION = 'expectation'
    TRANSITION_ID = 'id'
    NAME = 'name'
    KEY = 'key'
    RESULT = 'result'
    ROUTINE = 'routine'
    STATE = 'state'
    TRANSITION = 'transition'
    VALIDATIONS = 'validations'

    # Result Strings
    PASS = 'Pass'
    FAIL = 'FAIL'

    def __init__(self):
        self.events = list()

    def add_state(self, state: str) -> None:
        """
        Add new state to event tracker. This is the primary call to store all
        subsequent data.

        Args:
            state (str): Name of state.

        Returns:
            None

        """
        data = {self.STATE: state,
                self.TRANSITION: '',
                self.TRANSITION_ID: '',
                self.VALIDATIONS: [],
                self.ERRORS: []}

        self.events.append(data)

    def add_transition(self, trigger: str, id_: str) -> None:
        """ Adds the trigger used to progress from current state.

        Args:
            trigger (str): Name or API of trigger
            id_ (str): The unique id associated with the path step.

        Returns:
            None

        """
        # If there is at least one event in the list,  select the most recent
        if self.events:
            current_state_data = self.events[-1]
            current_state_data[self.TRANSITION] = trigger
            current_state_data[self.TRANSITION_ID] = id_
            current_state_data[self.VALIDATIONS] = []

        # No state registered.
        else:
            logging.error(f"Cannot add transition '{trigger}'. "
                          f"Not tracking current state.")

    def add_validation(self,
                       key_name: str, routine_name: str,
                       expectation: bool = True,
                       actual: bool = None,
                       result: bool = None) -> None:
        """ Registers a validation with the current transition (can add
        multiple validations)

        Args:
            key_name (str): Identifier for validation routine
            routine_name (str): Name of validation routine executed
            expectation (bool): Validation routine should return True or False
            actual (bool): Actual response from validation routine --> Optional
            result (bool): Result of validation --> OPTIONAL

        Returns:
            None

        """
        # Basic validation data structure
        validation_info = {self.KEY: key_name,
                           self.NAME: routine_name,
                           self.EXPECTATION: expectation,
                           self.ACTUAL: actual,
                           self.RESULT: result}

        # If there is at least one event in the list,  select the most recent
        if self.events:
            current_state_data = self.events[-1]
            current_state_data[self.VALIDATIONS].append(validation_info)

        # No state registered.
        else:
            logging.error(f"Cannot add validation info for "
                          f"'{routine_name}'. Not tracking current state.")

    def add_error(self, error: str):
        """ Add any error associated with transition that was caught

        Args:
            error (str): Error msg

        Returns:
            None

        """
        # If there is at least one event in the list,  select the most recent
        if self.events:
            current_state_data = self.events[-1]
            current_state_data[self.ERRORS].append(error)

        # No state registered.
        else:
            logging.error(f"Cannot add error info '{error}'. "
                          f"Not tracking current state.")

    def add_result(self, response: bool, result: bool):
        """ Add a result for the current validation routine

        Args:
            response (bool): Actual response from validation routine
            result (bool): Result of the validation routine

        Returns:
            None

        """
        if self.events:
            current_state = self.events[-1]
            if current_state[self.VALIDATIONS]:
                current_validation = current_state[self.VALIDATIONS][-1]
                current_validation[self.RESULT] = result
                current_validation[self.ACTUAL] = response
            else:
                logging.error(f"Cannot add result. Not validations registered.")

        # No state registered.
        else:
            logging.error(f"Cannot add result. Not tracking current state.")

    def generate_summary(
            self, description: str = None,
            detailed: bool = False) -> str:

        """ Builds an ASCII table representation of the data in self.events.

        Args:
            description (str): Description of the data in the table.
            detailed (bool): If True, show additional info in the table
                (e.g. - validation ids)

        Returns:
            (str) ASCII representation of table (PrettyTable table)
        """

        # Column Headers
        index = 'Index'
        state = 'State'

        transition = 'Transition'
        transition_id = 'Trans ID'
        v_name = 'Validation ID'
        v_routine = 'Validation Routine'
        expectation = 'Expectation'
        actual = 'Response'
        result = 'Result'
        errors = 'Errors'
        blank = '--'

        # List of Columns (in display order)
        table_cols = [index, state, transition, v_routine, v_name,
                      expectation, actual, result, errors]

        # If detailed, include the transition ID; always put it after
        # the transition name.
        if detailed:
            col_index = table_cols.index(transition)
            table_cols.insert(col_index + 1, transition_id)

        # Set the title
        title = "Execution Summary"
        if description is not None:
            title += f" for {description}"

        # Log the data
        logging.debug(f"\n{pprint.pformat(self.events)}")

        # Build the table
        table = prettytable.PrettyTable()
        table.field_names = table_cols
        table.align[index] = "r"

        # Iterate through states and add the data to the table
        for state_num, state_info in enumerate(self.events):

            # Basic structure for each state entry
            data_dict = {index: state_num + 1,
                         state: state_info[self.STATE],
                         transition: state_info[self.TRANSITION],
                         errors: "\n".join(state_info[self.ERRORS]),
                         v_name: blank,
                         v_routine: blank,
                         expectation: blank,
                         actual: blank,
                         result: blank}

            if detailed:
                data_dict[transition_id] = state_info[self.TRANSITION_ID]

            logging.debug(f"\nSTATE INFO:\n{pprint.pformat(state_info)}")
            logging.debug(f"SUMMARY DICT:\n{pprint.pformat(data_dict)}")

            # Check if there are validations and if so, there can be multiple.
            # The first validation can be listed in the same row as the state
            # info subsequent rows should be blank so that the parent data is
            # not repeated, but it is clear this data is part of the parent
            # data.

            if state_info[self.VALIDATIONS]:
                num_validations = len(state_info[self.VALIDATIONS])
                logging.debug(f"VALIDATIONS FOUND: {num_validations} "
                              f"for {state_info[self.STATE]}")

                # Iterate through validation data
                for idx in range(num_validations):
                    logging.debug(f"Processing index: {idx}")

                    # Create a blank line for all subsequent validation
                    # results
                    if idx > 0:
                        data_dict = {
                            index: '', state: '',
                            transition: '', errors: ''}

                        if detailed:
                            data_dict[transition_id] = ''

                    # Populate table row
                    v_info = state_info[self.VALIDATIONS][idx]
                    data_dict[v_name] = v_info[self.KEY]
                    data_dict[v_routine] = v_info[self.NAME]
                    data_dict[expectation] = v_info[self.EXPECTATION]
                    data_dict[actual] = v_info[self.ACTUAL]

                    # Determine result (True/False = Pass/Fail)
                    data_dict[result] = (self.PASS if v_info[self.RESULT]
                                         else self.FAIL)

                    table.add_row([data_dict[col] for col in table_cols])

            # No validations so just add the row.
            else:
                table.add_row([data_dict[col] for col in table_cols])

        return f"{title}\n{table.get_string()}\n"
