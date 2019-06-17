import typing

from flowtester.logging.logger import Logger
from flowtester.state_machine.engine.input import PathStep

logging = Logger()


class ValidatePaths:

    @staticmethod
    def validate_step(step: PathStep) -> bool:
        """
        Check the step for any missing information.

        Args:
            step (PathStep): The step to validate.

        Returns:
            Boolean result: False = validation error

        """
        result = None
        if step.id is None:
            logging.warn(f"Step '{step.trigger}' "
                         f"does not have an ID defined.")
            result = False

        if not step.expectations:
            logging.debug(f"Step '{step.trigger}' "
                          f"does not have any expectations.")

        # No errors found
        if result is None:
            result = True

        return result

    @classmethod
    def validate_steps(cls, steps: typing.List[PathStep]) -> bool:
        """

        Args:
            steps (list): The list of triggers to execute

        Returns:
            boolean: False = issues found in the list of steps

        """
        logging.debug(f"Validating the provided steps: "
                      f"{', '.join([s.trigger for s in steps])}")

        # If all steps are unique, the length of the id list and
        # the length of the set of ids should be equal.
        ids = [step.id for step in steps]
        result = len(set(ids)) == len(ids)

        id_list = []
        # Validate each step and the ids
        for num, step in enumerate(steps):

            # Make sure step is valid and correctly defined
            result = result & cls.validate_step(step)

            # Check for uniqueness
            try:
                matching_id = id_list.index(step.id)

            # Not found in the list
            except ValueError:
                pass

            # Found in the list (Reporting the index is incremented by 1
            # since indexing starts at 0)
            else:
                match = steps[matching_id].trigger
                logging.error(f"Step #{num + 1}'s ID (Trigger: {step.trigger}, "
                              f"ID: '{step.id}') is not unique.")
                logging.error(f"Step #{matching_id + 1} has the same id. "
                              f"(Trigger: {match}, ID: '{step.id}')")

            id_list.append(step.id)

        if not result:
            logging.error(f"The requested trigger/test path: "
                          f"{', '.join([f'{x.trigger} ({x.id})' for x in steps])} ")

        return result
