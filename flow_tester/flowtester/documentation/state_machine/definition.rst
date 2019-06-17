=================================
Defining The State Machine Model
=================================

The process of defining a state machine was intended to be simple, easy-to-read, and iterative; ``iterative`` meaning start with a simple system definition and continue to improve as more information is collected or as the product is enhanced.

**Format of State Machine Definition**:

The state machine definition uses a YAML file to define the various structures, definitions, and data. Each file contains a single model.

An example of a fully defined state machine model can be found in the repo: *<root_repo_directory>/cfgs/VM.yaml*.

----------------------------------------------------------------

--------------------------------
Preamble
--------------------------------
This is metadata that is used to identify the basic model. There are 3 fields:

**model**:

   This is the name of the model, e.g. - Raptor_AR, QM_QA_WorkFlow, PricingEngine.

   *Format*: A simple, descriptive string to name the model.


**description**:

   A descriptive "blurb" explaining the purpose, requirements, assumptions, etc. This string is purely for user information and is not used by the state machine in any functional way.

   *Format*: String (no limitation on character type or length).

**initial_state**:

   Every model needs an entry point into the state machine. This attribute specifies which state should be an entry point. **NOTE**: The initial state is validated against the defined states to make sure the state is defined prior to state machine execution.

   *Format*: String (name of the defined state to start state machine evaluation)

**EXAMPLE**: ::

     model: Test_State_Machine
     description: "This is a test state machine for testing a system."
     initial_state: START


----------------------------------------------------------------


--------------------------------
State Declarations
--------------------------------
There are two aspects to defining the state machine: *the specific definition* of each state and the *inclusion* of the state into the overall model definition.


************************************
Individual State Definition Format
************************************
Each state definition has several fields that are required.

**State Name**:

   This is a **CASE_SENSITIVE** single word name use to identify/describe the state. It must be **unique** to the model and any references to this state within the definition *must* match the state name. For a *complete* example, please refer to the end of this section.

   The name:

   * is a single word string; no spaces, instead use underscores '_'.
   * cannot start with a double underscore ( __ ); the double underscore is a reserved character sequence for identifying special state machine definitions. See the `Special Definitions`_  section for more details.

**Description**:

   This is a text string used to describe the state. It is used to explain the state to users in both the YAML file and is used in some execution reports to clarify what is expected in the workflow.

+++++++++++++++++++++++++++++++++++++
Validations:
+++++++++++++++++++++++++++++++++++++

   When the state machine transitions into the given state, the state machine will execute a list of validation APIs to make sure the system is in the expected state. The validations are defined as a "list of dictionaries" defining each validation name/id and routine:

   *Format*: ::

     - name: unique identification string
     - routine: dotted-path notation of validation routine.


   **name**: The name should be a unique, single word (or underscored) string used to label the specific callback. This allows users to reference a specific validation routine to set expectations or pass additional data to the validation callback.

   **routine**: The routine should be a dotted path of the validation routine to execute. The routine is should be readily referencable (e.g. - a method of an already instantiated object or imported library).

   **EXAMPLE**: ::

     validations:
       - name: check_if_server_exists
         routine: object_model.server.validations.does_server_exist
       - name: is_server_online
         routine: object_model.server.validations.is_server_online

   The validation callback routines, *as currently implemented*, **must** return a boolean value (True || False). Each callback response is logically **AND'ed** together so that the overall result will indicate if the validation routines collectively passed or failed. Each individual validation result is also tracked for reporting the detailed validation results.

+++++++++++++++++++++++++++++++++++++
Transitions:
+++++++++++++++++++++++++++++++++++++
  Also commonly referred to as *triggers*, the transitions definitions are the core of the state machine definition. Transitions are method calls (callbacks) that can be invoked to change from the current state to other various states or even back to the current state: a reflexive transition. All states that are not terminal states required triggers; a terminal state, by definition, is a state that does not have any triggers, so that once that state is reached, the state machine is unable to exit that state.

  **trigger_name**:

    The trigger name is a simple single word string describing the action or transition. *Recommendation*: the trigger name should be a verb; using a verb makes more intuitive sense when describing the state machine path since the trigger is an action causing a state change.

  **destination_state**:
    The destination state is a state that the state machine should transition after the execution of the given trigger. Prior to starting the execution, the state machine will validate all destination states to verify the states is valid and correctly defined. When the destination state is reached, the state machine will execute that destination state's validation routines to verify the state of the system is correct.

  **routine_to_change_state**:
    The routine should be a dotted path of the transition routine to execute. The routine is should be readily referencable (e.g. - a method of an already instantiated object or imported library).

  **EXAMPLE**: ::

      transitions:
      - routine_to_change_state: object_model.pause_server
        destination_state: PAUSED
        trigger_name: PAUSE

      - routine_to_change_state: object_model.lock_server
        destination_state: LOCKED
        trigger_name: LOCK

      - routine_to_change_state: object_model.delete_server
        destination_state: DELETING
        trigger_name: DELETE

+++++++++++++++++++++++++++++++++++++
Putting It All Together
+++++++++++++++++++++++++++++++++++++
All of the sections described above, when put together, defines a state.

**EXAMPLE**:  ::

 - ACTIVE:
    description: "STATE: Server is in ACTIVE state."
    validations:
    - name: active
      routine:  object_model.is_server_active
    - name: test_me
      routine: object_model.no_such_function

    transitions:
    - routine_to_change_state: object_model.pause_server
      destination_state: PAUSED
      trigger_name: PAUSE
    - routine_to_change_state: object_model.lock_server
      destination_state: LOCKED
      trigger_name: LOCK
    - routine_to_change_state: object_model.delete_server
      destination_state: DELETING
      trigger_name: DELETE


----------------------------------------------------------------


********************************
Model State Definitions
********************************

The `Individual State Definition Format`_ section described how to define a single state; this section will quickly describe how to assemble the states into a format that will be read by the flow tester.

* All state names need to be unique.
* Each state definition is a dictionary.
* All states in the **definition** section are combined into a list.

**EXAMPLE**: ::

 model: SAMPLE_VM
 description: "A sample state machine definition for a VM."
 initial_state: DOES_NOT_EXIST
 definition:

 - DOES_NOT_EXIST:
     description: "Base State: VM does not exist"
     validations:
     - name: existence
       routine: object_model.does_server_exist

     transitions:
     - routine_to_change_state: object_model.create_server
       destination_state: BUILDING
       trigger_name: CREATE

 - BUILDING:
     description: "STATE: Server is being provisioned (building)."
     validations:
     - name: building
       routine: object_model.building_server

     transitions:
     - routine_to_change_state: object_model.building_server
       destination_state: ACTIVE
       trigger_name: BUILD_SUCCESS
     - routine_to_change_state: object_model.building_server_fail
       destination_state: ERROR
       trigger_name: BUILD_FAILURE

 - ERROR:
     description: "STATE: Server is in ERROR state. Terminal State."
     validations:
     - name: in_error
       routine: object_model.is_server_in_error


----------------------------------------------------------------


--------------------------------
Special Definitions
--------------------------------

There are special definitions used to simplify the state machine definition. These special definitions should be **prefixed and suffixed** with a double underscore: __.

  **Example**: *__this_is_a_special_definition_name__*


********************************
Multi-State and Global Triggers:
********************************

Some state machine models may have a state that can be reached by multiple states using the same transition API/callback. Rather than define the trigger for each state, the trigger can be defined once and applied to any number of (or all) valid source states.

For instance, when building a virtual machine (VM), it is possible that at any point in the process, the VM could go into the error state due to an unanticipated error.


**Prefix**:

   The specialized prefix for multi-trigger definitions is: **__MULTI_TRIGGERS__**.


**Definition**:

  The multi-trigger definition is very similar to a standard trigger definition with a few additional fields.

  **trigger_name**:

    The trigger name is a simple single word string describing the action or transition.

    *Recommendation*: the trigger name should be a verb; using a verb makes more intuitive sense when describing the state machine path since the trigger is an action causing a state change.

  **description**: *(NEW)*

   This is a text string used to describe the purpose of the trigger. This field is unique to the multi-trigger definition and is only for reporting and for definition clarity; it is not used by the state machine. There are no requirements on the length, characters, or content of the string.

  **destination_state**:
    The destination state is a state that the state machine should transition after the execution of the given trigger. Prior to starting the execution, the state machine will validate all destination states to verify the states is valid and correctly defined. When the destination state is reached, the state machine will execute that destination state's validation routines to verify the state of the system is correct.

  **routine_to_change_state**:
    The routine should be a dotted path of the transition routine to execute. The routine is should be readily referencable (e.g. - a method of an already instantiated object or imported library).

  **source_states**:  *(NEW)*
   This field defines the states that can use this trigger to transition to the specified destination state. The field value has two forms:

   *wildcard*:
     The wildcard allows all defined states to be able to call this trigger.

     **NOTE**: The wildcard will include the terminal states of the model, so *caution* should be used when using the wildcard. Do you really want **all** states to have access to this trigger?

     *Format*: ::

        source_states: "*"

   *list*:
     This is a list of defined states that will be granted access to call this trigger.

     *Format*: ::

        source_states:
           - ACTIVE
           - BUILDING
           - REBOOT
           - PAUSE

  **Example**: ::

    - __MULTI_TRIGGERS__:
      - trigger_name: multi_trigger_test_from_all
        description: test_all using a wildcard specifier
        destination_state: ERROR
        routine_to_change_state: object_model.in_error
        source_states: "*"

      - trigger_name: multi_trigger_test_from_select_states
        description: test_select using a list
        destination_state: ERROR
        routine_to_change_state: object_model.in_error
        source_states:
          - ACTIVE
          - BUILDING
          - DELETED


----------------------------------------------------------------


================================
Utilities
================================

To help with the building of a state machine model definition YAML file, there is a script in the utility directory that will allow you to build a basic YAML file in the correct/supported format.

**Location**:  */flowtester/utils/state_machine_def_template_builder.py*

**Usage**: ::

 state_machine_def_template_builder.py [-h] [-m] [-d] num_states yaml_out_file

 positional arguments:
   num_states           The number of states in the state machine.
   yaml_out_file        The name of the YAML template file to .

 optional arguments:
   -h, --help           Show this help message and exit.
   -m, --multi_trigger  Add a multi-trigger definition to the template.
   -d, --debug          Enable debug logging.

Once the template is defined, the user just needs to "fill in the blanks".
