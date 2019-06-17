==================
Unit Testing
==================

------------------
Purpose
------------------

Unit tests are the first line of defense in verifying the code does not have any issues (bugs). Since unit tests validate the functionality as close to the code as possible, unit tests are **critical** for a maintaining a successful project as it grows and evolves. As part of the ``flow tester`` code hygiene process, unit tests should be written and maintained for all code. The unit test coverage is measured and each committed change should be evaluated to verify coverage covers as many code paths as possible.

Unit tests should not require external resources or dependencies, such as databases, web services, or other applications. The external dependencies should be mocked so that the tests can be run locally without special configurations.

**NOTE**: When mocking external dependencies, care needs to be taken to assure the mocks reflect the *current* expected behavior(s) and are updated to reflect any external dependency changes.

------------------
Organization
------------------
The testing code is maintained in the /tests subdirectory of the project. ::

    <base_project_dir>/flowtester/tests

The structure is broken into two primary sections: *functional* and *unit*. There is also a data directory, which contains any YAML files and object models required to test the flow tester. The object models are kept in the same directory as the YAML files since both files are directly dependent on each other.


Functional
..................
The functional test directory will be used for testing larger, more comprehensive functionality, the tests should validate the entire ``flowtester`` process, as provided by the various flowtester components working together. Currently, there are no tests in this directory, but over time, if there is a need, the directory is available.

Unit
..................
Unit tests validate the module code at the "code level"; the tests are intimately aware of the implementation details of the code. The tests should verify as many code paths possible and validate all conditionals throughout the code.

Organization and Naming Convention
**********************************

- **Directory Structure**: The unit test code directory structure exactly mirrors the functional code directory structure. This allows easy location and identification of tests to a specific python code file.

- **File Naming**: The unit test files should match the exact code filename but also include a prefix of *test_*.

  +--------------+--------------------------+
  | *code file*: | ``this_is_code.py``      |
  +--------------+--------------------------+
  | *test file*: | ``test_this_is_code.py`` |
  +--------------+--------------------------+

  The prefix of ```test_``` must be present, or nose will not detect the test file as a candidate for execution.


- **Test Classes**: Naming of test classes matches the same nomenclature as files.

  +--------------------+------------------------+
  | *code class name*: |   ``ExampleClass:``    |
  +--------------------+------------------------+
  | *test class name*: |  ``TestExampleClass:`` |
  +--------------------+------------------------+

  The test class has the same name as the code class but should be prefixed by "Test".


- **Test Functions**: Test functions should contain the primary code method under test and list the primary aspect(s) being validated. The test routines **must start** with *test* (as required by nose; for more information, please refer the Execution section.)

  +---------------------------+---------------------------------------------+
  | *code class method name*: | ``create_something(options=None)``          |
  +---------------------------+---------------------------------------------+
  | *test class method name*: | ``test_create_something_with_no_options()`` |
  +---------------------------+---------------------------------------------+
  | *test class method name*: | ``test_create_something_with_options()``    |
  +---------------------------+---------------------------------------------+

  Any helper method or orchestration routine can be defined and named in any manner desired, but it is **highly recommended** that the function names indicate what the routine does.

- **Utils**: There is a file in the ``/tests/unit directory``: utils.py - This contains general routines needed by multiple classes/files. Routines in this file should always be general and not specific to any test. Routines that are specific to a test or set of tests should be contained within the same test code python file, or in the same directory.

------------------
Execution
------------------
Execution is simple with `nose <https://nose.readthedocs.io/en/latest/index.html>`_ and can be executed directly from the tests/unit directory.


Tools and Installation
........................
The primary tools used for unit testing are **nose**, **coverage**, and **mock** (as needed). All of the packages need to be installed and can be installed via pip: ::

   pip install -r test_requirements.txt

Executing the Tests
....................
There is a shell script in the base module directory: **unittest.sh**. This is the same directory as setup.py, requirements.txt, etc. The shell script is the quickest way to execute the unit tests since it provides all of the necessary configuration information to nose and also configures the code coverage tool.

Debugging
..........

Occasionally, the coverage database will become corrupted. Symptoms for corruptions often include:

- No changes in coverage percentages when additional tests were added that are expected to cover new/missed code.
- Unittest execution fails due to be unable to write the results to the database.

Fortunately, the corruption is easy to fix, although a rather brute force method. In the same directory as the ``./unittest.sh``, delete the coverage database::

   rm .coverage

When the unit tests are rerun, the database should be re-instantiated and repopulated.

---------------
Test Coverage 
---------------

The coverage tool is provided by `coverage <https://coverage.readthedocs.io/en/coverage-4.2/#>`_ and integrates directly into the nose execution process. (See the unittest.sh for the configured options used).

The coverage tool, as configured, will generate two reports: a summary table of the coverage diplayed at the end of the test execution and a detailed HTML version of the coverage.

The HTML report is created in ``<base_flowtester_dir>/htmlcov``. (Note: GitHub is configured via .gitignore to ignore the ``htmlcov`` directory, so you can run the tests and not worry about accidentally polluting the repo). 

Using a browser, navigate into the htmlcov directory and select **index.html**. index.html wil display the per file summary of number of lines covered, missed, and skipped. By clicking on any of files listed, it will display the full file listing, indicating exactly which lines are covered, not covered, and skipped.

**NOTE**: The coverage indicates which lines were **executed** but it does not mean all logic in a conditional statement were executed. This is important to note because:

* **Conditionals**: In python, if a conditional has a logical 'and' operation, if **any** of the conditional clauses evaluate to *False*, python stops evaluating the clause. This means there is a _chance_ that one of the remaining conditionals was not evaluated - which *could* mask a logic error, an exception, or <gasp> a bug.

* **Parameters**: A routine might be executed by a different segment of code that is using it properly, but the routine is not actually tested. Consider parameter combinations with default values, expected values, and unexpected values (within reason), such as None; especially if those values are used as part of conditional logic.


------------------
Adding Tests
------------------
Every python file that exists in the code base (that has logic [1]_) should have a corresponding unit test file. A test can have multiple assertions, but should only validate one aspect or responsibility of the given routine.

**Recommendation**: Keep the tests simple and numerous rather than a few complex tests - complex tests are hard to understand, follow, debug, and significantly increases the chance of missing something. Additionally, when something is missed, addressing it can increase the amount of code duplication.

**Recommendation**: Import and instantiate the python logger. Add logging msgs (INFO level) like input, expectations, and responses, throughout the test to document the process. Nose will automatically capture all output. If the test passes, this information will not be displayed, but on failure, nose will display all logging, STDOUT, and STDERR to the console.

The test case nomenclature is defined in the `Organization and Naming Convention`_ section.

`Test Coverage`_ is reported with each run (using ./unittests.sh), so all changes should be evaluated to make sure the code is adequately tested beyond "just executing".


Docstrings and Documentation
..............................
Test routines should be named clearly so they give a general indication of what they are testing. Docstrings are not required for tests since there are no parameters and the tests should only 5-6 lines (excluding logging) with a purpose-focused name.

Docstrings should be created for routines that are helper functions or orchestrations. Provide clear descriptions of the parameters, usage, assumptions, and return values. Docstrings are not required for the actual tests if the name is clear and the test is small.

Test routines and helper routines can have embedded comments (not required, but recommended), especially for complex logic, assumptions built into the logic, or where there is a break in the code. (Line break between two distinct code segments.)

Commits
..................
For all commits, the unit tests should be executed and should pass prior to creating the PR. For all new code, updated logic, or any refactoring, please be sure to add unit tests where it makes sense (changes in logic, conditionals, return values, or new lines not currently covered by existing tests.)

The coverage percentages should remain as high as possible, but it is recognized that sometimes the effort required to reach a specific error condition is not worth time required; **please do not use** that as an excuse to not provide adequate testing coverage.

Footnotes
..................

.. [1] Files that are purely data/constants classes or empty __init__.py do not need to have unit tests defined.
