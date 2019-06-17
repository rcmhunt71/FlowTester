from typing import List
from uuid import uuid4

from nose.tools import assert_true, assert_false

from flowtester.logging.logger import Logger
from flowtester.state_machine.engine.input import PathStep
from flowtester.state_machine.paths.validation import ValidatePaths


logging = Logger()


class TestValidatePaths:
    TRIGGER_NAME = 'test_step'
    TRIGGER_ID = str(uuid4())
    EXPECTATIONS = {'test_1': True, 'test_2': False}
    STEP_DATA = {'param1': 'param1_value', 'param2': 'param2_value'}

    def _define_path_step(
            self, trigger_name: str = None,
            trigger_id: str = None) -> PathStep:

        """
        Builds a simple path step with a name, id, expectations,
        and data

        Args:
            trigger_name (str): Name of trigger/step
            trigger_id (str): Unique id for trigger/step

        Returns:
            Instantiated and populated PathStep object
        """

        trigger_name = trigger_name or self.TRIGGER_NAME
        trigger_id = trigger_id or self.TRIGGER_ID

        step = PathStep(trigger=trigger_name, trigger_id=trigger_id)
        step.add_data(self.STEP_DATA)
        for validation_id, expectation in self.EXPECTATIONS.items():
            step.add_expectation(validation_id, expectation)
        return step

    def _define_path_steps(self, num_steps: int) -> List[PathStep]:
        """
        Builds a list of populated PathSteps, all with unique names and ids.

        Args:
            num_steps (int): Number of steps to build and put into list.

        Returns:
            List of unique PathSteps

        """
        return [self._define_path_step(
            trigger_name=f'trigger_{x}',
            trigger_id=str(uuid4())) for x in range(num_steps)]

    def test_validate_step_id_is_none(self):
        test_step = self._define_path_step()
        test_step.id = None
        logging.info(test_step)
        assert_false(
            ValidatePaths.validate_step(test_step),
            f'StepPath.id is {test_step.id} but validated successfully.'
            f'\n{test_step}')

    def test_validate_step_without_expectations(self):
        test_step = self._define_path_step()
        test_step.expectations = []
        assert_true(
            ValidatePaths.validate_step(test_step),
            f'StepPath does not any expectations (which is acceptable)'
            f' and did not validate.\n{test_step}'
        )

    def test_validate_populated_step(self):
        test_step = self._define_path_step()
        logging.info(test_step)
        assert_true(
            ValidatePaths.validate_step(test_step),
            f'StepPath did not validate.\n{test_step}'
        )

    def test_validate_steps_with_duplicate_ids(self):
        num_steps = 5
        test_steps = self._define_path_steps(num_steps=num_steps)
        test_steps[0].id = test_steps[-1].id
        assert_false(
            ValidatePaths.validate_steps(test_steps),
            f'StepPaths with duplicate ids validated but should not have.\n'
            f'{test_steps[0]}\n{test_steps[-1]}'
        )

    def test_validate_steps_with_invalid_ids(self):
        num_steps = 5
        test_steps = self._define_path_steps(num_steps=num_steps)
        test_steps[-1].id = None
        assert_false(
            ValidatePaths.validate_steps(test_steps),
            f'StepPaths with an invalid id validated but should not have.\n'
            f'{test_steps[-1]}'
        )
