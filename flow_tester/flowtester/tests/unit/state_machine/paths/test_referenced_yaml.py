import copy
import pprint
import typing

from nose.tools import (
    assert_true, assert_equals, assert_not_equals, raises, assert_greater_equal)

from flowtester.logging.logger import Logger
from flowtester.state_machine.paths.referenced_yaml import (
    ReferentialYAML, ReferenceParseError, StepIdExists,
    UndefinedId, MissingIdLandmark, UndefinedStep)
from flowtester.state_machine.config.yaml_cfg import YamlInputFile
from flowtester.state_machine.config.constants import StateMachineConstants \
    as SMConsts
from flowtester.state_machine.paths.path_yaml import YamlPathConsts \
    as YAMLConsts
from flowtester.tests.unit.utils import get_data_file


logging = Logger()


class TestReferentialYaml:

    TESTS_SUBDIR = 'tests'
    DATA_SUBDIR = 'data'
    SIMPLE_REF = 'sample_referential_path.yaml'
    BASE_REF_FILE = 'sample_path.yaml'
    TEST_SUITE = 'EXAMPLE_1'
    TEST_CASE = 'test_1'

    # ---------------------------------------------------------
    # ReferentialYAML.check_if_file_references_another_file()
    # ---------------------------------------------------------
    def test_check_if_file_references_another_valid_file_and_validate_ref(self):

        expected_ref_obj = ReferentialYAML.REFERENCE_DATA(
            target_test_suite=self.TEST_SUITE,
            target_test_case=self.TEST_CASE,
            reference_file=self.BASE_REF_FILE,
            reference_test_suite=self.TEST_SUITE,
            reference_test_case=self.TEST_CASE)

        data_file = get_data_file(
            test_dir_name=self.TESTS_SUBDIR,
            data_dir_name=self.DATA_SUBDIR,
            filename=self.SIMPLE_REF)

        yaml_obj = YamlInputFile(input_file=data_file)
        ref_yaml_obj = ReferentialYAML(yaml_input=yaml_obj)

        # Verify the reference is found
        assert_true(ref_yaml_obj.check_if_file_references_another_file())

        # Verify the reference was parsed correctly
        for ref_obj in ref_yaml_obj.references:
            self._validate_reference_data(expected_ref_obj, ref_obj)

    @raises(ReferenceParseError)
    def test_check_if_file_references_another_file_invalid_reference(self):
        data_file = get_data_file(
            test_dir_name=self.TESTS_SUBDIR,
            data_dir_name=self.DATA_SUBDIR,
            filename=self.SIMPLE_REF)

        yaml_obj = YamlInputFile(input_file=data_file)

        illegal_value = (f"{self.BASE_REF_FILE}{ReferentialYAML.DELIMITER}"
                         f"{self.TEST_SUITE}{ReferentialYAML.DELIMITER}")

        self._update_yaml(yaml=yaml_obj,
                          test_suite=self.TEST_SUITE,
                          test_case=self.TEST_CASE,
                          element=SMConsts.REFERENCE,
                          value=illegal_value)

        ref_yaml_obj = ReferentialYAML(yaml_input=yaml_obj)

        # Verify the reference is found but fails due to being unable to parse
        ref_yaml_obj.check_if_file_references_another_file()

    @raises(ReferenceParseError)
    def test_check_if_file_references_empty_string(self):
        data_file = get_data_file(
            test_dir_name=self.TESTS_SUBDIR,
            data_dir_name=self.DATA_SUBDIR,
            filename=self.SIMPLE_REF)

        yaml_obj = YamlInputFile(input_file=data_file)

        self._update_yaml(yaml=yaml_obj,
                          test_suite=self.TEST_SUITE,
                          test_case=self.TEST_CASE,
                          element=SMConsts.REFERENCE,
                          value='')

        ref_yaml_obj = ReferentialYAML(yaml_input=yaml_obj)

        # Verify the reference is found but fails due to being unable to parse
        ref_yaml_obj.check_if_file_references_another_file()

    # ---------------------------------------------
    # ReferentialYAML.get_referenced_test_data()
    # ---------------------------------------------
    def test_get_referenced_test_data(self):
        filename = self.SIMPLE_REF
        test_suite = self.TEST_SUITE
        test_case = self.TEST_CASE

        tc_data = self._test_get_referenced_test_data(
            filename=filename, testsuite=test_suite, testcase=test_case)
        assert_true(isinstance(tc_data, dict))
        assert_greater_equal(len(tc_data.keys()), 0)

    def test_get_referenced_test_data_invalid_ts(self):
        filename = self.SIMPLE_REF
        test_suite = "DNE"
        test_case = self.TEST_CASE

        tc_data = self._test_get_referenced_test_data(
            filename=filename, testsuite=test_suite, testcase=test_case)
        assert_true(isinstance(tc_data, dict))
        assert_equals(tc_data, {})

    def test_get_referenced_test_data_invalid_tc(self):
        filename = self.SIMPLE_REF
        test_suite = self.TEST_SUITE
        test_case = "DNE"

        tc_data = self._test_get_referenced_test_data(
            filename=filename, testsuite=test_suite, testcase=test_case)
        assert_true(isinstance(tc_data, dict))
        assert_equals(tc_data, {})

    # ---------------------------------------------
    # ReferentialYAML.add_referenced_tc_to_ts()
    # ---------------------------------------------
    def test_add_referenced_tc_to_ts(self):
        tc_data = {
            YAMLConsts.DESCRIPTION: "Added test",
            YAMLConsts.STEPS: {
                'STEP_A': {},
                'STEP_B': {}
            }
        }

        data_file = get_data_file(
            test_dir_name=self.TESTS_SUBDIR,
            data_dir_name=self.DATA_SUBDIR,
            filename=self.SIMPLE_REF)

        yaml_obj = YamlInputFile(input_file=data_file)
        ref_yaml_obj = ReferentialYAML(yaml_input=yaml_obj)

        ref_yaml_obj.add_referenced_tc_to_ts(
            target_ts=self.TEST_SUITE,
            target_tc=self.TEST_CASE,
            tc_data=tc_data)

        updated_tc_yaml = ref_yaml_obj.data[0][self.TEST_SUITE][self.TEST_CASE]
        del updated_tc_yaml[YAMLConsts.REFERENCE]

        logging.info(f"Data added: {tc_data}")
        logging.info(f"Updated YAML Data: {updated_tc_yaml}")

        assert_equals(tc_data.get(YAMLConsts.STEPS, {}),
                      updated_tc_yaml.get(YAMLConsts.STEPS, {}))

    def test_add_referenced_tc_to_ts_where_tc_is_new(self):
        tc_data = {
            YAMLConsts.DESCRIPTION: "Added test",
            YAMLConsts.STEPS: {
                'STEP_A': {},
                'STEP_B': {}
            }
        }
        test_case_name = "NEW_TEST_CASE"

        data_file = get_data_file(
            test_dir_name=self.TESTS_SUBDIR,
            data_dir_name=self.DATA_SUBDIR,
            filename=self.SIMPLE_REF)

        yaml_obj = YamlInputFile(input_file=data_file)
        ref_yaml_obj = ReferentialYAML(yaml_input=yaml_obj)

        ref_yaml_obj.add_referenced_tc_to_ts(
            target_ts=self.TEST_SUITE,
            target_tc=test_case_name,
            tc_data=tc_data)

        updated_tc_yaml = ref_yaml_obj.data[0][self.TEST_SUITE][test_case_name]

        logging.info(f"Data added: {tc_data}")
        logging.info(f"Updated YAML Data: {updated_tc_yaml}")

        assert_equals(tc_data.get(YAMLConsts.STEPS, {}),
                      updated_tc_yaml.get(YAMLConsts.STEPS, {}))

    # ---------------------------------------------
    # ADD: ReferentialYAML.add_steps()
    # ---------------------------------------------
    def test_add_steps_valid_config_before_id(self):
        added_step_name_1 = 'STEP_1A'
        insert_before_id_1 = '2'
        added_test_case_id_1 = 'ADDED_1'

        added_step_name_2 = 'STEP_2A'
        insert_before_id_2 = '3'
        added_test_case_id_2 = 'ADDED_2'

        tc_step_data = [
            {
                added_step_name_1:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id_1,
                    YAMLConsts.ID: added_test_case_id_1,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            },
            {
                added_step_name_2:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id_2,
                    YAMLConsts.ID: added_test_case_id_2,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)

        # Verify the steps exist and are in the list
        insert_index_1 = ids.index(added_test_case_id_1)
        before_index_1 = ids.index(insert_before_id_1)
        insert_index_2 = ids.index(added_test_case_id_2)
        before_index_2 = ids.index(insert_before_id_2)

        # Verify the added step id is before the "before_id" step id
        assert_equals(insert_index_1 + 1, before_index_1)
        assert_equals(insert_index_2 + 1, before_index_2)

    def test_add_steps_valid_config_before_added_step_id(self):
        added_step_name_1 = 'STEP_1A'
        insert_before_id_1 = '2'
        added_test_case_id_1 = 'ADDED_1'

        added_step_name_2 = 'STEP_2A'
        insert_before_id_2 = 'ADDED_1'
        added_test_case_id_2 = 'ADDED_2'

        tc_step_data = [
            {
                added_step_name_1:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id_1,
                    YAMLConsts.ID: added_test_case_id_1,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            },
            {
                added_step_name_2:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id_2,
                    YAMLConsts.ID: added_test_case_id_2,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)

        # Verify the steps exist and are in the list
        insert_index_1 = ids.index(added_test_case_id_1)
        before_index_1 = ids.index(insert_before_id_1)
        insert_index_2 = ids.index(added_test_case_id_2)
        before_index_2 = ids.index(insert_before_id_2)

        # Verify the added step id is before the "before_id" step id
        assert_equals(insert_index_1 + 1, before_index_1)
        assert_equals(insert_index_2 + 1, before_index_2)

    def test_add_steps_valid_config_before_and_after_added_step_id(self):
        added_step_name_1 = 'STEP_1A'
        insert_before_id_1 = '2'
        added_test_case_id_1 = 'ADDED_1'

        added_step_name_2 = 'STEP_2A'
        insert_after_id_2 = 'ADDED_1'
        added_test_case_id_2 = 'ADDED_2'

        tc_step_data = [
            {
                added_step_name_1:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id_1,
                    YAMLConsts.ID: added_test_case_id_1,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            },
            {
                added_step_name_2:
                {
                    YAMLConsts.AFTER_ID: insert_after_id_2,
                    YAMLConsts.ID: added_test_case_id_2,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)

        logging.info(f"ID List:\n{' '.join(ids)}")

        # Verify the steps were added and are in the list
        insert_index_1 = ids.index(added_test_case_id_1)
        before_index_1 = ids.index(insert_before_id_1)
        insert_index_2 = ids.index(added_test_case_id_2)
        after_index_2 = ids.index(insert_after_id_2)

        # before_index_1 will be two lower than the insertion spot since the
        # before_index_1 will be shifted an additional slot due the second
        # (step_id = STEP_2A) insertion.
        assert_equals(insert_index_1 + 2, before_index_1)

        # Verify the added step id is before the "after_id" step id
        assert_equals(insert_index_2, after_index_2 + 1)

    def test_add_steps_valid_config_after_id(self):
        added_step_name = 'STEP_1A'
        insert_after_id = '1'
        added_test_case_id = 'ADDED_1'
        tc_step_data = [
            {
                added_step_name:
                {
                    YAMLConsts.AFTER_ID: insert_after_id,
                    YAMLConsts.ID: added_test_case_id,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                },
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)

        # Verify the steps exist and are in the list
        insert_index = ids.index(added_test_case_id)
        after_index = ids.index(insert_after_id)

        # Verify the added step id is before the "after_id" step id
        assert_equals(insert_index, after_index + 1)

    def test_add_steps_valid_config_both_before_after_id(self):
        added_step_name = 'STEP_1A'
        insert_before_id = '2'
        insert_after_id = '1'
        added_test_case_id = 'ADDED_1'
        tc_step_data = [
            {
                added_step_name:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id,
                    YAMLConsts.AFTER_ID: insert_after_id,
                    YAMLConsts.ID: added_test_case_id,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                },
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)

        # Verify the steps exist and are in the list
        insert_index = ids.index(added_test_case_id)
        before_index = ids.index(insert_before_id)

        # Verify the added step id is before the "before_id" step id
        assert_equals(insert_index + 1, before_index)

    def test_add_steps_valid_config_both_before_after_id_with_same_id(self):
        # The "after_id" will be honored as the final position
        # See referenced_yaml.py:ReferencedYaml._get_target_landmark() for
        # more information

        added_step_name = 'STEP_1A'
        insert_before_id = '2'
        insert_after_id = '2'
        added_test_case_id = 'ADDED_1'
        tc_step_data = [
            {
                added_step_name:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id,
                    YAMLConsts.AFTER_ID: insert_after_id,
                    YAMLConsts.ID: added_test_case_id,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                },
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)

        # Verify the steps exist and are in the list
        insert_index = ids.index(added_test_case_id)
        before_index = ids.index(insert_before_id)
        after_index = ids.index(insert_after_id)

        # Verify the added step id is before the "after_id" step id
        assert_equals(insert_index, after_index + 1)
        assert_not_equals(insert_index + 1, before_index)

    @raises(UndefinedId)
    def test_add_steps_valid_config_with_valid_before_invalid_after_id(self):
        # Should fail because after_id is invalid
        added_step_name = 'STEP_1A'
        insert_before_id = '2'
        insert_after_id = '7'
        added_test_case_id = 'ADDED_1'
        tc_step_data = [
            {
                added_step_name:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id,
                    YAMLConsts.AFTER_ID: insert_after_id,
                    YAMLConsts.ID: added_test_case_id,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                },
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)
        logging.error(f"IDs Returned: {', '.join(ids)}")

    @raises(StepIdExists)
    def test_add_steps__before__step_id_is_existing_id(self):
        added_step_name = 'STEP_1A'
        insert_before_id = '2'
        added_test_case_id = '3'
        tc_step_data = [
            {
                added_step_name:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id,
                    YAMLConsts.ID: added_test_case_id,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                },
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)
        logging.error(f"IDs Returned: {', '.join(ids)}")

    @raises(StepIdExists)
    def test_add_steps__after__step_id_is_existing_id(self):
        added_step_name = 'STEP_1A'
        insert_after_id = '2'
        added_test_case_id = '3'
        tc_step_data = [
            {
                added_step_name:
                {
                    YAMLConsts.AFTER_ID: insert_after_id,
                    YAMLConsts.ID: added_test_case_id,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                },
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)
        logging.error(f"IDs Returned: {', '.join(ids)}")

    @raises(UndefinedId)
    def test_add_steps__before__nonexistent_id(self):
        added_step_name = 'STEP_1A'
        insert_before_id = '7'
        added_test_case_id = '100'
        tc_step_data = [
            {
                added_step_name:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id,
                    YAMLConsts.ID: added_test_case_id,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                },
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)
        logging.error(f"IDs Returned: {', '.join(ids)}")

    @raises(UndefinedId)
    def test_add_steps__after__nonexistent_id(self):
        added_step_name = 'STEP_1A'
        insert_after_id = '7'
        added_test_case_id = '100'
        tc_step_data = [
            {
                added_step_name:
                {
                    YAMLConsts.AFTER_ID: insert_after_id,
                    YAMLConsts.ID: added_test_case_id,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                },
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)
        logging.error(f"IDs Returned: {', '.join(ids)}")

    @raises(MissingIdLandmark)
    def test_add_steps_without_landmark(self):
        added_step_name = 'STEP_1A'
        added_test_case_id = 'ADDED_STEP'
        tc_step_data = [
            {
                added_step_name:
                {
                    YAMLConsts.ID: added_test_case_id,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                },
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)
        logging.error(f"IDs Returned: {', '.join(ids)}")

    @raises(StepIdExists)
    def test_add_steps_valid_config_duplicate_ids_to_be_added(self):
        added_step_name_1 = 'STEP_1A'
        insert_before_id_1 = '2'
        added_test_case_id_1 = 'ADDED_1'

        added_step_name_2 = 'STEP_2A'
        insert_after_id_2 = 'ADDED_1'
        added_test_case_id_2 = 'ADDED_1'

        tc_step_data = [
            {
                added_step_name_1:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id_1,
                    YAMLConsts.ID: added_test_case_id_1,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            },
            {
                added_step_name_2:
                {
                    YAMLConsts.AFTER_ID: insert_after_id_2,
                    YAMLConsts.ID: added_test_case_id_2,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            }
        ]

        ids = self._test_add_steps_and_get_ids(tc_step_data=tc_step_data)
        logging.error(f"IDs were returned:\n{', '.join(ids)}")

    # ---------------------------------------------
    # MODIFY: ReferentialYAML.modify_steps()
    # ---------------------------------------------
    def test_modify_steps_valid(self):
        yaml_file = self.SIMPLE_REF
        tc_step_data = [
            {
                "STEP_1":
                    {
                        YAMLConsts.ID: 1,
                        YAMLConsts.DATA: {'params': 1, 'value': 7},
                        YAMLConsts.EXPECTATIONS:
                            {
                                "expectations_10": False,
                                "expectations_20": True,
                            }
                    }
            }
        ]

        expected_tc, actual_tc = self._test_modify_steps(
            filename=yaml_file, testsuite=self.TEST_SUITE,
            testcase=self.TEST_CASE, updated_step_data=tc_step_data)

        # Verify the actual and expected testcases are the same.
        # NOTE: __self__.maxDiff --> Enables full diffs rather than
        #       truncate based on a specific character count
        assert_equals.__self__.maxDiff = None
        assert_equals(expected_tc, actual_tc)

    @raises(UndefinedId)
    def test_modify_steps_invalid_step_non_existent_id(self):
        yaml_file = self.SIMPLE_REF
        tc_step_data = [
            {
                "STEP_1":
                    {
                        YAMLConsts.ID: 'DNE',
                        YAMLConsts.DATA: {'params': 1, 'value': 7},
                        YAMLConsts.EXPECTATIONS:
                            {
                                "expectations_10": False,
                                "expectations_20": True,
                            }
                    }
            }
        ]
        expected_tc, actual_tc = self._test_modify_steps(
            filename=yaml_file, testsuite=self.TEST_SUITE,
            testcase=self.TEST_CASE, updated_step_data=tc_step_data)
        logging.error(f"Returned updated Test Cases:\n"
                      f"EXPECTED:\n{pprint.pformat(expected_tc)}\n"
                      f"ACTUAL:\n{pprint.pformat(actual_tc)}")

    def test_modify_steps_invalid_step_non_existent_step_name(self):
        # Should not have any impact since steps are referenced by step id
        # and the update should not change the step/trigger name.
        yaml_file = self.SIMPLE_REF
        tc_step_data = [
            {
                "DNE":
                    {
                        YAMLConsts.ID: 1,
                        YAMLConsts.DATA: None,
                        YAMLConsts.EXPECTATIONS: None
                    }
            }
        ]
        expected_tc, actual_tc = self._test_modify_steps(
            filename=yaml_file, testsuite=self.TEST_SUITE,
            testcase=self.TEST_CASE, updated_step_data=tc_step_data)

        # Verify the actual and expected testcases are the same.
        # NOTE: __self__.maxDiff --> Enables full diffs rather than
        #       truncate based on a specific character count
        assert_equals.__self__.maxDiff = None
        assert_equals(expected_tc, actual_tc)

    # ---------------------------------------------
    # DELETE: ReferentialYAML.delete_steps()
    # ---------------------------------------------
    def test_delete_steps_valid_step_ids(self):
        delete_step_ids = ['3', '4']
        orig_ids, updated_ids = self._test_delete_steps_and_get_ids(
            delete_ids=delete_step_ids)

        # Validate requested IDs were removed
        assert_equals(set(orig_ids) - set(delete_step_ids), set(updated_ids))

    @raises(UndefinedStep)
    def test_delete_steps_invalid_step_ids(self):
        delete_step_ids = ['3a', '4a']
        orig_ids, updated_ids = self._test_delete_steps_and_get_ids(
            delete_ids=delete_step_ids)

        # Validate requested IDs were removed
        assert_equals(set(orig_ids) - set(delete_step_ids), set(updated_ids))

    def test_delete_steps_duplicate_step_ids(self):
        delete_step_ids = ['3', '3']
        orig_ids, updated_ids = self._test_delete_steps_and_get_ids(
            delete_ids=delete_step_ids)

        # Validate requested IDs were removed
        assert_equals(set(orig_ids) - set(delete_step_ids), set(updated_ids))

    def test_delete_steps_empty_list_of_step_ids(self):
        delete_step_ids = []
        orig_ids, updated_ids = self._test_delete_steps_and_get_ids(
            delete_ids=delete_step_ids)

        # Validate requested IDs were removed
        assert_equals(set(orig_ids) - set(delete_step_ids), set(updated_ids))

    # ---------------------------------------------
    # EVAL: ReferentialYAML.evaluate_yaml_file()
    # ---------------------------------------------
    def test_evaluate_yaml_file(self):

        filename = self.SIMPLE_REF
        testsuite = self.TEST_SUITE
        testcase = self.TEST_CASE
        element = YAMLConsts.DEL_STEPS

        added_step_name_1 = 'STEP_1A'
        insert_before_id_1 = '2'
        added_test_case_id_1 = 'ADDED_1'

        added_step_name_2 = 'STEP_2A'
        insert_after_id_2 = 'ADDED_1'
        added_test_case_id_2 = 'ADDED_2'

        add_tc_data = [
            {
                added_step_name_1:
                {
                    YAMLConsts.BEFORE_ID: insert_before_id_1,
                    YAMLConsts.ID: added_test_case_id_1,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            },
            {
                added_step_name_2:
                {
                    YAMLConsts.AFTER_ID: insert_after_id_2,
                    YAMLConsts.ID: added_test_case_id_2,
                    YAMLConsts.DATA: None,
                    YAMLConsts.EXPECTATIONS: {'test_me': False}
                }
            }
        ]

        modify_tc_data = [
            {
                "STEP_1":
                    {
                        YAMLConsts.ID: 'DNE',
                        YAMLConsts.DATA: {'params': 1, 'value': 7},
                        YAMLConsts.EXPECTATIONS:
                            {
                                "expectations_10": False,
                                "expectations_20": True,
                            }
                    }
            }
        ]

        delete_step_ids = ['3', '4']

        data_file = get_data_file(
            test_dir_name=self.TESTS_SUBDIR, data_dir_name=self.DATA_SUBDIR,
            filename=filename)
        yaml_obj = YamlInputFile(input_file=data_file)
        test_yaml_obj = ReferentialYAML(yaml_input=yaml_obj)
        test_yaml_obj.evaluate_yaml_file()

        ref_yaml_obj = self._read_and_update_source_yaml_file(
            filename=filename, testsuite=testsuite, testcase=testcase,
            element=YAMLConsts.ADD_STEPS, value=add_tc_data)

        ref_yaml_obj = self._read_and_update_source_yaml_file(
            filename=filename, testsuite=testsuite, testcase=testcase,
            element=YAMLConsts.MOD_STEPS, value=modify_tc_data,
            ref_yaml=ref_yaml_obj)

        ref_yaml_obj = self._read_and_update_source_yaml_file(
            filename=filename, testsuite=testsuite, testcase=testcase,
            element=YAMLConsts.DEL_STEPS, value=delete_step_ids,
            ref_yaml=ref_yaml_obj)

        ref_ts = list(ref_yaml_obj.data[0].values())[0]
        ref_tc = list(ref_ts.values())[0]
        del ref_tc[YAMLConsts.ADD_STEPS]
        del ref_tc[YAMLConsts.MOD_STEPS]
        del ref_tc[YAMLConsts.DEL_STEPS]

        assert_equals.__self__.maxDiff = None
        assert_equals(test_yaml_obj.data, ref_yaml_obj.data)

    # ---------------------------------------------
    #        TEST HELPER ROUTINES
    # ---------------------------------------------
    def _test_delete_steps_and_get_ids(
            self, delete_ids: typing.List[str]) \
            -> typing.Tuple[typing.List[str], typing.List[str]]:
        """
        Delete the provided steps to the base path definition, and return the
        ordered list of IDs in the definition before and after the deletion.

        Args:
            delete_ids (List[str]): List of IDs to delete

        Returns:
            Tuple of Lists of Str: 2 lists of ids (str) -->
            before and after deletion

        """
        filename = self.SIMPLE_REF
        testsuite = self.TEST_SUITE
        testcase = self.TEST_CASE
        element = YAMLConsts.DEL_STEPS

        ref_yaml_obj = self._read_and_update_source_yaml_file(
            filename=filename, testsuite=testsuite, testcase=testcase,
            element=element, value=delete_ids)

        # Get list of original IDs
        orig_ids = self._get_testcase_ids(
            yaml_data=ref_yaml_obj, test_suite=self.TEST_SUITE,
            test_case=self.TEST_CASE)

        # Delete the requested steps
        ref_yaml_obj.delete_steps()

        # Get list if IDs
        updated_ids = self._get_testcase_ids(
            yaml_data=ref_yaml_obj, test_suite=self.TEST_SUITE,
            test_case=self.TEST_CASE)

        return orig_ids, updated_ids

    def _test_add_steps_and_get_ids(self, tc_step_data: list) -> list:
        """
        Add the provided steps to the base path definition, and return the
        ordered list of IDs in the definition.

        Args:
            tc_step_data (list): Data to add to the base path definition

        Returns:
            List of ids in the path definition

        """
        filename = self.SIMPLE_REF
        testsuite = self.TEST_SUITE
        testcase = self.TEST_CASE
        element = YAMLConsts.ADD_STEPS

        ref_yaml_obj = self._read_and_update_source_yaml_file(
            filename=filename, testsuite=testsuite, testcase=testcase,
            element=element, value=tc_step_data)

        # Insert the new steps to the YAML
        ref_yaml_obj.add_steps()

        # Get the list of test step IDs
        ids = self._get_testcase_ids(
            yaml_data=ref_yaml_obj.yaml, test_suite=self.TEST_SUITE,
            test_case=self.TEST_CASE)

        logging.info(f"STEPS: {', '.join(ids)}")
        return ids

    def _test_get_referenced_test_data(
            self, filename: str, testsuite: str, testcase: str) -> dict:
        """
        Call get_referenced_test_data and return results

        Args:
            filename (str): Name of YAML file to read
            testsuite (str): Name of testsuite to retrieve
            testcase (str): Name of testcase to retrieve

        Returns:
            Dict: test case definition that meet the provide parameters

        """
        data_file = get_data_file(
            test_dir_name=self.TESTS_SUBDIR, data_dir_name=self.DATA_SUBDIR,
            filename=filename)

        yaml_obj = YamlInputFile(input_file=data_file)
        ref_yaml_obj = ReferentialYAML(yaml_input=yaml_obj)

        tc_data = ref_yaml_obj.get_referenced_test_data(
            yaml_input=ref_yaml_obj, testsuite=testsuite, testcase=testcase)

        return tc_data

    def _test_modify_steps(
            self, filename: str, testsuite: str, testcase: str,
            updated_step_data: list) -> typing.Tuple[dict, dict]:
        """
        Get the ReferentialYAML file, and update the specified testsuite &
        testcase with the specified modifications

        Args:
            filename (str): Name of the YAML file to read
            testsuite (str): Test suite to update
            testcase (str): Test case to update
            updated_step_data (List): List of dictionaries of updated step data

        Returns:
            Tuple of 2 dictionaries (expected & actual test case definitions)

        """
        element = YAMLConsts.MOD_STEPS
        ref_yaml_obj = self._read_and_update_source_yaml_file(
            filename=filename, testsuite=testsuite, testcase=testcase,
            element=element, value=updated_step_data)

        # EXPECTED: Get the original step definition, make a copy, and combine
        # the updated data for the step
        orig_tc_data = ReferentialYAML.get_referenced_test_data(
            yaml_input=ref_yaml_obj, testsuite=self.TEST_SUITE,
            testcase=self.TEST_CASE)
        orig_tc_data = copy.deepcopy(orig_tc_data)

        expected_tc = self._combine_steps(
            original=orig_tc_data, modifications=updated_step_data[0])
        logging.info(f"Expected TC YAML:\n{pprint.pformat(expected_tc)}")

        # MODIFY the requested steps via the actual source code
        ref_yaml_obj.modify_steps()

        # ACTUAL: Get the actual testcase
        actual_tc = ReferentialYAML.get_referenced_test_data(
            yaml_input=ref_yaml_obj, testsuite=self.TEST_SUITE,
            testcase=self.TEST_CASE)
        logging.info(f"Actual TC YAML:\n{pprint.pformat(actual_tc)}")

        return expected_tc, actual_tc

    # ---------------------------------------------
    #      ORCHESTRATION (GET DATA) ROUTINES
    # ---------------------------------------------

    def _read_and_update_source_yaml_file(
            self, filename: str, testsuite: str, testcase: str,
            element: str, value: typing.Any,
            ref_yaml: ReferentialYAML = None) -> ReferentialYAML:
        """
        Read the specified file, and update the corresponding testsuite/testcase
        element with the provided value.

        Args:
            filename (str): Name of the YAML file
            testsuite (str): Testsuite to update
            testcase (str): Testcase to update
            element (str): Testcase element (dict key) to update
            value (any): Value to update the testcase element
            ref_yaml (ReferentialYAML): Populated Referential Yaml File Obj

        Returns:
            Updated ReferentialYAML Object

        """

        if ref_yaml is None:

            # Read YAML File
            data_file = get_data_file(
                test_dir_name=self.TESTS_SUBDIR,
                data_dir_name=self.DATA_SUBDIR,
                filename=filename)
            yaml_obj = YamlInputFile(input_file=data_file)

        else:
            yaml_obj = ref_yaml.yaml
            ref_yaml_obj = ref_yaml

        # Insert the MOD_STEP data to the YAML structure
        self._update_yaml(
            yaml=yaml_obj, test_suite=testsuite, test_case=testcase,
            element=element, value=value)

        # Build reference YAML object and add the data from
        # the primary reference
        if ref_yaml is None:
            ref_yaml_obj = ReferentialYAML(yaml_input=yaml_obj)
            assert_true(ref_yaml_obj.check_if_file_references_another_file())

        ref_yaml_obj._add_referenced_paths()
        logging.info(f"Updated YAML:\n{pprint.pformat(ref_yaml_obj.data)}")

        return ref_yaml_obj

    @staticmethod
    def _update_yaml(
            yaml: YamlInputFile, test_suite: str, test_case: str,
            element: str, value: typing.Any) -> None:
        """
        Provided a listed YAML structure, the testsuite and testcase, the
        attribute name to update, and the value to update the attribute to,
        find the attribute and update the structure.

        Args:
            yaml (ReferentialYAML): YAML Structure
            test_suite (str): Test suite name
            test_case (str): Test case name
            element (str): Name of test case attribute to update
            value (Any): Value or structure to update attribute to

        Returns:
            None

        """
        tc_data = ReferentialYAML.get_referenced_test_data(
            yaml_input=yaml, testsuite=test_suite, testcase=test_case)

        if element not in tc_data:
            logging.warn(f"Unable to find requested element: "
                         f"'{element}' in yaml_file")
            logging.warn(f"Test case found: {', '.join(tc_data.keys())}")
            logging.warn(f"Adding attribute '{element}' to structure.")
            logging.info(f"Inserting value: {value}")
        else:
            logging.info(f"ELEMENT: {element}")
            logging.info(f"UPDATED VALUE: {value}")

        tc_data[element] = value

        logging.info(f"Updated YAML: {pprint.pformat(yaml)}")

    @staticmethod
    def _get_testcase_steps(
            yaml_data: YamlInputFile, test_suite: str, test_case: str) -> list:

        """
        Get the list of steps within test_suite:test_case structure (yaml data)

        Args:
            yaml_data (YamlInputFile): YAML data structure
            test_suite (str): Name of test suite in data
            test_case (str): Name of test case in data

        Returns:
            (list) List of steps

        """
        # Get the test case definition
        tc_data = ReferentialYAML.get_referenced_test_data(
            yaml_input=yaml_data, testsuite=test_suite, testcase=test_case)

        logging.debug(f"TEST CASE DATA:\n{pprint.pformat(tc_data)}")

        # Get the step definitions from the test case definition
        steps = tc_data.get(YAMLConsts.STEPS, {})

        # Get the names of the steps (maintained in order)
        step_names = [list(x.keys())[0] for x in steps]
        return step_names

    @staticmethod
    def _get_testcase_ids(
            yaml_data: typing.Union[ReferentialYAML, YamlInputFile],
            test_suite: str, test_case: str) -> list:

        """
        Get the list of step ids within test_suite:test_case structure
        (yaml data)

        Args:
            yaml_data (YamlInputFile): YAML data structure
            test_suite (str): Name of test suite in data
            test_case (str): Name of test case in data

        Returns:
            (list) List of ids

        """
        # Get the test case definition
        tc_data = ReferentialYAML.get_referenced_test_data(
            yaml_input=yaml_data, testsuite=test_suite, testcase=test_case)

        logging.debug(f"TEST CASE DATA:\n{pprint.pformat(tc_data)}")

        # Get the step definitions from the test case definition
        steps = tc_data[YAMLConsts.STEPS]

        # Get the ids of the steps (maintained in order)
        step_ids = [str(list(x.values())[0][YAMLConsts.ID]) for x in steps]
        return step_ids

    @staticmethod
    def _combine_steps(original: dict, modifications: dict) -> dict:
        """
        Combine the original step definition with the requested modifications.

        Args:
            original: dictionary of original test case definition
            modifications: dictionary modifying a step within the test case

        Returns:
            Updated dictionary of test case definition

        """
        exclusions = [YAMLConsts.ID]

        original = copy.deepcopy(original)
        trigger_name, modified_data = list(modifications.items())[0]
        target_id = modified_data.get(YAMLConsts.ID)

        logging.info(f"Original Data\n{pprint.pformat(original)}")

        logging.info(f"Updating:\n{trigger_name}:\n"
                     f"{pprint.pformat(modified_data)}")

        for step in original[YAMLConsts.STEPS]:
            step_name, step_data = list(step.items())[0]
            step_id = step_data.get(YAMLConsts.ID)

            if target_id == step_id:
                logging.info(f"{trigger_name}: {step_id}\n"
                             f"{pprint.pformat(step_data)}")
                for attribute in modified_data.keys():
                    logging.info(f"CHECKING: {attribute}")
                    if attribute not in exclusions:
                        step_data[attribute] = modified_data[attribute]
                    logging.info(pprint.pformat(step_data))

        return original

    # ---------------------------------------------
    #        VALIDATION ROUTINES
    # ---------------------------------------------
    @staticmethod
    def _validate_reference_data(
            ref_info: ReferentialYAML.REFERENCE_DATA,
            ref: ReferentialYAML.REFERENCE_DATA) -> None:
        """
        Compare the functional parsed data in the NamedTuple (ref) and the
        regexp parsed data. It should be identical for all elements.

        Args:
            ref_info: Tuple of regexp parsed data
            ref: NamedTuple from ReferencedYAML routines

        Returns:
            None

        """

        attributes = ['target_test_suite', 'target_test_case', 'reference_file',
                      'reference_test_suite', 'reference_test_case']
        for attr in attributes:
            assert_equals(getattr(ref_info, attr), getattr(ref, attr))
