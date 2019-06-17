import pprint
import typing


class PathStep:
    """
    Stores an individual step/trigger, and the expectations, ids, etc.
    This is a container object that can be expanded so various consumers have
    access to the necessary information, without creating specialized methods
    or crossing responsibility boundaries (e.g. - reduces coupling).
    """

    ID = 'id'
    EXPECTATION = 'expectation'
    DEFAULT_EXPECTATION = True

    def __init__(self, trigger, trigger_id=None):
        self.trigger = trigger
        self.expectations = []
        self.trigger_data = None
        self.id = trigger_id

    def add_id(self, step_id: str) -> None:
        """
        Assign a unique id to the step for direct referencing since the
        trigger name may not be unique or could be duplicated within a list.

        Args:
            step_id (str): unique id

        Returns:
            None

        """
        self.id = step_id

    def add_expectation(self, validation_id: str, expectation: bool) -> None:
        """
        Add an result expectation to the step.

        Args:
            validation_id (str): Trigger validation id (defined by data model)
            expectation (boolean): Expectation of validation results

        Returns:
            None

        """
        expected = {self.ID: validation_id,
                    self.EXPECTATION: expectation}
        self.expectations.append(expected)

    def add_data(self, data: typing.Any) -> None:
        """
        Save data defined in YAML file for the given step

        Args:
            data: dictionary of data.

        Returns:
            None

        """
        self.trigger_data = data

    def get_expectation(
            self, validation_id: str) -> typing.Any:
        """
        Check if validation_id exists, and if so, return expectation. If the
        id does not exist, return the default expectation.

        Args:
            validation_id: id representing a state's validation routine

        Returns:
            Boolean value associated with the id, or
            if id DNE, the default expectation.

        """
        expectation = self.DEFAULT_EXPECTATION
        keys = [x for x in self.expectations if validation_id in x[self.ID]]
        if keys:
            expectation = keys[0][self.EXPECTATION]
        return expectation

    def __str__(self):
        response = f"STEP: {self.trigger}\nID: {self.id}"
        expectations = []

        for exp in self.expectations:
            expectations.append((f"\tValidation ID: {exp[self.ID]:12}"
                                 f"\tExpectation: {exp[self.EXPECTATION]}"))

        # Expectations stored in list and then "joined" to create
        # consistent formatting. Was adding '\n' to each line, but it
        # created unnecessary line breaks for multi-expectation triggers
        if expectations:
            response += "\n".join(expectations)
        else:
            response += "\tNo custom expectations"

        data = self.trigger_data or None
        response += f"\n\tTrigger Data: {pprint.pformat(data)}"

        return response
