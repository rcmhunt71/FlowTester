from uuid import uuid4

from nose.tools import assert_equals, assert_true

from flowtester.logging.logger import Logger
from flowtester.reporting.event_tracking import EventTracker


logging = Logger()


class TestEventTracker:

    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    BLANK = ''

    EVENTS = [CREATE, UPDATE, DELETE]

    TRANSITION_NAME = 'trigger'
    TRANSITION_ID = str(uuid4())
    VALIDATION_NAME = 'valid_1'
    VALIDATION_ROUTINE = 'this.is.a.test.routine'
    VALIDATION_EXPECTATION = False

    ERROR_MSG = 'This is an error.'

    def _instantiate_and_add_multiple_states(self) -> EventTracker:
        """
        Instantiates and populates an event tracker with multiple states.

        Returns:
            A populated multi-state EventTracker object
        """

        tracker = EventTracker()
        for state in self.EVENTS:
            tracker.add_state(state=state)
        return tracker

    def _validation_multi_state_tracker(self, tracker: EventTracker) -> None:
        """
        Validates a multi-state tracker, based on tracker built by
        self._instantiate_and_add_multiple_states()

        Args:
            tracker: Instantiated EventTracker object

        Returns:
            None

        """
        assert_equals(len(tracker.events), len(self.EVENTS))
        assert_true(isinstance(tracker.events[-1], dict))
        assert_equals(tracker.events[-1][EventTracker.STATE], self.EVENTS[-1])

    def _test_validation_info(self, name: str, routine: str, val_exp: bool,
                              actual: bool, result: bool) -> None:
        """
        Builds a TrackerEvent object based on parameters, add validation info
        and verifies object was updated correctly.

        Args:
            name (str): Name of validation
            routine (str): Name of validation routine
            val_exp (bool): Expected value
            actual (bool): Actual value
            result (bool): Does val_exp match actual value

        Returns:
            None
        """
        tracker = self._instantiate_and_add_multiple_states()
        self._validation_multi_state_tracker(tracker)
        tracker.add_validation(
            key_name=name, routine_name=routine,
            expectation=val_exp, actual=actual, result=result)

    @staticmethod
    def _validate_validations(
            event: dict, name: str, routine: str, expectation: bool,
            actual: bool, result: bool):
        """
        Validate a given validation dictionary (member from a state)

        Args:
            event (dict): State dictionary as defined in event_tracking.py
            name (str): Name of validation
            routine (str): Name of validation routine
            expectation (bool): Expected value
            actual (bool): Actual value
            result (bool): Does val_exp match actual value

        Returns:
            None
        """

        if expectation is None:
            expectation = True

        assert_equals(
            event[EventTracker.VALIDATIONS][0][EventTracker.KEY], name)
        assert_equals(
            event[EventTracker.VALIDATIONS][0][EventTracker.NAME], routine)

        assert_equals(
            event[EventTracker.VALIDATIONS][0][EventTracker.EXPECTATION],
            expectation)
        assert_equals(
            event[EventTracker.VALIDATIONS][0][EventTracker.ACTUAL], actual)
        assert_equals(
            event[EventTracker.VALIDATIONS][0][EventTracker.RESULT], result)

    def test_add_state(self):
        state = self.CREATE
        tracker = EventTracker()
        tracker.add_state(state=state)

        assert_equals(len(tracker.events), 1)
        assert_true(isinstance(tracker.events[0], dict))
        assert_equals(tracker.events[0][EventTracker.STATE], state)

    def test_add_transition_to_last_element(self):
        tracker = self._instantiate_and_add_multiple_states()
        tracker.add_transition(
            trigger=self.TRANSITION_NAME, id_=self.TRANSITION_ID)

        self._validation_multi_state_tracker(tracker)

        # Check all events have been updated correctly. Only the last
        # state should have any transition info
        target_index = len(tracker.events) - 1
        for index, event in enumerate(tracker.events):

            exp_trans = self.BLANK
            exp_trans_id = self.BLANK

            if index == target_index:
                exp_trans = self.TRANSITION_NAME
                exp_trans_id = self.TRANSITION_ID

            assert_equals(
                event[EventTracker.TRANSITION], exp_trans)
            assert_equals(
                event[EventTracker.TRANSITION_ID], exp_trans_id)

    def test_add_transition_without_defined_state(self):
        tracker = EventTracker()
        tracker.add_transition(
            trigger=self.TRANSITION_NAME, id_=self.TRANSITION_ID)
        assert_equals(len(tracker.events), 0)

    def test_add_validation_required_parameters(self):
        self._test_validation_info(
            name=self.VALIDATION_NAME,
            routine=self.VALIDATION_ROUTINE,
            val_exp=None,
            actual=None,
            result=None)

    def test_add_validation_expectation_parameter(self):
        self._test_validation_info(
            name=self.VALIDATION_NAME,
            routine=self.VALIDATION_ROUTINE,
            val_exp=False,
            actual=None,
            result=None)

    def test_add_validation_results(self):
        self._test_validation_info(
            name=self.VALIDATION_NAME,
            routine=self.VALIDATION_ROUTINE,
            val_exp=False,
            actual=True,
            result=False)

    def test_add_validation_without_defined_state(self):
        tracker = EventTracker()
        tracker.add_validation(
            key_name=self.VALIDATION_NAME,
            routine_name=self.VALIDATION_ROUTINE)
        assert_equals(len(tracker.events), 0)

    def test_add_error_without_defined_state(self):
        tracker = EventTracker()
        tracker.add_error(error=self.ERROR_MSG)
        assert_equals(len(tracker.events), 0)

    def test_add_error(self):
        tracker = self._instantiate_and_add_multiple_states()
        error_msg_2 = "OOPS! ERROR"

        tracker.add_error(error=self.ERROR_MSG)
        tracker.add_error(error=error_msg_2)
        assert_equals(len(tracker.events[-1][EventTracker.ERRORS]), 2)
        assert_equals(
            tracker.events[-1][EventTracker.ERRORS][0], self.ERROR_MSG)
        assert_equals(
            tracker.events[-1][EventTracker.ERRORS][-1], error_msg_2)

    def test_add_results_with_defined_validation(self):
        response = False
        result = True

        tracker = self._instantiate_and_add_multiple_states()
        tracker.add_validation(
            key_name=self.VALIDATION_NAME,
            routine_name=self.VALIDATION_ROUTINE)

        tracker.add_result(response, result)
        validations = tracker.events[-1][EventTracker.VALIDATIONS][0]
        assert_equals(validations[EventTracker.KEY], self.VALIDATION_NAME)
        assert_equals(validations[EventTracker.NAME], self.VALIDATION_ROUTINE)
        assert_equals(validations[EventTracker.ACTUAL], response)
        assert_equals(validations[EventTracker.RESULT], result)

    def test_add_results_without_defined_validation(self):
        response = False
        result = True

        tracker = self._instantiate_and_add_multiple_states()
        tracker.add_result(response, result)

        validations = tracker.events[-1][EventTracker.VALIDATIONS]
        assert_equals(validations, [])

    def test_add_results_without_defined_state(self):
        response = False
        result = True

        tracker = EventTracker()
        tracker.add_result(response, result)
        assert_equals(len(tracker.events), 0)

    def test_generate_summary_without_detail_and_descript_does_not_error(self):
        self._test_summary()

    def test_generate_summary_with_description(self):
        self._test_summary(description='test me')

    def test_generate_summary_with_detail_does_not_error(self):
        self._test_summary(detailed=True)

    def test_generate_summary_with_detail_and_descript_does_not_error(self):
        self._test_summary(detailed=True, description='test_me')

    def _test_summary(self, description=None, detailed=False):
        tracker = self._instantiate_and_add_multiple_states()
        tracker.add_validation(key_name='test_1', routine_name='this.is.a.test',
                               expectation=True)
        tracker.add_validation(key_name='test_2', routine_name='this.is.a.test',
                               expectation=False)
        tracker.add_result(False, True)
        tracker.generate_summary(detailed=detailed, description=description)
