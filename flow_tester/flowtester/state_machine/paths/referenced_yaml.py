from collections import namedtuple
from copy import deepcopy
import os
import pprint
import typing

from flowtester.logging.logger import Logger
from flowtester.state_machine.config.constants import StateMachineConstants \
    as SMConsts
from flowtester.state_machine.config.yaml_cfg import YamlInputFile
from flowtester.state_machine.paths.path_consts import YamlPathConsts \
    as YamlConsts


logging = Logger()


# ==============================================
#    EXCEPTION CLASSES
# ==============================================
class UndefinedStep(Exception):
    pass


class UndefinedId(Exception):
    pass


class StepIdExists(Exception):
    pass


class ReferenceParseError(Exception):
    pass


class MissingIdLandmark(Exception):
    pass


# ==============================================
#    PRIMARY CLASS FOR MODULE
# ==============================================
class ReferentialYAML:

    """
    This class checks the YAML Input file for references to other YAML files.
    If the references are found, the class will retrieve the referenced file,
    get the specific TestSuite/TestCase reference, validate that the step IDs
    [1] are correct for the given actions (ADD, DELETE, MODIFY), and will
    insert the updated YAML structure into the current file.

    [1] Validations:
    For ADD:
      * Verify the IDs are unique between the added IDs and between the
        referenced model.
      * Verify landmark key is specified (BEFORE_ID, AFTER_ID) and that the ID
        specified is defined in the referenced model.

    For MODIFY:
      * Verify the ID exists in the referenced model.

    For DELETE:
      * Verify the ID exists in the referenced model.

    Notes:
        The module is organized so that the primary routines are defined in the
        file and then sections for the data retrieval and validation are defined

    """

    DELIMITER = ":"
    REFERENCE_DATA = namedtuple(
        'CfgFileRef',
        'target_test_suite '
        'target_test_case '
        'reference_file '
        'reference_test_suite '
        'reference_test_case')

    def __init__(self, yaml_input: YamlInputFile):
        self.yaml = yaml_input
        self.cfg_file_path = os.path.sep.join(
            self.yaml.input_file.split(os.path.sep)[:-1])
        self.input_file = self.yaml.input_file
        self.data = self.yaml.data
        self.references = list()

    def evaluate_yaml_file(self) -> typing.List[dict]:
        """
        Check if input YAML file references another YAML file. Is so,
        added referenced file and add, update, and delete test info as
        specified in the input YAML file.

        Returns:
           Fully updated YAML data file (list of dictionaries).

        """

        # If references another Yaml file, update the YAML structure accordingly
        if self.check_if_file_references_another_file():
            self._add_referenced_paths()

            self.add_steps()
            self.modify_steps()
            self.delete_steps()

            logging.debug(f"UPDATED:\n{pprint.pformat(self.yaml.data)}")

        return self.data

    def check_if_file_references_another_file(self) -> bool:
        """
        Check for reference key within each test case defined in the provided
        YAML file.
        If found, store (target testsuite, target testcase, file reference)
        in self.references.

        Returns:
            (bool) - True: Reference found

        """
        references_found = False

        for test_suite_data in self.data:

            # Get test suite name & data
            test_suite = list(test_suite_data.keys())[0]
            test_case_data = test_suite_data[test_suite]

            logging.debug(f"Data:\n{test_suite_data}")
            logging.debug(f"TS: {test_suite}")

            # Iterate through each test case and check for a reference key
            for test_case, tc_data in test_case_data.items():
                ref_file, ref_ts, ref_tc = reference_info = ('', '', '')
                logging.debug(f"TC: {test_case}")

                # Check for reference key
                reference_found = SMConsts.REFERENCE in tc_data.keys()

                # If found, parse and store in NamedTuple and append to list
                # of references
                value_error = False
                if reference_found:
                    try:
                        reference_info = tc_data.get(SMConsts.REFERENCE).split(
                            self.DELIMITER)
                        reference_info = [x.strip() for x in reference_info]
                        ref_file, ref_ts, ref_tc = reference_info
                    except ValueError:
                        value_error = True

                    if value_error or '' in reference_info:
                        msg = (f"\nCfg File:   {self.yaml.input_file}\n"
                               f"Test Suite: {test_suite}\n"
                               f"Test Case:  {test_case}\n"
                               f"Unable to split '"
                               f"{tc_data.get(SMConsts.REFERENCE)}' using "
                               f"delimiter '{self.DELIMITER}'")

                        logging.error(msg)
                        raise ReferenceParseError(msg)

                    self.references.append(self.REFERENCE_DATA(
                        target_test_suite=test_suite,
                        target_test_case=test_case,
                        reference_file=ref_file,
                        reference_test_suite=ref_ts,
                        reference_test_case=ref_tc))

                # Tally result
                references_found = references_found or reference_found

        return references_found

    def add_steps(self) -> None:
        """
        Process each path set that references an external file. If that the
        path set contains a ADD_STEPS section (list of step IDs), add those
        steps.

        Returns: None

        """
        for ref in self.references:
            logging.debug(f"Processing TS: {ref.target_test_suite}  "
                          f"TC: {ref.target_test_case}")

            ts = [ts_data for ts_name, ts_data in self.yaml.data[0].items()
                  if ts_name == ref.target_test_suite]
            tc = ts[0][ref.target_test_case]

            # Get the steps to be added.
            # --------------------------------
            # If the key is not defined, return an empty list.
            add_steps = tc.get(YamlConsts.ADD_STEPS, [])

            # If the key is defined, but no value is set, so
            # add_steps will be None so reset add_steps to []
            add_steps = add_steps or []

            # Verify all steps to be added are not defined in the reference path
            # if this is not the case, _verify_add_ids_do_not_exist() will
            # throw an exception.
            add_step_ids = [y.get(YamlConsts.ID) for x in add_steps for y
                            in x.values()]

            # Get all IDs associated with the landmark (BEFORE_ID/AFTER_ID)
            landmark_ids = []
            for landmark in [YamlConsts.BEFORE_ID, YamlConsts.AFTER_ID]:
                landmark_ids += [y.get(landmark) for x in add_steps for y
                                 in x.values() if landmark in y]
            landmark_ids = list(set(landmark_ids))

            # Log all calculated/collected data
            logging.debug(f"ADD STEPS:\n{pprint.pformat(add_steps)}")
            logging.debug(f"STEP IDs TO BE ADDED: {', '.join(add_step_ids)}")
            logging.debug(f"UNIQUE LANDMARK IDs: {', '.join(landmark_ids)}")

            # Get the current mapping
            mapping = self._build_id_map(tc_def_dict=tc)

            # Verify IDs to be added do not exist
            self._verify_add_ids_do_not_exist(
                ts=ref.target_test_suite, tc=ref.target_test_case,
                mapping=mapping, ids_to_be_added=add_step_ids)

            # Verify Landmark IDs + "IDs to be added" used as reference points
            # exist
            possible_ids = list(mapping.keys())
            possible_ids.extend(add_step_ids)
            self._verify_target_ids_exist(
                ts=ref.target_test_suite, tc=ref.target_test_case,
                mappings=possible_ids, target_ids=landmark_ids)

            # Insert the new steps
            for target_step in add_steps:

                # Get a list of the ids to list index mapping
                logging.debug(f"Target Step Definition to be added:\n"
                              f"{target_step}")
                target_step_name = list(target_step.keys())[0]
                target_step_data = list(target_step.values())[0]

                # Get target landmark (before/after) and step id
                landmark, target_id = self._get_target_landmark(
                    tc_name=target_step_name, tc_data=target_step_data,
                    tc_ref=ref)

                # Get the landmarked step's index and increment to get
                # targeted list index
                target_id_index = mapping[str(target_id)]
                if landmark == YamlConsts.AFTER_ID:
                    target_id_index += 1

                # Copy the step definition to be inserted, and
                # delete the landmark key from the definition.
                step_def = deepcopy(target_step_data)
                del step_def[landmark]

                # Insert the step into the list at the target index
                tc[YamlConsts.STEPS].insert(
                    target_id_index, {target_step_name: step_def})

                # Regenerate the index dictionary based on the latest update
                mapping = self._build_id_map(tc_def_dict=tc)

            # Log results of operation
            logging.debug(f"Updated Test Case:\n{pprint.pformat(tc)}")

    def delete_steps(self):
        """
        Process each path set that references an external file.
        If that the path set contains a DEL_STEPS section (list of step IDs),
        remove those steps.

        Returns: None

        """
        for ref in self.references:
            logging.debug(f"Processing TS: {ref.target_test_suite}  "
                          f"TC: {ref.target_test_case}")

            # Get the test case and test step information
            ts = [ts_data for ts_name, ts_data in self.yaml.data[0].items()
                  if ts_name == ref.target_test_suite]
            tc = ts[0][ref.target_test_case]

            # Get a list of the ids to list index mapping
            mapping = self._build_id_map(tc_def_dict=tc)

            # Get the list of UNIQUE steps to be deleted.
            # --------------------------------------------
            # If the key is not defined, return an empty list.
            del_steps = list(set(tc.get(YamlConsts.DEL_STEPS, [])))

            # If the key is defined, but no value is set, del_steps will be
            # None, so reset to []
            del_steps = del_steps or []

            # Verify all steps to be deleted are defined in the reference path
            # if this is not the case, _verify_del_id_exist will throw an
            # exception
            self._verify_del_or_mod_ids_exist(
                ts=ref.target_test_suite, tc=ref.target_test_case,
                mapping=mapping, ids_to_be_updated=del_steps)

            # Get the index order in reverse order, so each step can be
            # deleted without impacting the index of the other elements
            # to be deleted
            to_delete_list = sorted([mapping[id_] for id_ in del_steps],
                                    reverse=True)
            logging.debug(f"Indices to delete: {to_delete_list}")

            # Delete the steps (using list.pop() so we can log the step
            # being deleted)
            for target_index in to_delete_list:
                item = tc[YamlConsts.STEPS].pop(target_index)
                logging.debug(f"Removed item {target_index}:\n{item}")

            # Log results of operation
            logging.debug(f"Updated Test Case:\n{pprint.pformat(tc)}")

    def modify_steps(self):
        """
        Process each path set that references an external file. If that the
        path set contains a MOD_STEPS section (list of step IDs and
        definitions), update those steps based on the reference steps.

        Returns:
            None

        """
        for ref in self.references:
            logging.debug(f"Processing TS: {ref.target_test_suite}  "
                          f"TC: {ref.target_test_case}")

            ts = [ts_data for ts_name, ts_data in self.yaml.data[0].items()
                  if ts_name == ref.target_test_suite]
            tc = ts[0][ref.target_test_case]

            # Get the steps to be updated.
            # --------------------------------
            # If the key is not defined, return an empty list.
            mod_steps = tc.get(YamlConsts.MOD_STEPS, [])

            # If the key is defined, but no value is set, so
            # mod_steps will be None so reset mod_steps to []
            mod_steps = mod_steps or []

            # Verify all steps to be modified are defined in the
            # reference path
            mod_step_ids = [str(y.get(YamlConsts.ID)) for x in mod_steps for y
                            in x.values()]

            # Log all calculated/collected data
            logging.debug(f"MODIFY STEPS:\n{pprint.pformat(mod_steps)}")
            logging.debug(f"STEP IDs TO BE ADDED: {', '.join(mod_step_ids)}")

            # Get the current mapping
            mapping = self._build_id_map(tc_def_dict=tc)

            # Verify Landmark IDs to be used as reference points do exist
            self._verify_target_ids_exist(
                ts=ref.target_test_suite, tc=ref.target_test_case,
                mappings=list(mapping.keys()),
                target_ids=mod_step_ids)

            # Insert the new steps
            for target_step in mod_steps:

                # Get a list of the ids to list index mapping
                logging.debug(f"Target Step Definition to be modified:"
                              f"\n{pprint.pformat(target_step)}")
                target_step_data = list(target_step.values())[0]
                target_id = str(target_step_data.get(YamlConsts.ID))

                # Get the target step's index
                target_id_index = mapping.get(target_id)

                # Copy the step definition to be inserted, and
                # delete the landmark key.
                step_def = deepcopy(target_step_data)

                valid, trigger_name = self._validate_trigger_names_match(
                    ts=ref.target_test_suite, tc=ref.target_test_case,
                    mapping=mapping, reference_tc=tc, mod_data=target_step)

                if not valid:
                    logging.warn(f"Using reference "
                                 f"target name: {trigger_name} "
                                 f"(list index: {target_id_index})")

                # Insert the step into the list
                tc[YamlConsts.STEPS][target_id_index].update(
                    {trigger_name: step_def})

            # Log results of operation
            logging.debug(f"Updated Test Case:\n{pprint.pformat(tc)}")

    def add_referenced_tc_to_ts(
            self, target_ts: str, target_tc: str, tc_data: dict):
        """
        Find the correct TS/TC in the current data set, and update
        the dictionary with the steps listed from the included data.

        Args:
            target_ts (str): Name of target test suite
            target_tc (str): Name of target test case
            tc_data (dict): TC step definition to update the test case

        Returns:
            None

        """

        # Attributes to overwrite from referenced test case
        tc_attributes = [YamlConsts.STEPS]

        # Check each test suite for matching target_ts
        for test_suite in self.yaml.data:
            if target_ts in test_suite.keys():

                # TS found, find TC. Initialize if necessary
                if target_tc not in test_suite[target_ts].keys():
                    test_suite[target_ts][target_tc] = {}

                # Update the provided attributes
                for tc_attr in tc_attributes:

                    # Update the given attribute if present
                    if tc_attr in tc_data:
                        test_suite[target_ts][target_tc].update(
                            {tc_attr: tc_data.get(tc_attr)})

    # ==============================================
    #    DATA RETRIEVAL ROUTINES
    # ==============================================

    @staticmethod
    def _build_id_map(tc_def_dict: dict) -> dict:
        """
        Routine to map path/test step IDs to their index in the path list.

        Args:
            tc_def_dict: Dictionary defining the testcase.

        Returns:
            (dict) step_id: list_index

        """
        id_to_step_mapping = {}

        # Get the list of steps (in list order)
        steps = tc_def_dict[YamlConsts.STEPS]

        # Store the step id and the element index
        for index, step_def_dict in enumerate(steps):
            step_id = str(list(step_def_dict.values())[0][YamlConsts.ID])
            id_to_step_mapping[step_id] = index

        logging.debug(pprint.pformat(id_to_step_mapping))

        return id_to_step_mapping

    @staticmethod
    def _get_target_landmark(
            tc_name: str, tc_data: dict, tc_ref: REFERENCE_DATA) -> tuple:
        """
        Parse the testcase data to determine the landmark (previous, next) and
        the id to use with the landmark.

        Notes:
            If 'before' and 'after' are both specified, the AFTER will the
            last point referenced and will be the landmark used.

        Args:
            tc_name: Test case name
            tc_data: Test case data
            tc_ref: Test case reference

        Returns:
            (str, str): Landmark, step_id for landmark
        """
        target_id = None
        landmark = None

        # ------------------------------ NOTE ------------------------------
        # Determines order for processing. If both landmarks are specified,
        # the last element will be the element that is "honored".
        # ------------------------------------------------------------------
        positions = [YamlConsts.BEFORE_ID, YamlConsts.AFTER_ID]

        # Find and store the landmark and the associated ID
        for landmark_key in positions:
            if landmark_key in tc_data:
                target_id = tc_data.get(landmark_key)
                landmark = landmark_key

        if target_id is None:
            raise MissingIdLandmark(
                f"\nTS: {tc_ref.target_test_suite}"
                f"\nTC: {tc_ref.target_test_case}"
                f"\nAdding {tc_name}: Missing ID Landmark "
                f"({', '.join(positions)})")

        logging.debug(f"Target Step Location: {landmark}:{target_id}")
        return landmark, target_id

    def _add_referenced_paths(self) -> None:
        """
        Given a list of referenced files via CfgFileReferences named tuple,
        find the referenced data and store it in the current test suite
        definition.

        Returns:
            None

        """
        # Get references for each test case identified
        for ref in self.references:

            # Location in data structure to add updated data
            target_ts = ref.target_test_suite
            target_tc = ref.target_test_case
            ref_ts = ref.reference_test_suite
            ref_tc = ref.reference_test_case

            # Get referenced YAML config file
            referenced_file = os.path.sep.join(
                [self.cfg_file_path, ref.reference_file])

            reference_data = YamlInputFile(referenced_file)
            logging.debug(f"RAW DATA:\n{pprint.pformat(reference_data.data)}")

            tc_data = self.get_referenced_test_data(
                yaml_input=reference_data, testsuite=ref_ts, testcase=ref_tc)
            logging.debug(f"Testcase data for TS: '{ref_ts}' TC: '{ref_tc}' "
                          f"in FILE: '{referenced_file}'"
                          f"\n{pprint.pformat(tc_data)}")

            self.add_referenced_tc_to_ts(target_ts, target_tc, tc_data)

    @staticmethod
    def get_referenced_test_data(
            yaml_input: typing.Union[YamlInputFile, "ReferentialYAML"],
            testsuite: str, testcase: str) -> dict:
        """
        Search the YAML generated data structure for the testsuite and testcase.
        If found, return the corresponding dictionary.

        Args:
            yaml_input (YamlInputFile): The parsed YAML file (already read into
                memory)
            testsuite (str): Name of testsuite
            testcase (str): Name of testcase

        Returns:
            Dictionary of the test case definition.
            If testcase is not found, empty dict.

        """
        # Iterate through read-in file searching for testsuite/testcase.
        target_ts_data = {}
        for test_suite_data in yaml_input.data:
            if testsuite in test_suite_data.keys():
                target_ts_data = test_suite_data.get(testsuite, {})

        # Didn't find the requested testsuite.
        if not target_ts_data:
            logging.error(f"Requested testsuite not found in FILE: "
                          f"{yaml_input.input_file}")
            return target_ts_data

        # Testsuite found.
        logging.debug(f"SUCCESS: Found TS: {testsuite} "
                      f"in FILE: {yaml_input.input_file}")

        # Get the testcase data
        testcase_data = target_ts_data.get(testcase, {})

        # Didn't find the requested testcase in the testsuite
        if not testcase_data:
            logging.error(f"Requested test case \"{testcase}\" not found in "
                          f"testsuite: \"{testsuite}\" "
                          f"in FILE: {yaml_input.input_file}")

        # Testcase found.
        else:
            logging.debug(f"SUCCESS: Found TC: \"{testcase}\" "
                          f"in TS: \"{testsuite}\" "
                          f"in FILE: {yaml_input.input_file}")

        # Return the testcase definition
        return testcase_data

    # ==============================================
    #    VALIDATION ROUTINES
    # ==============================================

    def _verify_add_ids_do_not_exist(
            self, ts: str, tc: str, mapping: dict,
            ids_to_be_added: list) -> bool:
        """
        Verify all ids to be added are not already defined as steps in the path
        Args:
            ts (str): Name of Testsuite (reported for errors)
            tc (str): Name of Testcase (reported for errors)
            mapping (dict): Dictionary of "ids" to list indices
            ids_to_be_added (list): List of ids to be added

        Returns:
            True if all ids are unique (not defined in reference path or
            duplicated in to_be_added list)

        Raises:
            StepExists if IDs to be added is already defined in the testcase

        """
        # Convert all lists to sets
        known_ids = set(mapping.keys())
        ids_to_be_added_set = set(ids_to_be_added)

        # Check to make sure there are no duplicates between the added IDs
        if len(ids_to_be_added_set) != len(ids_to_be_added):
            msg = (f"\nCfg File:   {self.yaml.input_file}\n"
                   f"Test Suite: {ts}\n"
                   f"Test Case:  {tc} --> IDs to be added that are duplicated "
                   f"in specification: {', '.join(ids_to_be_added)}")
            logging.error(msg)
            raise StepIdExists(msg)

        logging.debug(f"KNOWN IDS: {', '.join([str(x) for x in known_ids])}")
        logging.debug(f"TO ADD: "
                      f"{', '.join([str(x) for x in ids_to_be_added_set])}")

        # Find the intersection and compare to the list to be added.
        # The lists should be unique, so there cannot be an intersection.
        common = ids_to_be_added_set & known_ids

        if common:
            msg = (f"\nCfg File:   {self.yaml.input_file}\n"
                   f"Test Suite: {ts}\n"
                   f"Test Case:  {tc} --> IDs to be added that are already "
                   f"defined in referenced path: {', '.join(common)}")
            logging.error(msg)
            raise StepIdExists(msg)

        return True

    def _verify_del_or_mod_ids_exist(
            self, ts: str, tc: str, mapping: dict,
            ids_to_be_updated: list) -> bool:
        """
        Verify all ids to be modified/deleted are defined as steps in the path
        Args:
            ts (str): Name of Testsuite (reported for errors)
            tc (str): Name of Testcase (reported for errors)
            mapping (dict): Dictionary of "ids" to list indices
            ids_to_be_updated (list): List of ids to be updated or deleted

        Returns:
            True if all ids are known (defined)

        Raises:
            UndefinedStep if IDs to be updated/deleted are not defined in
            the testcase (path)

        """
        # Convert all lists to sets
        known_ids = set(mapping.keys())
        ids_to_be_updated = set(ids_to_be_updated)

        logging.debug(f"KNOWN IDS: {', '.join([str(x) for x in known_ids])}")
        logging.debug(f"TO MODIFY/DELETE: "
                      f"{', '.join([str(x) for x in ids_to_be_updated])}")

        # Find the intersection and compare to the list to be updated.
        # Intersection should match all ids to update. If the intersection is
        # not the same as the update list, there is an id in the update list
        # that is not defined in the path.
        diff = (ids_to_be_updated & known_ids) ^ ids_to_be_updated

        if diff:
            msg = (f"\nCfg File:   {self.yaml.input_file}\n"
                   f"Test Suite: {ts}\n"
                   f"Test Case:  {tc}\n"
                   "IDs to be modified/deleted that are not defined in "
                   f"the referenced path: {', '.join(diff)}")
            logging.error(msg)
            raise UndefinedStep(msg)

        logging.debug("All ids to be modified or deleted are defined "
                      "in the reference model")
        return True

    def _verify_target_ids_exist(
            self, ts: str, tc: str, mappings: list, target_ids: list) -> bool:
        """
        Verify all landmark IDs are defined in the reference model.
        Args:
            ts (str): Test suite name
            tc (str): Test case name
            mappings (list): List of all defined ids
            target_ids (list): List of all IDs to be used as landmarks

        Returns: True if all ids are known (defined)

        Raises:
            UndefinedStep if IDs to be updated/deleted are not defined in the
            testcase (path)

        """
        # Convert lists to sets of strings for qualitative comparison
        known_ids_set = set([str(x) for x in mappings])
        target_ids_set = set([str(x) for x in target_ids])

        logging.debug(f"KNOWN IDS: "
                      f"{', '.join([str(x) for x in known_ids_set])}")
        logging.debug(f"VALIDATING EXISTENCE: "
                      f"{', '.join([str(x) for x in target_ids_set])}")

        # Are there any target ids that are not in the known ids?
        diff = target_ids_set.difference(known_ids_set)

        if diff:
            msg = (f"\nCfg File:   {self.yaml.input_file}\n"
                   f"Test Suite: {ts}\n"
                   f"Test Case:  {tc}\n"
                   "Target IDs to add/modify are not defined in "
                   f"the referenced path: {', '.join(diff)}")
            logging.error(msg)
            raise UndefinedId(msg)

        # If you get to here, everything is ok!
        logging.debug("All target IDs are defined in the reference model.")
        return True

    def _validate_trigger_names_match(
            self, ts: str, tc: str, mapping: dict, reference_tc: dict,
            mod_data: dict) -> typing.Tuple[bool, str]:
        """
        Verify modified step trigger name matches the referenced trigger name.

        Args:
            ts (str): Test suite name
            tc (str): Test case name
            mapping (dict): Dictionary of all defined ids (and index in list)
            reference_tc (dict): Reference Testcase definition
            mod_data (dict): Definition of modified trigger data

        Returns: Tuple (bool: trigger names match, str: trigger name to use)

        """
        # Get the modified definition's trigger name

        target_trigger_name = list(mod_data.keys())[0]

        target_id = str(mod_data[target_trigger_name][YamlConsts.ID])
        step_index = mapping[target_id]
        reference_tc_name = list(
            reference_tc[YamlConsts.STEPS][step_index].keys())[0]

        if target_trigger_name != reference_tc_name:
            msg = (f"\n\tTarget Trigger does not match the defined "
                   f"trigger name:\n"
                   f"\tModified Trigger Name: {target_trigger_name}\n"
                   f"\tDefined Trigger Name:  {reference_tc_name}\n"
                   f"\tCfg File:   {self.yaml.input_file}\n"
                   f"\tTest Suite: {ts}\n"
                   f"\tTest Case:  {tc}")

            logging.warn(msg)
            logging.warn(f"Defaulting to reference trigger name: "
                         f"{reference_tc_name}")
            result = False
            target_trigger_name = reference_tc_name

        # If you get to here, everything is ok!
        else:
            logging.debug("SUCCESS: Modified trigger definition name matches "
                          "the trigger name in the reference model.")
            result = True

        return result, target_trigger_name


# ==============================================
#    INTERNAL TESTING PURPOSES ONLY
# ==============================================


if __name__ == '__main__':  # pragma: no cover

    filename = ('/Users/robe6162/code/sales/FlowTester/src/'
                'FlowTester/cfgs/paths_relative.yaml')
    yaml = YamlInputFile(filename)
    ref_yaml = ReferentialYAML(yaml)
    logging.info(f"ORIGINAL:\n{pprint.pformat(ref_yaml.yaml.data)}")
    data = ref_yaml.evaluate_yaml_file()
    logging.info(f"UPDATED:\n{pprint.pformat(data)}")

    # TODO: Add logic for nested referenced files
