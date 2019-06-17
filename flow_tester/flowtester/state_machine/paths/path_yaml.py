import pprint
import typing

from flowtester.logging.logger import Logger
from flowtester.state_machine.paths.referenced_yaml import ReferentialYAML
from flowtester.state_machine.config.yaml_cfg import YamlInputFile
from flowtester.state_machine.engine.input import PathStep
from flowtester.state_machine.paths.path_consts import YamlPathConsts
from flowtester.state_machine.paths.validation import ValidatePaths

logging = Logger()


class StatePathsYaml(YamlInputFile):

    def __init__(self, input_file):
        super(StatePathsYaml, self).__init__(input_file)
        self.test_case = None

        # Check if YAML file is a referential file (points to another YAML
        # file. If so, build corresponding updated YAML structure. If it
        # is not a referential file, it will return the original YAML
        # structure built by the YamlInputFile instantiation.
        self.data = ReferentialYAML(self).evaluate_yaml_file()

    def show_file(self):
        """
        Debug: show the contents of the file in python native data structures

        Returns:
            None

        """
        logging.info(f"FILE '{self.input_file}' contents:\n"
                     f"{pprint.pformat(self.data)}")

    def get_test_suites(self) -> typing.List[str]:
        """ List all test suites defined in file (YAML Dict Keys)

        Returns:
            List of test suites (keys)

        """
        return [list(ts.keys())[0] for ts in self.data]

    def get_possible_test_cases(self, test_suite: str) -> typing.List[str]:
        """ List all test cases defined for a specific test suite

        Args:
            test_suite: Test suite to get test cases

        Returns:
            List of test cases for the provided test suite

        """
        test_suites = self.get_test_suites()
        if test_suite not in test_suites:
            logging.debug(f"ERROR: Test suite '{test_suite}' not in list of "
                          f"known test suites in file '{self.input_file}':"
                          f" {test_suites} ")
            return ['']

        logging.debug(f"Requested Test Suite: {test_suite}")

        ts_data = [x for x in self.data if test_suite in x][0][test_suite]
        logging.debug(f"Test Suite Definition:\n{pprint.pformat(ts_data)}")

        test_cases = list(ts_data.keys())
        logging.debug(f"Test Cases: {test_cases}")

        return test_cases

    def build_test_case(
            self, test_suite: str, test_name: str) -> typing.List[PathStep]:
        """
        Get the test case definition for the specified test suite & test case

        Args:
            test_suite (str): Name of test suite (ConfigParser section)
            test_name (str): Name of test case (Config Parser section option)

        Returns:
            (list[dict]) Paths for state machine with execution
            and validation parameters

        """
        test_cases = self.get_possible_test_cases(test_suite)

        # Check if test case is defined...
        if test_name not in test_cases:
            logging.error(f"The test case '{test_name}' was not found in "
                          f"specified suite: '{test_suite}'")
            return []

        # Get test suite data, get the test case steps and return list
        ts_data = [x for x in self.data if test_suite in x][0][test_suite]

        test_case = []
        for tc in ts_data[test_name].get(YamlPathConsts.STEPS, []):
            step = PathStep(trigger=list(tc.keys())[0])

            # Record the trigger's unique id (if present)
            if YamlPathConsts.ID in tc[step.trigger]:
                step.add_id(tc[step.trigger][YamlPathConsts.ID])

            # Save validation expectations (id corresponds to specific
            # validation routine associated with step and result is the
            # expectation)
            if tc[step.trigger][YamlPathConsts.EXPECTATIONS] is not None:
                for v_id, exp in \
                        tc[step.trigger][YamlPathConsts.EXPECTATIONS].items():
                    step.add_expectation(v_id, exp)

            # Save the data to passed to the trigger if provided
            if (tc[step.trigger][YamlPathConsts.DATA] is not None or
                    tc[step.trigger][YamlPathConsts.DATA] != {}):
                step.add_data(tc[step.trigger][YamlPathConsts.DATA])

            test_case.append(step)

        self.test_case = test_case

        valid_path = ValidatePaths.validate_steps(steps=self.test_case)
        if not valid_path:
            logging.error("Errors found in the path definitions. "
                          "Returning an empty list of steps.")

        return self.test_case if valid_path else []

    def list_test_info(self, test_suite: str = None) -> str:
        """ Display test suite and test cases defined in the specified file.

        Args:
            test_suite: Name of test suite (OPTIONAL)

        Note:
            Specifying test suite will only list test cases associated with the
            test suite.

        Returns:
            (str) - listing of test suite(s) and test cases.

        """
        response = f"\nList of Test Suites & Test Cases in " \
            f"'{self.input_file}':\n"
        response += "-" * (len(response) - 1)
        test_cases_found = False

        # Iterate through the test suites
        suites = self.get_test_suites()
        for suite in sorted(suites):

            # If test suite was specified... only list those test cases
            if test_suite is not None and suite != test_suite:
                continue

            # We have a match or want all test suites, so list the test cases
            test_cases_found = True
            response += f"\n{suite}:\n\t"
            response += "\n\t".join(sorted(self.get_possible_test_cases(suite)))

        if not test_cases_found:
            response += f"\nTest suite '{test_suite}' not found."
            response += f"\nKnown test suites: {suites}"

        response += "\n"
        return response

    def get_traversal_path(
            self, test_suite: str = None, test_case: str = None,
            test_case_def: typing.List[PathStep] = None) -> typing.List[str]:
        """
        Get the list of steps defined in the testcase.

        Args:
            test_suite: Name of the Test Suite
            test_case: Name of the Test Case
            test_case_def: Definition of the test case

        Note:
            Either the test_suite & the test_case need to be specified or
            the test case definition (from StatePathYaml.get_test_case())

        Returns:
            List of steps (triggers) to traverse
        """

        test_case_def = test_case_def or self.test_case
        if test_case_def is None:
            if test_suite is None or test_case is None:
                logging.error("Need to specify the test suite and test case.")
                logging.error("Provided:\n"
                              f"Test Suite: {test_suite}\n"
                              f"Test Case: {test_case}")
                test_case_def = []
            else:
                test_case_def = self.build_test_case(test_suite, test_case)

        logging.debug(f"TEST CASE DEFINITION: {test_case_def}")

        return [x.trigger for x in test_case_def]

    def get_path_validation_expectations(
            self, test_suite: str = None, test_case: str = None,
            test_case_def: typing.List[PathStep] = None) -> typing.List[dict]:
        """
        Get the list of steps defined in the testcase.

        Args:
            test_suite: Name of the Test Suite
            test_case: Name of the Test Case
            test_case_def: Definition of the test case

        Note:
            Either the test_suite & the test_case need to be specified or
            the test case definition (from StatePathYaml.get_test_case())

        Returns:
            List of expectations per validation for the test case
                (dictionary: key = validation, value = expectation)
        """

        if test_case_def is None:
            if test_suite is None or test_case is None:
                logging.error("Need to specify the test suite and test case.")
                logging.error("Provided:\n"
                              f"test suite: {test_suite}\n"
                              f"test case: {test_case}")
                return []
            else:
                test_case_def = self.build_test_case(test_suite, test_case)

        expectations = []
        for step in test_case_def:
            expectations.append(
                {step.trigger:
                    {
                        step_def[PathStep.ID]:
                            step_def[PathStep.EXPECTATION] for step_def
                        in step.expectations}
                 }
            )

        return expectations
