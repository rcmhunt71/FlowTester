from random import choice
from typing import NoReturn

from mock import patch
from nose.tools import assert_equals, assert_not_equals, assert_in, assert_true

from flowtester.logging.logger import Logger
from flowtester.state_machine.paths.path_yaml import StatePathsYaml
from flowtester.tests.unit.utils import get_data_file

logging = Logger()


class TestStatePathsYaml:
    DATA_DIR_NAME = 'data'
    TEST_DIR_NAME = 'tests'
    SAMPLE_PATH = 'sample_path.yaml'

    def test_get_test_suites(self) -> NoReturn:
        # """
        #
        # Test suite names in yaml file match number and definition
        #
        # Returns:
        #     None
        # """

        # Determine expected data
        num_test_suites = 2
        expected_test_suite_names = [
            f"EXAMPLE_{x + 1}" for x in range(num_test_suites)]

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        test_suites = state_path_obj.get_test_suites()

        logging.info(f"EXPECTED TEST SUITES: {expected_test_suite_names}")
        logging.info(f"RETURNED TEST SUITES: {test_suites}")

        # Verify right number and names are returned.
        assert_equals(len(test_suites), num_test_suites)
        for name in test_suites:
            assert_in(name, expected_test_suite_names)

    def test_get_possible_test_cases(self):

        # Test get_possible_test_cases routine in path_yaml.py
        # Test requires specific data file

        # Determine expected results
        test_suite_name = "EXAMPLE_2"
        expected_num_test_cases = 2
        expected_testcase_names = [
            f'test_{x + 1}' for x in range(expected_num_test_cases)]

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        test_case_list = state_path_obj.get_possible_test_cases(
            test_suite=test_suite_name)

        logging.info(f"EXPECTED TEST CASES: {expected_testcase_names}")
        logging.info(f"RETURNED TEST CASES: {test_case_list}")

        # Verify right number and names are returned.
        assert_equals(len(test_case_list), expected_num_test_cases)
        for tc_name in test_case_list:
            assert_in(tc_name, expected_testcase_names)

    def test_get_traversal_path_with_correct_params(self):
        # Determine expected results
        test_suite_name = 'EXAMPLE_1'

        num_test_cases = 2
        test_case_name = 'test_{num}'.format(
            num=choice([x + 1 for x in range(num_test_cases)]))

        num_steps_in_test_case = 4
        step_names = [f"STEP_{x + 1}" for x in range(num_steps_in_test_case)]

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        traversal_path = state_path_obj.get_traversal_path(
            test_suite=test_suite_name, test_case=test_case_name)

        assert_equals(len(traversal_path), num_steps_in_test_case)
        for trigger in traversal_path:
            assert_in(trigger, step_names)

    def test_get_traversal_without_tc_name(self):
        # Determine expected results
        self._get_traversal_with_invalid_params(ts='EXAMPLE_1', tc=None)

    def test_get_traversal_without_ts_name(self):
        # Determine expected results
        self._get_traversal_with_invalid_params(ts=None, tc='test_1')

    def test_get_traversal_without_params(self):
        # Determine expected results
        self._get_traversal_with_invalid_params(ts=None, tc=None)

    def test_get_traversal_with_unknown_testsuite_and_testcase(self):
        # Determine expected results
        self._get_traversal_with_invalid_params(
            ts='ts_does_not_exist', tc='tc_does_not_exist')

    def _get_traversal_with_invalid_params(self, ts, tc):
        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        traversal_path = state_path_obj.get_traversal_path(
            test_suite=ts, test_case=tc)

        assert_equals(len(traversal_path), 0)

    def test_show_file(self):
        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        state_path_obj.show_file()

    def test_list_test_info_works(self):
        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        state_path_obj.list_test_info()

    def test_list_test_info_works_with_dne_test_suite(self):
        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        state_path_obj.list_test_info(test_suite='imaginary')

    def test_list_test_info_works_with_existing_test_suite(self):
        # Determine data file path
        test_suite = 'EXAMPLE_1'
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        state_path_obj.list_test_info(test_suite=test_suite)

    def test_get_traversal_path_with_test_case_def(self):
        # Determine expected results
        test_suite_name = 'EXAMPLE_1'

        num_test_cases = 2
        test_case_name = 'test_{num}'.format(
            num=choice([x + 1 for x in range(num_test_cases)]))

        num_steps_in_test_case = 4
        step_names = [f"STEP_{x + 1}" for x in range(num_steps_in_test_case)]

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        tc_def = state_path_obj.build_test_case(
            test_suite=test_suite_name, test_name=test_case_name)
        traversal_path = state_path_obj.get_traversal_path(
            test_case_def=tc_def)

        assert_equals(len(traversal_path), num_steps_in_test_case)
        for trigger in traversal_path:
            assert_in(trigger, step_names)

    def test_build_test_case_without_params(self):
        # Determine expected results
        test_suite_name = None
        test_case_name = None

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        tc_def = state_path_obj.build_test_case(
            test_suite=test_suite_name, test_name=test_case_name)

        assert_equals(len(tc_def), 0)

    @patch(
        'flowtester.state_machine.paths.path_yaml.ValidatePaths.validate_steps',
        return_value=False)
    def test_build_test_case_with_invalid_info(self, mock_inv_resp: str):

        test_suite_name = "EXAMPLE_1"
        test_case_name = "test_1"

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine (with mocked response in build_test_case)
        state_path_obj = StatePathsYaml(data_file)
        tc_def = state_path_obj.build_test_case(
            test_suite=test_suite_name, test_name=test_case_name)

        assert_equals(tc_def, [])

    def test_build_test_case_with_correct_params(self):
        # Determine expected results
        test_suite_name = "EXAMPLE_1"
        test_case_name = "test_1"
        test_case_steps = 4
        step_names = [f"STEP_{x + 1}" for x in range(test_case_steps)]

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        tc_def = state_path_obj.build_test_case(
            test_suite=test_suite_name, test_name=test_case_name)
        tc_step_names = [x.trigger for x in tc_def]

        assert_equals(len(tc_def), test_case_steps)
        for step in tc_step_names:
            assert_in(step, step_names)

    def test_get_path_validation_expectations_with_suite_and_case(self):

        # Test the StatePathYaml.get_test_validation_expectations() with a
        # valid testcase and testsuite

        expected_test_suite = 'EXAMPLE_1'
        expected_test_case = 'test_1'
        num_expectations = 2
        expectation_ids = [f"expectation_{x + 1}" for x in
                           range(num_expectations)]

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        expectations = state_path_obj.get_path_validation_expectations(
            test_suite=expected_test_suite, test_case=expected_test_case)

        # Verify expectations is a non-empty list
        assert_true(isinstance(expectations, list))
        assert_not_equals(expectations, [])

        # Verify each entry in the list (dictionary of dictionaries) has the
        # expected keys and the values are the correct data type (bool)
        for step in expectations:
            step_name = list(step.keys())[0]
            logging.info(f"STEP NAME: {step_name}")
            expectation_dict = list(step.values())[0]

            # Verify the keys are correct
            for exp_id in expectation_ids:
                assert_in(exp_id, list(expectation_dict.keys()),
                          f"{step_name}: Expected key ({exp_id}) was not found "
                          f"in the list of defined keys.")

                # Verify the values are booleans
                for key, exp in list(expectation_dict.items()):
                    assert_true(isinstance(exp, bool),
                                f"{step_name}: Expected value {str(exp)} for "
                                f"{key} was not a boolean")

    def test_get_path_validation_expectations_with_test_def(self):
        # Test the StatePathYaml.get_test_validation_expectations() with a
        # valid testcase and testsuite

        expected_test_suite = 'EXAMPLE_1'
        expected_test_case = 'test_1'
        num_expectations = 2
        expectation_ids = [f"expectation_{x + 1}" for x in
                           range(num_expectations)]

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        test_def = state_path_obj.build_test_case(
            test_suite=expected_test_suite, test_name=expected_test_case)
        expectations = state_path_obj.get_path_validation_expectations(
            test_case_def=test_def)

        # Verify expectations is a non-empty list
        assert_true(isinstance(expectations, list))
        assert_not_equals(expectations, [])

        # Verify each entry in the list (dictionary of dictionaries) has the
        # expected keys and the values are the correct data type (bool)
        for step in expectations:
            step_name = list(step.keys())[0]
            logging.info(f"STEP NAME: {step_name}")
            expectation_dict = list(step.values())[0]

            # Verify the keys are correct
            for exp_id in expectation_ids:
                assert_in(exp_id, list(expectation_dict.keys()),
                          f"{step_name}: Expected key ({exp_id}) was not found "
                          f"in the list of defined keys.")

                # Verify the values are booleans
                for key, exp in list(expectation_dict.items()):
                    assert_true(isinstance(exp, bool),
                                f"{step_name}: Expected value {str(exp)} for "
                                f"{key} was not a boolean")

    def test_get_path_validation_expectations_with_invalid_suite_and_case(self):

        # Test the StatePathYaml.get_test_validation_expectations() with an
        # invalid testcase and testsuite

        expected_test_suite = 'TS_DOES_NOT_EXIST'
        expected_test_case = 'TC_DOES_NOT_EXIST'

        self._get_path_validation_fail_path(
            ts=expected_test_suite, tc=expected_test_case)

    def test_get_path_validation_expectations_without_suite_and_case(self):

        # Test the StatePathYaml.get_test_validation_expectations() with an
        # invalid testcase and testsuite

        self._get_path_validation_fail_path(ts=None, tc=None)

    def _get_path_validation_fail_path(
            self, ts: str, tc: str) -> NoReturn:

        # Determine data file path
        data_file = get_data_file(
            filename=self.SAMPLE_PATH,
            test_dir_name=self.TEST_DIR_NAME,
            data_dir_name=self.DATA_DIR_NAME)

        # Execute routine
        state_path_obj = StatePathsYaml(data_file)
        expectations = state_path_obj.get_path_validation_expectations(
            test_suite=ts, test_case=tc)

        # Verify expectations is a non-empty list
        assert_true(isinstance(expectations, list))
        assert_equals(expectations, [])
