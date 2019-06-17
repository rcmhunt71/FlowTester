from random import choice
from typing import List, NoReturn
from uuid import uuid4

from flowtester.logging.logger import Logger
from flowtester.state_machine.engine.input import PathStep

from nose.tools import assert_equals, assert_true


logging = Logger()


class TestPathStep:

    TRIGGER_NAME = 'TEST'

    def test__str__does_not_crash(self):
        test_id = str(uuid4())
        validation_ids = ['test']
        expectations = [False]

        step = PathStep(trigger=self.TRIGGER_NAME)
        step.add_id(step_id=test_id)
        self._add_and_validate_expectations(
            validation_ids=validation_ids, expectations=expectations)

        assert_true(isinstance(str(step), str))

    def test_add_id(self):

        # Verify ID is added to PathStep correctly

        test_id = str(uuid4())
        step = PathStep(trigger=self.TRIGGER_NAME)
        step.add_id(step_id=test_id)

        assert_equals(step.id, test_id)

    def test_add_data(self):

        # Verify data is added to PathStep correctly

        test_data = str(uuid4())
        step = PathStep(trigger=self.TRIGGER_NAME)
        step.add_data(data=test_data)

        assert_equals(step.trigger_data, test_data)

    def test_add_single_expectation(self):

        # Verify expectation is added to PathStep correctly

        validation_ids = ['test']
        expectations = [False]
        self._add_and_validate_expectations(
            validation_ids=validation_ids, expectations=expectations)

    def test_add_multiple_expectations(self):

        # Verify expectations (plural) are added to PathStep correctly

        validation_ids = ['test_1', 'test_2', 'test_3']
        expectations = [False, True, False]
        self._add_and_validate_expectations(
            validation_ids=validation_ids, expectations=expectations)

    def _add_and_validate_expectations(
            self, validation_ids: List[str],
            expectations: List[bool]) -> NoReturn:

        # Add requested expectations
        step = PathStep(trigger=self.TRIGGER_NAME)
        for id_, expect in zip(validation_ids, expectations):
            step.add_expectation(
                validation_id=id_, expectation=expect)

        # Verify the expectations were added correctly (format and value)
        assert_equals(len(step.expectations), len(validation_ids))
        for index in range(len(validation_ids)):
            assert_equals(
                step.expectations[index][PathStep.ID],
                validation_ids[index])
            assert_equals(
                step.expectations[index][PathStep.EXPECTATION],
                expectations[index])

    def test_get_expectations(self):

        # Verify requested expectation value is returned

        validation_ids = ['test_1', 'test_2']
        expectations = [False, True]
        target_index = choice(range(len(expectations)))

        logging.info(f"Selecting expectation element: {target_index}")

        # Add expectations
        step = PathStep(trigger=self.TRIGGER_NAME)
        for id_, expect in zip(validation_ids, expectations):
            step.add_expectation(
                validation_id=id_, expectation=expect)

        # Get randomly selected expectation (selected from expectations added)
        expectation = step.get_expectation(validation_ids[target_index])

        # Verify return value matches the expectation
        assert_equals(expectation, expectations[target_index])
