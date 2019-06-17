import inspect
import logging
import os
from typing import Any

from flowtester.logging.logger import Logger, ContextAdapter

from nose.tools import assert_equals, assert_true, assert_false, raises, assert_is_none


class TestCommonLogging:

    def test_context_adapter__translate_to_dotted_lib_path(self):
        self._test__translate_to_dotted_lib_path(logger_class=ContextAdapter)

    def test_logger__translate_to_dotted_lib_path(self):
        self._test__translate_to_dotted_lib_path(logger_class=Logger)

    @staticmethod
    def _test__translate_to_dotted_lib_path(logger_class: Any) -> None:
        """
        Tests the dotted_path translation process. By necessity, it exists in the
        ContextManager and the base logger routine, although the assumptions are
        different. This routine has the ability to test both.

        Args:
            logger_class: Logger or ContextAdapter

        Returns:
            None

        """
        # Build sample path
        path_text = 'this is a test directory that does not exist'
        path_list = path_text.split(' ')

        # Define input and expectations
        path_dir = os.path.sep.join(path_list)
        expected_path = '.'.join(path_list)

        # Using provided class, get the data
        returned_path = logger_class._translate_to_dotted_lib_path(path_dir)

        print(f"DATA TO CREATE PATH: {path_list}")
        print(f"EXPECTED PATH: {expected_path}")
        print(f"RETURNED PATH: {returned_path}")

        assert_equals(returned_path, expected_path)

    def test_context_adapter__method_without_custom_project_options(self):
        adapter = ContextAdapter(logger=logging.getLogger(), extra={})
        self._test_logging_object__method(project='dne', logger_obj=adapter)

    def test_context_adapter__method_with_custom_project_options(self):
        adapter = ContextAdapter(logger=logging.getLogger(), extra={})
        self._test_logging_object__method(project='tests', logger_obj=adapter)

    def test_context_adapter__method_with_project_options_set_to_none(self):
        adapter = ContextAdapter(logger=logging.getLogger(), extra={})
        self._test_logging_object__method(project=None, logger_obj=adapter)

    def test_logger__method_without_custom_project_options(self):
        self._test_logging_object__method(project='dne', logger_obj=Logger())

    def test_logger__method_with_custom_project_options(self):
        self._test_logging_object__method(project='tests', logger_obj=Logger())

    def test_logger__method_with_project_options_set_to_none(self):
        self._test_logging_object__method(project=None, logger_obj=Logger())

    @staticmethod
    def _test_logging_object__method(project: str, logger_obj: Any) -> None:
        """
        Tests the method metadata determination process. By necessity, it exists
        in the ContextManager and the base logger routine, although the
        assumptions are different. This routine has the ability to test both.

        Args:
            project (str): Name of project (used as part of the parameterized testing)
            logger_obj: Object/Class containing method under test

        Returns:
            None

        """
        # Set the expectations for pid
        expected_pid = os.getpid()

        # Get the returned data (arguments depend on type of logger provided)
        if isinstance(logger_obj, ContextAdapter):

            # Returned filename will be converted to python path notation without the file extension
            expected_filename = __file__.split('.')[0]

            # If the project is set and matches the path, only the path beyond the project name will
            # be returned.
            expected_filename_parts = expected_filename.split(os.path.sep)
            if project in expected_filename_parts:
                index = expected_filename_parts.index(project)
                expected_filename_parts = expected_filename_parts[index + 1:]

            # Build the dotted notation
            expected_filename = '.'.join(expected_filename_parts)

            expected_routine = '_test_logging_object__method'
            method_args = {'project': project, 'depth': 1}
            filename, line_num, routine, pid = logger_obj._method(**method_args)

        else:
            response_dict = logger_obj._method()
            elements = ['file_name', 'linenum', 'routine', 'pid']
            (filename, line_num, routine, pid) = [response_dict[x] for x in elements]

            # Unable to determine since nose sets the execution path and routine
            expected_filename = filename
            expected_routine = 'runTest'

        print(f"Returned FILENAME: {filename}")
        print(f"Expected FILENAME: {expected_filename}\n")

        # NOTE: Line num is not validated because it changes too easily and would break the test.
        print(f"Returned LINENUM: {line_num}\n")

        print(f"Returned ROUTINE: {routine}")
        print(f"Expected ROUTINE: {expected_routine}\n")

        print(f"Returned PID: {pid}")
        print(f"Expected PID: {expected_pid}")

        assert_equals(filename, expected_filename)
        assert_equals(routine, expected_routine)
        assert_equals(pid, expected_pid)


class TestLogger:
    def test_basic_logger(self):
        logger = Logger()

        # Remove the file extension from the file, and transform into dotted path notation
        expected_logger_name = ".".join(__file__.split('.')[0].split(os.path.sep))

        assert_equals(logger.loglevel, Logger.DEFAULT_LOG_LEVEL)
        assert_false(logger.root)
        assert_is_none(logger.filename)
        assert_equals(logger.project, logger.DEFAULT_PROJECT)
        assert_equals(logger.name, expected_logger_name)
        assert_true(isinstance(logger.logger, ContextAdapter))

    def test_logging_level_info(self):
        self._test_logging_level('info')

    def test_logging_level_debug(self):
        self._test_logging_level('debug')

    def test_logging_level_warn(self):
        self._test_logging_level('warn')

    def test_logging_level_warning(self):
        self._test_logging_level('warning')

    def test_logging_level_error(self):
        self._test_logging_level('error')

    def test_logging_level_critical(self):
        self._test_logging_level('critical')

    def test_logging_level_exception(self):
        self._test_logging_level('exception')

    @staticmethod
    def _test_logging_level(level: str) -> None:
        """
        Invokes logging method based on level.

        Args:
            level (str): name of logging level

        Returns:
            None

        """
        logger = Logger()
        log_method = getattr(logger, level.lower())
        log_method(f"This is a test for logger level {level.upper()}. "
                   f"This should not crash or throw an error.")

    def test_determine_project(self):
        filename = inspect.stack()[-1].filename
        expected_file_path = os.path.sep.join(filename.split(os.path.sep)[:-1])
        returned_file_path = Logger.determine_project()

        print(f"FILE: {filename}")
        print(f"EXPECTED PATH: {expected_file_path}")
        print(f"RETURNED PATH: {expected_file_path}")

        assert_equals(returned_file_path, expected_file_path)
