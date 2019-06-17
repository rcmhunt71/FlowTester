import os
from typing import NoReturn

from flowtester.state_machine.config.yaml_cfg import YamlInputFile
from flowtester.logging.logger import Logger
from flowtester.tests.unit.utils import get_data_dir

from nose.tools import assert_equals, assert_not_equals, assert_greater_equal

logging = Logger()


class TestYamlFile:

    TESTS_SUBDIR = 'tests'
    DATA_SUBDIR = 'data'

    EXISTING_YAML_FILE = 'general_sample.yaml'
    NON_EXISTING_YAML_FILE = 'this_does_not_exist.yaml'
    MALFORMED_YAML_FILE = 'general_malformed.yaml'

    def test_input_file_does_not_exist(self) -> NoReturn:
        # """
        # A non-existent YAML file returns '{}'
        #
        # Returns:
        #     None
        # """

        # Build file path
        data_path = get_data_dir(
            test_dir_name=self.TESTS_SUBDIR, data_dir_name=self.DATA_SUBDIR)
        data_file = os.path.sep.join(
            [data_path, self.NON_EXISTING_YAML_FILE])

        # Read in data file
        test_file_obj = YamlInputFile(input_file=data_file)

        assert_equals(test_file_obj.data, {})

    def test_input_file_exists(self) -> NoReturn:
        # """
        # A well defined YAML file returns a populated dictionary
        #
        # Returns:
        #     None
        #
        # """
        # Build file path
        data_path = get_data_dir(
            test_dir_name=self.TESTS_SUBDIR, data_dir_name=self.DATA_SUBDIR)
        data_file = os.path.sep.join(
            [data_path, self.EXISTING_YAML_FILE])

        # Read in data file
        test_file_obj = YamlInputFile(input_file=data_file)

        assert_not_equals(test_file_obj.data, {})
        assert_greater_equal(len(list(test_file_obj.data.keys())), 1)

    def test_malformed_yaml_file(self) -> NoReturn:
        # """
        # A malformed YAML generates Parser exception and returns '{}'
        #
        # Returns:
        #     None
        #
        # """
        # Build file path
        data_path = get_data_dir(
            test_dir_name=self.TESTS_SUBDIR, data_dir_name=self.DATA_SUBDIR)
        data_file = os.path.sep.join(
            [data_path, self.MALFORMED_YAML_FILE])

        # Read in data file
        test_file_obj = YamlInputFile(input_file=data_file)

        assert_equals(test_file_obj.data, {})
