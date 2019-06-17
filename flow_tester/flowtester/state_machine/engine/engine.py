import os
import pprint
import typing

import transitions
from transitions.extensions import HierarchicalGraphMachine as Machine

from flowtester.logging import logger
from flowtester.reporting.graph_path import GraphPath
from flowtester.reporting.event_tracking import EventTracker
from flowtester.state_machine.engine.engine_definition import MachineDefinition
from flowtester.state_machine.config.constants \
    import StateMachineConstants as SMConsts
from flowtester.state_machine.engine.input import PathStep


logging = logger.Logger()


class StateMachine:
    """
    This class provides the orchestration around the state machine
    implementation (transitions). The class loads the model into the state
    machine, orchestrates the registration of the necessary callbacks and
    provides basic logging and reporting.
    """

    # Used for delimiting the logging for each state transition
    NUM_STARS_BORDER = 120

    # Used for reporting the traversal path
    NUM_ELEMS_PER_GRAPH_LINE = 4

    def __init__(
            self, data_model: MachineDefinition,
            object_model: typing.Any) -> None:

        # Model definition
        self.data_model = data_model

        # Model metadata
        self.name = self.data_model.get_model_name()
        self.description = self.name

        # Representation of the test product (source of truth)
        self.object_model = object_model

        # Instantiate the state machine
        self.state = None

        self.machine = Machine(
            model=self,
            states=self.data_model.get_list_of_states(),
            initial=self.data_model.get_initial_state(),
            send_event=False,
        )
        self.reporter = EventTracker()

        self.requested_execution_steps = []  # List of PathStep objects
        self.current_step = None             # PathStep object
        self.trigger_list = []               # List of triggers to execute

    @property
    def path(self) -> typing.List[str]:
        """
        Use the result tracker to determine the traversed path

        Returns:
             List of states traversed.

        """
        return [elem[EventTracker.STATE] for elem in self.reporter.events]

    def configure_state_machine(self) -> None:
        """
        Takes the data model and configure the state machine.

        Returns:
             None

        """
        # Register each state
        for state in self.data_model.get_list_of_states():

            # Get a list of triggers available to the current state
            triggers = self.data_model.get_transitions(state)

            if triggers is None:
                continue

            for trigger in triggers:
                transition_routine = trigger[SMConsts.CHANGE_STATE_ROUTINE]

                # Register the trigger with the state
                self.machine.add_transition(
                    trigger=trigger[SMConsts.TRIGGER_NAME],
                    source=state,
                    dest=trigger[SMConsts.DESTINATION_STATE],
                    before='execute_transition_callback',
                    after='validate_current_state')

                logging.debug(f"Adding Trigger: '"
                              f"{trigger[SMConsts.TRIGGER_NAME]}'"
                              f" from '{state}'"
                              f" to '{trigger[SMConsts.DESTINATION_STATE]}'"
                              f" via '{transition_routine}"
                              f"{'' if transition_routine == 'None' else ()}'")

        multi_triggers = self.data_model.validate_multi_triggers(
            self.data_model.get_multi_triggers())

        for trigger in multi_triggers:
            self.machine.add_transition(
                trigger=trigger[SMConsts.TRIGGER_NAME],
                source=trigger[SMConsts.SOURCE_STATES],
                dest=trigger[SMConsts.DESTINATION_STATE],
                before='execute_transition_callback',
                after='validate_current_state')

            transition_routine = trigger[SMConsts.CHANGE_STATE_ROUTINE]
            logging.debug(f"Adding Multi-Trigger: '"
                          f"{trigger[SMConsts.TRIGGER_NAME]}'"
                          f" from: {trigger[SMConsts.SOURCE_STATES]}"
                          f" to '{trigger[SMConsts.DESTINATION_STATE]}'"
                          f" via '{transition_routine}"
                          f"{'' if transition_routine == 'None' else ()}'")

    def _get_callback(self, routine: str) -> typing.Callable:
        """ Get the callable routine reference from the text name.

        Args:
            routine (str): dotted notation reference to desired method.

        Note:
             The routine needs to be available to the state machine, so it
             needs to be either defined in this class or instantiated as part
             of the object model.

        Returns:
            Callable reference to routine.

        Raises:
            AttributeError - If the prescribed callback function is not found.

        """

        # Start with this class
        callback = self

        logging.debug(f"Starting point for building callback: {callback}")

        current_path = 'self'
        # Traverse the dotted path to get to the desired routine
        for attribute in routine.split('.'):
            current_path += f".{attribute}"
            logging.debug(f"Getting attr: {attribute}")
            try:
                callback = getattr(callback, attribute)
            except AttributeError as exc:
                logging.error(f"Unable to find: {current_path}")
                raise exc

            logging.debug(f"Current callback points to: {callback}")

        return callback

    def _border(
            self, topic: str,
            log_level_str: str = 'info') -> None:  # pragma: no cover
        """
        Prints a border around the state transitions.
        Args:
            topic: Message in border
            log_level_str: Level to log...

        Returns:
            None

        """
        star_len = int(self.NUM_STARS_BORDER / 2)
        log = getattr(logging, log_level_str.lower())
        log('')
        log(f"{'*' * star_len} {topic} {'*' * star_len}")

    def execute_transition_callback(self, **kwargs) -> None:
        """
        This the primary transition callback orchestrator. This routine is
        needed so that additional information can be passed into the
        callback routine (external data). If the configured callback routine
        is just called, we do not get a chance to pass data to the routine.

        Returns:
            None

        """
        # Get the configured trigger callback name (str)
        state = self.state
        trigger = self.current_step.trigger
        logging.debug(f"CURRENT STATE INFO: State: {state}"
                      f" Trigger: {trigger}")

        trigger_def = self.data_model.get_transition_info_by_name(
            state, trigger)
        transition_routine = trigger_def[SMConsts.CHANGE_STATE_ROUTINE]

        logging.debug(f"TRIGGER DEFINITION: {pprint.pformat(trigger_def)}")
        logging.debug(f"TRANSITION ROUTINE: {transition_routine}")

        # TODO: Check to see if there is config data for the API. Need
        #       to be sure to get correct state step to get corresponding
        #       data. Also need data reading routines. Be sure to keep with
        #       path data. Do not implement/integrate into this class.

        # Convert the callback name to a callable routine and execute.
        if transition_routine not in [None, 'None']:
            trans_callback = self._get_callback(transition_routine)
            logging.debug(f"TRANS_CALL: {trans_callback}\n\n")
            return trans_callback(**kwargs)

    def validate_current_state(self, **kwargs) -> bool:
        """
        Callback orchestration used to execute the validation callback after
        the state change trigger has executed.

        Note:
            This call is registered with each validation callback:
             - it executes the routine
             - gathers and stores result.

        Returns:
            None

        """
        overall_result = True

        # Get the list of validations associated with the state changes
        validation_definitions = self.data_model.get_state_validation_methods(
            state=self.state)

        # If there are no validations defined, return True because there
        # is no way to validate if state transition was successful.
        if validation_definitions is None:
            return overall_result

        # Iterate through validations, execute and tally results
        for routine_info in validation_definitions:
            if (routine_info in [None, {}] or
                    routine_info[SMConsts.NAME] is None):
                logging.info(f"No state validations defined for: "
                             f"'{self.state}'")
                continue

            # Store the validation routine name
            routine_id = routine_info[SMConsts.NAME]
            routine_name = routine_info[SMConsts.ROUTINE]
            expectation = self.current_step.get_expectation(routine_id)

            self.reporter.add_validation(
                key_name=routine_id, routine_name=routine_name,
                expectation=expectation)

            # Get the routine (callable), execute, and store the result
            validation = self._get_callback(routine_name)
            validation_result = validation(**kwargs)
            self.reporter.add_result(response=validation_result,
                                     result=validation_result == expectation)

            # Tally the overall result
            overall_result = overall_result & validation_result

        # Log the result
        status = "PASSED" if overall_result else "FAILED"
        self._border(f"END STEP - {status}")

        return overall_result

    def _set_execution_description(self, description: str = None) -> None:
        """ Sets the description for the current execution (for logging)

        Args:
            description (str): Basic description; if not, use the model name

        Returns:
            None

        """
        self.description = f"{self.data_model.get_model_name()}"
        if description is not None:
            self.description += f" {description}"
        logging.debug(f"Setting current execution description to: "
                      f"'{self.description}'")

    def execute_state_machine(self, input_data: typing.List[PathStep],
                              description: str = None) -> None:
        """
        Iterate through the provided path (triggers), executing and recording
        the state transitions, validations,

        Args:
            input_data (List[PathData]): List of test step information
            description (str): Description of trigger list

        Returns:

        """

        # Store requested execution information
        self._set_execution_description(description)
        self.requested_execution_steps = input_data
        self.trigger_list = [x.trigger for x in self.requested_execution_steps]
        logging.debug(f"Requested path: {self.trigger_list}")

        # Register initial state
        self.reporter.add_state(self.state)

        # Iterate through the trigger list
        for self.current_step in self.requested_execution_steps:
            trigger = self.current_step.trigger

            self._border(f"START ACTION: '{trigger.upper()}'")
            logging.info(f"Requested Transition: {trigger.upper()}")
            self.reporter.add_transition(
                trigger=trigger, id_=self.current_step.id)

            try:
                api_data = self.current_step.trigger_data or {}
                if str(api_data).lower() == 'none':
                    api_data = {}
                logging.info(f"Trigger Name: {trigger}\n")
                logging.info(f"Trigger Data: {pprint.pformat(api_data)}")

                api = getattr(self, trigger)
                logging.info(f"Trigger API: {pprint.pformat(api)}")

                result = api(**api_data)

            # Illegal transition
            except transitions.MachineError as exc:
                self.reporter.add_transition(
                    trigger=trigger, id_=self.current_step.id)
                self.reporter.add_error(exc.value)
                logging.error(f"ERROR: {exc}")
                logging.error(f"Remaining in '{self.state.upper()}' "
                              f"state.")

            # Something has gone wrong!! Data or Object Issues
            except (AttributeError, TypeError) as exc:
                raise exc

            else:
                logging.info(f"Result of Trigger: {result}")

            self.reporter.add_state(self.state)

        logging.info("Path traversal complete.")

    def traversal_path(self) -> GraphPath:
        """
        Generate ASCII chain of the traversal path

        Returns:
            GraphPath object (if cast to str, prints ascii chain)
        """
        return GraphPath(graph_list=self.path, triggers=self.trigger_list,
                         items_per_line=self.NUM_ELEMS_PER_GRAPH_LINE,
                         add_index=True)

    def execution_summary(self, detailed: bool = False) -> str:
        """
        Generates report of states, triggers, destination state, validation
        routines and thei result.

        Args:
            detailed (bool): Show additional configuration/execution
            information.

        Returns:
            Stringified PrettyTable containing execution results.
        """
        return self.reporter.generate_summary(
            description=self.description, detailed=detailed)

    def generate_image(
            self, path_only=False, filename=None) -> str:
        """
        Builds a PNG representation of the defined state machine.

        Args:
            path_only: Only show the current path (very limited at this point)
            filename: Name of file to create. Defaults to <model_name>.png

        Note:
            See transition documentation about generating a specific path.
            Currently not covered by unit tests due to complexity involved
            in mocking get_graph().draw()

        Returns:
            (str) - Name of generated image file
        """

        title = self.data_model.get_model_name()
        if filename is None:
            filename = f"./{title}.png"
        filename = os.path.abspath(filename)

        logging.info(f"Writing State Machine image to: "
                     f"'{os.path.abspath(filename)}'")

        if path_only:
            self.machine.get_graph(title=title, show_roi=True).draw(
                filename, prog='dot')
        else:
            self.machine.get_graph(title=title).draw(filename, prog='dot')

        return filename
