from typing import List, NoReturn

from flowtester.logging.logger import Logger
from flowtester.reporting.graph_path import GraphPath

from nose.tools import assert_true, assert_greater_equal


logging = Logger()


class TestGraphPath:

    # Note:
    # GraphItem is tested by inclusion as part of testing the GraphPath object

    NUM_STEPS = 7
    NUM_ITEMS_PER_LINE = 3
    LINES_PER_ROW = 4

    PATH = [f'ITEM_{x}' for x in range(NUM_STEPS)]
    TRIGGERS = [f'TGR_{x}' for x in range(NUM_STEPS)]

    def test_default_functionality(self):
        self._test_functionality(items=self.PATH)

    def test_functionality_with_added_index(self):
        self._test_functionality(items=self.PATH, add_index=True)

    def test_functionality_with_items_per_line_less_than_one(self):
        self._test_functionality(
            items=self.PATH, add_index=True, items_per_line=0)

    def test_default_functionality_with_triggers(self):
        self._test_functionality(
            items=self.PATH, triggers=self.TRIGGERS)

    def test_default_functionality_with_full_items_per_line(self):
        self._test_functionality(
            items=self.PATH, items_per_line=len(self.PATH))

    def test_back_and_forth_line_traversal(self):
        self._test_functionality(
            items=self.PATH, items_per_line=1)

    def test_right_to_left_arrow_blocks(self):
        self._test_functionality(
            items=self.PATH, items_per_line=5)

    def test_long_element_name(self):
        path = self.PATH[:]
        path[-1] = "This is a really long name"
        self._test_functionality(items=path)

    def _test_functionality(
            self, items: List[str],
            triggers: List[str] = None,
            items_per_line: int = NUM_ITEMS_PER_LINE,
            add_index: bool = False) -> NoReturn:
        """
        Builds graph based on input and checks attributes of returned
        string.

        Args:
            items List[str]: List of elements to put into graph
            triggers List[str]: List of triggers to list above each item
            items_per_line (int): Number of elements per line in graph
            add_index (bool): Add incrementing index to each element

        Returns:
            None

        """

        # Build Graph Object
        path = GraphPath(
            graph_list=items, triggers=triggers,
            add_index=add_index, items_per_line=items_per_line)

        # Render the string representation (should work)
        str_path = str(path)
        assert_true(isinstance(str_path, str))

        # Estimate the number of lines in the rendering
        if items_per_line < 1:
            items_per_line = 1

        expected_num_lines = (
                int(len(items) / items_per_line) * self.LINES_PER_ROW)
        assert_greater_equal(len(str_path.split('\n')), expected_num_lines)
