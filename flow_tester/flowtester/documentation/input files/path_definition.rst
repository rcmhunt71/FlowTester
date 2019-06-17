===========================
Path Definition Input File
===========================

The Path definition file is one of two required input YAML files for the flow tester (the other being the state machine definition file). The path definition file defines a test case by specifying the series of data, expectations, and triggers to execute in the order specified.

There are two basic types of path definition files\: **complete** and **inherited**. A Complete definition contains a complete path and is a stand-alone file (no external dependencies). Inherited files reference a complete file and define the modifications to make to the path (additions, updates, and deletions).

----------------------------
Complete Definition Files
----------------------------

Complete definition YAML files contain all data and triggers to execute test within the State Machine. (For an example, refer to the ``cfgs`` directory in root of the repo. The file uses the YAML format with the following fields:

Test Suite
************
The testsuite is the outermost key in the YAML dictionary, and provides a simple description of the test cases contained within. ::

 - <TEST_SUITE>
    - <TEST_CASE_1>
       <...>
    - <TEST_CASE_2>
       <...>

Test Case
*************
A test case is a complete description of a traversal path through the state machine. It is defined as a secondary key under the Test Suite. ::

 - <TEST_SUITE>:
    - <TEST_CASE_1>:
        <...>
    - <TEST_CASE_2>:
        <...>

Test cases have a series of defined keys & values as its definition.

Description
-------------
The description is a string describing the test case/path. It is not limited in size, so it can sentence or paragraph describing the intent of the test case. ::

 - <TEST_SUITE>:
    - <TEST_CASE_1>:
        description: <description text>
        
Steps
---------------
The steps are the **ordered** list of triggers to traverse a path through the state machine. ::

 - <TEST_SUITE>:
    - <TEST_CASE_1>:
        description: <description text>
        steps:
          - <TRIGGER_1>
            <...>
          - <TRIGGER_2>
            <...>
          - <TRIGGER_3>
            <...>

The trigger names are taken directly from the state machine definition - **the path is very tightly coupled to the state machine**. If a step is not recognized, the test case will not execute; this is validated as a static check when the state machine and path file are read from file.

Steps have series of fields that provide the contextual information required to execute the trigger and the capability to set expectations if the validation to the next state is correct. (See expectations below).

Each step is comprised of:

* the trigger name
* a unique id
* data for the trigger (optional)
* expectations (optional)

Example of a step definition: ::

 steps:
   -<TRIGGER NAME>:
     id: <unique id>
     data: <python dictionary of data>
     expectations:
        <validation id>: <boolean expectation>

Id
================
The ``id`` is a unique identifier within the steps; every step requires an id. The id is not required for execution, but used by the inherited definition to identify a specific step, since triggers can be repeated within a single path. The id allows the correct insertion, deletion, or modification of a step.


The id can be any string or number of any format (e.g. - UUID, descriptive text, index, etc.).

Examples: ::

   id: create_entity
   id: step_3
   id: 3ffe-677ea3210-ffe4-772ae127

Data
==============
Data is a dictionary specifying the keyword arguments to pass into the trigger, **if the trigger** requires data. Each data dictionary is specific to the keyword arguments of the given trigger, as defined in the state machine definition (``routine_to_change_state: object_model.routine_to_execute_trigger``). ::

    data:
      create: True
      metadata:
         key_1: value_1
         key_2: value_2
      name: Example data
     
Expectations
===============
The expectations allow a test case to specify certain the expected boolean response to the defined state validations. In the state machine definition, each state can have a series of validations, each of which return a boolean indicating success or failure. These validations are defined with a descriptive keyword and the name of a routine to generate a callback to execute.

The expectations are dictionary of the specific keywords and the expected response. If a validation is not listed in the expectations, the step defaults to assuming the validation will return True. ::

    validations:
      - exists: False
      - active: False
      - connected: True   <<--- This is optional, since if a validation is not listed, it will expect a default response of True.

---------------------------------------
Inherited Definition Files
---------------------------------------
Inherited definition files will take an existing definition file and add, modify, or remove steps. An inherited file may reference another inherited file which may reference another inherited file which may reference a complete path file (**not implemented yet**).

* **Recommendation**: Keep the length of the inheritance chain to a minimal length (once implemented), otherwise it will very difficult to understand what the test case is doing. There will be a *utility* that will combine the referenced files and base file for a single path into a one YAML structure and generate a base path YAML file. The intent is to provide a complete listing of the path allowing a description of what the final path looks like.

The inherited file will have the <TEST_SUITE> and <TEST_CASE> keys, and under the test case, it will have a ``description`` key, but will have some additional fields.

Reference File
****************
The reference file indicates what base file or parent reference file to update. The value should be another file, with the path, **relative to the current file**. The test suite and test case should be attached as comma-delimited values. 

Adding Steps
****************
To add a step, the "landmark" step ID needs to be provided, either identified as the preceding or next ID.

**before_id**: The step to be added will be inserted before the listed step id.

**after_id**: The step to be added will be inserted AFTER the listed step id.

If the both the "before" id and the "after" id are specified, the ``before`` id data will take precedence. ::

  - <TEST_SUITE>:
     - <TEST_CASE_1>:
         description: <description text>
         reference: <relative path to reference YAML file>:TestSuite:TestCase
         steps_to_add:
            - ID_8:
                after_id: ID_7
                trigger: <trigger_name>
                data: {}
                expectations: {}
            - ID_NEW:
                before_id: 3ffe-677ea3210-ffe4-772ae127
                trigger: <trigger_name>
                data:
                   create: False
                   admin: <credentials>
                expectations: {}
            - ID_11:
                before_id: ID_10
                after_id: ID_100
                trigger: <trigger_name>
                data:
                   create: False
                   admin: <credentials>
                expectations: {}
              
Deleting Steps
****************
For deleting a step, the only information required is the target step's unique id. The YAML will contain a list of IDs of steps to delete. ::


  - <TEST_SUITE>:
     - <TEST_CASE_1>:
         description: <description text>
         reference: <relative path to reference YAML file>\:TestSuite\:TestCase
         steps_to_delete:
            - ID_1
            - ID_3
            - ID_7

Modifying Steps
****************
For updating/modifying steps, the specific step ID will be referenced and the step fields to be updated (with updated data) will be defined. ::

  - <TEST_SUITE>:
     - <TEST_CASE_1>:
         description: <description text>
         reference: <relative path to reference YAML file>
         steps_to_update:
            - ID_2:
                data: {}
                expectations: {}
            - ID_5:
                data:
                   create: True
                   metadata:
                      key_1: value_1
                      key_2: value_2
                   name: Example data
                expectations:
                   deleted: False
                   
NOTE: All fields **except** the trigger name and the step ID can be modified.
