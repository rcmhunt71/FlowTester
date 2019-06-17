import os
import tempfile
from typing import Tuple

from flowtester.logging.logger import Logger
from flowtester.reporting.graph_path import GraphPath
from flowtester.state_machine.config.constants \
    import StateMachineConstants as SMConsts
from flowtester.state_machine.engine.input import PathStep
from flowtester.state_machine.engine.engine import StateMachine
from flowtester.tests.unit.utils import (
    get_model_name_from_raw_file,
    setup_state_machine_definitions)
from flowtester.tests.data.basic_state_machine_obj_model import ImportCheck

from nose.tools import (assert_equals, assert_greater_equal,
                        assert_true, assert_false,
                        assert_in, assert_not_in,
                        raises)


logging = Logger()


class TestStateMachine:
    MACHINE_DEFINITION_FILE = 'general_sample.yaml'
    SIMPLE_MACHINE_DEF_FILE = 'basic_state_machine.yaml'

    def test_model(self):
        # This tests a large percentage of the configure_state_machine.
        # Testing all paths is dependent on the model definition, and
        # general_sample.yaml contains the necessary conditions/definitions
        # to traverse all logic conditions.
        def_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        sm = StateMachine(data_model=model_def, object_model=None)
        sm.configure_state_machine()
        assert_true(isinstance(sm, StateMachine))

    def test_get_model_name(self):
        def_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        sm = StateMachine(data_model=model_def, object_model=None)
        expected_model_name = get_model_name_from_raw_file(def_file)

        logging.info(f"Expected Model Name: {expected_model_name}")
        logging.info(f"Actual Model Name: {sm.name}")

        assert_equals(sm.name, expected_model_name)

    def test__get_callback__exists(self):
        def_file, model_cfg, model_def = setup_state_machine_definitions(
            self.SIMPLE_MACHINE_DEF_FILE)

        obj_model = ImportCheck()

        sm = StateMachine(data_model=model_def, object_model=obj_model)
        api = sm._get_callback('object_model.test_routine')

        # Verify the routine returned a Callable reference.
        assert_true(callable(api))

        # Execute the API. It should return the default value, which is False
        assert_equals(api(), ImportCheck.DEFAULT_RESPONSE)

    @raises(AttributeError)
    def test__get_callback__does_not_exist(self):
        def_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        obj_model = ImportCheck()

        sm = StateMachine(data_model=model_def, object_model=obj_model)

        # Should raise AttributeError since the method does not exist.
        sm._get_callback('object_model.undefined_test_routine')

    def test__set_execution_description_no_args(self):
        def_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        expected_model_name = get_model_name_from_raw_file(def_file)

        obj_model = ImportCheck()

        sm = StateMachine(data_model=model_def, object_model=obj_model)
        sm.configure_state_machine()
        sm._set_execution_description()
        assert_equals(sm.description, expected_model_name)

    def test__set_execution_description_with_text(self):
        def_file, model_cfg, model_def = setup_state_machine_definitions(
            self.MACHINE_DEFINITION_FILE)

        expected_model_name = get_model_name_from_raw_file(def_file)
        descr = "test_str"

        obj_model = ImportCheck()

        sm = StateMachine(data_model=model_def, object_model=obj_model)
        sm.configure_state_machine()
        sm._set_execution_description(descr)
        assert_equals(sm.description, f"{expected_model_name} {descr}")

    def test_execute_transition_callback_no_data(self):
        model_file = self.SIMPLE_MACHINE_DEF_FILE
        self._test_trigger_call_back(model_file=model_file)

    def test_execute_transition_callback_with_data(self):
        data = 'SOME DATA PASSED TO ROUTINE'
        model_file = self.SIMPLE_MACHINE_DEF_FILE
        self._test_trigger_call_back(data=data, model_file=model_file)

    def _test_trigger_call_back(self, model_file, data=None):

        # Define and stage state machine for execution
        sm, trigger_name, trigger_callback = \
            self._setup_state_machine_for_execution(filename=model_file)

        # Execute transition
        sm.execute_transition_callback(data=data)

        # Object model will update data based on specific routine called.
        # Check obj model to verify trigger routine matches the last call
        # recorded to the object_model.
        assert_equals(trigger_callback.split('.')[-1],
                      sm.object_model.last_call)
        assert_equals(sm.object_model.data, data)

    @staticmethod
    def _setup_state_machine_for_execution(filename):
        def_file, model_cfg, model_def = setup_state_machine_definitions(
            filename)
        obj_model = ImportCheck()
        sm = StateMachine(data_model=model_def, object_model=obj_model)
        sm.configure_state_machine()

        # Get data about transition configuration
        trans_data = model_def.get_transitions(sm.machine.initial)[0]
        callback_routine = trans_data[SMConsts.CHANGE_STATE_ROUTINE]

        # Setup state machine to execute transition
        trigger_name = trans_data[SMConsts.TRIGGER_NAME]
        sm.current_step = PathStep(
            trigger=trigger_name,
            trigger_id=f'from_{sm.machine.initial}')
        return sm, trigger_name, callback_routine

    def test_validate_current_state_without_expectations(self):
        model_file = self.SIMPLE_MACHINE_DEF_FILE

        sm, trigger_name, callback_routine = \
            self._setup_state_machine_for_execution(filename=model_file)
        getattr(sm, trigger_name)()
        result = sm.validate_current_state()
        assert_equals(result, True)

    def test_validate_current_state_with_expectations(self):
        model_file = self.SIMPLE_MACHINE_DEF_FILE
        exp_result = False

        sm, trigger_name, callback_routine = \
            self._setup_state_machine_for_execution(filename=model_file)
        getattr(sm, trigger_name)()
        result = sm.validate_current_state(result=exp_result)
        assert_equals(result, exp_result)

    def test_validate_state_without_validations(self):
        model_file = self.SIMPLE_MACHINE_DEF_FILE
        exp_result = True

        sm, trigger_name, callback_routine = \
            self._setup_state_machine_for_execution(filename=model_file)
        result = sm.validate_current_state()
        assert_equals(result, exp_result)

    def test_generate_image_without_filename(self):
        self._test_image_generation()

    def test_generate_image_path_only(self):
        self._test_image_generation(path_only=True)

    def test_generate_image_wit_filename(self):
        # Create a temporary image filename
        filename = os.path.sep.join([
            tempfile.gettempdir(),
            f"{next(tempfile._get_candidate_names())}.png"])

        logging.info(f"Temp file: {filename}")
        self._test_image_generation(filename=filename)

    def _test_image_generation(
            self, filename: str = None, path_only: bool = False) -> None:
        """
        Instantiate a state machine and generate an
        image of the state machine.

        Args:
            filename (str): Filespec of file to store image
            path_only (str): Only generate the current image path

        Returns:
            None
        """
        # Set up state machine configuration
        model_file = self.SIMPLE_MACHINE_DEF_FILE
        def_file, model_cfg, model_def = setup_state_machine_definitions(
            model_file)
        expected_model_name = get_model_name_from_raw_file(def_file)

        # Build state machine
        obj_model = ImportCheck()
        sm = StateMachine(data_model=model_def, object_model=obj_model)
        sm.configure_state_machine()

        # Generate image
        image_name = sm.generate_image(filename=filename, path_only=path_only)

        # Assure image filename is correct and file exists
        filename = filename or os.path.abspath(f"{expected_model_name}.png")
        assert_equals(filename, image_name)
        assert_true(os.path.exists(image_name))

        # Verify image is deleted
        os.remove(image_name)
        assert_false(os.path.exists(image_name))

    def test_state_machine_traversal_path(self):
        model_file = self.SIMPLE_MACHINE_DEF_FILE

        sm, trigger_name, callback_routine = \
            self._setup_state_machine_for_execution(filename=model_file)

        steps = [PathStep(
            trigger=trigger_name,
            trigger_id=f'from_{sm.machine.initial}')]

        sm.execute_state_machine(input_data=steps)

        expected_path = [sm.machine.initial, sm.state]

        logging.info(f"EXPECTED PATH: {expected_path}")
        logging.info(f"ACTUAL PATH: {sm.path}")

        assert_true(isinstance(sm.path, list))
        assert_equals(expected_path, sm.path)

    def test_state_machine_illegal_path(self):
        model_file = self.SIMPLE_MACHINE_DEF_FILE
        illegal_trigger_name = 'ILLEGAL_TRIGGER'

        sm, trigger_name, callback_routine = \
            self._setup_state_machine_for_execution(filename=model_file)

        steps = [
            PathStep(
                trigger=trigger_name,
                trigger_id=f'from_{sm.machine.initial}'),
            PathStep(
                trigger=illegal_trigger_name,
                trigger_id="ILLEGAL STEP")
        ]

        # Execute the state machine
        sm.execute_state_machine(input_data=steps)

        # Illegal path should cause duplication of last state since
        # transition was requested but action denied.
        expected_path = [sm.machine.initial, sm.state, sm.state]

        logging.info(f"EXPECTED PATH: {expected_path}")
        logging.info(f"ACTUAL PATH: {sm.path}")

        assert_true(isinstance(sm.path, list))
        assert_equals(expected_path, sm.path)

    def test_execution_summary(self):

        detailed = False
        trigger_name, trigger_id, report = self._execute_and_generate_summary(
            detailed=detailed)
        assert_in(trigger_name, report)
        assert_not_in(trigger_id, report)
        assert_true(isinstance(report, str))

    def test_execution_summary_detailed(self):

        detailed = True
        trigger_name, trigger_id, report = self._execute_and_generate_summary(
            detailed=detailed)
        assert_in(trigger_name, report)
        assert_in(trigger_id, report)
        assert_true(isinstance(report, str))

    def test_traversal_path(self):
        sm, _, _ = self._setup_and_execute_state_machine()
        path = sm.traversal_path()
        assert_true(isinstance(path, GraphPath))

        # Four line per GraphPath entry, so if there is only 1 state,
        # there should be at least 4 lines.
        assert_greater_equal(len(str(path).split('\n')), 4)

    def _execute_and_generate_summary(self, detailed: bool = False) -> Tuple[str, str, str]:
        """
        Sets up and executes the model, and then generates the execution report

        Args:
            detailed (bool): True = Generate detailed report

        Returns:
            Tuple: trigger_name (str), trigger_id (str), report (str)

        """
        sm, trigger_name, trigger_id = self._setup_and_execute_state_machine()
        report = sm.execution_summary(detailed=detailed)
        return trigger_name, trigger_id, report

    def _setup_and_execute_state_machine(self) -> Tuple[StateMachine, str, str]:
        """
        Sets up and executes the model

        Returns:
            Tuple: state_machine (StateMachine), trigger_name (str), trigger_id (str)

        """
        model_file = self.SIMPLE_MACHINE_DEF_FILE

        sm, trigger_name, callback_routine = \
            self._setup_state_machine_for_execution(filename=model_file)

        trigger_id = f'from_{sm.machine.initial}'
        steps = [PathStep(
            trigger=trigger_name,
            trigger_id=trigger_id)]

        sm.execute_state_machine(input_data=steps)
        return sm, trigger_name, trigger_id

