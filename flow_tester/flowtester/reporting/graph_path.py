"""
graph_list.py

(C) 2013-2019 Rackspace Hosting, Inc.

Purpose:
This library will create a string-based visual representation of a ordered
list, for instance: a state machine path. It creates a start box, and using
ASCII art, creates a box for each element (state), and will wrap to the next
"line" with arrows. After the last element (state), it will append an "end"
box. The number of elements per line and the size of each box are configurable.

Example:
Given a list: [create_lb, ssl_off, ssl_on, suspend_lb,
               unsuspend_lb, ssl_on, delete_lb]

Using 2 elements/line, the result:
TEST PATH:
                          STEP  1             STEP  2
   +============+      +------------+      +------------+
   |   READY    |----->| create_lb  |----->|  ssl_off   |----->+
   +============+      +------------+      +------------+      |
                                                               |
                          STEP  4             STEP  3          |
                       +------------+      +------------+      |
                +<-----| suspend_lb |<-----|   ssl_on   |<-----+
                |      +------------+      +------------+
                |
                |         STEP  5             STEP  6
                |      +------------+      +------------+
                +----->|unsuspend_lb|----->|   ssl_on   |----->+
                       +------------+      +------------+      |
                                                               |
                                              STEP  7          |
   +============+                          +------------+      |
   |    END     |<-------------------------| delete_lb  |<-----+
   +============+                          +------------+
"""
import random
from typing import List

DEFAULT_SIZE = 20


class GraphPath(object):
    """
    The primary graph structure, the graph list creates a series of graph
    elements, and builds an ordered list of "elements", then stitches them
    together based on the number of elements per line.

    Casting the GraphList object as a string will create the graphic.

    """
    BUFFER = 10
    TRIGGER_PREFIX = "Trigger"

    def __init__(self,
                 graph_list: List[str],
                 triggers: List[str] = None,
                 items_per_line: int = 3,
                 item_size: int = DEFAULT_SIZE,
                 add_index: bool = False) -> None:

        """ Initializes the GraphList

        Args:
            graph_list (list): List of states (equates to boxes in diagram)
            triggers (list): List of state transition triggers or element
                descriptions to be rendered and centered above each box.
            items_per_line (int): Number of boxes per "line"
            item_size (int): Default size (in characters) of box.
                Graph will automatically adjust if box entry is longer
                than the default size.
            add_index (bool): Add step index to displayed text
                e.g - | 1: <text> |

        Return:
            None

        """
        self.graph_list = graph_list
        self.triggers = triggers or []
        self.items_per_line = items_per_line
        self.item_size = item_size

        # Add 'index: ' to each element if requested
        if add_index:
            self.graph_list = ["{0}: {1}".format(index + 1, value) for
                               index, value in enumerate(graph_list)]

        self._get_length_of_longest_element()

        if self.items_per_line < 1:
            self.items_per_line = 1

        # Update item_size to fit longest element if longest element
        # is greater than the item_size

        self.diagram = self.build_diagram()

    def __str__(self) -> str:
        """
        Displays ASCII chain of the provided path.

        Returns:
            (str) - ASCII representation of path
        """
        return self.render()

    def _get_length_of_longest_element(self) -> None:
        """
        Determines the longest element in the list, and adjusts the
        self.item_size if the length is greater than self.item_size.
        Stores the value in the object.

        Returns:
            None

        """
        for element in self.graph_list:
            if (len(element) + self.BUFFER) > self.item_size:
                self.item_size = len(element) + self.BUFFER

    def build_diagram(self) -> List["GraphItem"]:
        """
        This routine will create the ordered list of graph elements (blocks)
        based on the number of elements per line.

        Returns:
            List of graph elements (blocks)
        """
        blocks = list()
        direction = True  # True = left to right, False = right to left
        step = 1

        # The number of elements per line is increased by two: one additional
        # element on the right and left for arrows and start/end blocks.
        line_length = self.items_per_line + 2

        # Create the start block
        blocks.append(GraphItem(id_=0, item_type='start',
                                fwd=direction, size=self.item_size))

        # Iterate through the entire list of elements (states)
        while step <= len(self.graph_list):
            steps_to_add = self.items_per_line

            # Check if current iteration is the last "row", then
            # adjust the number of steps to add to the "row" so
            # additional elements are added.
            if step + self.items_per_line > len(self.graph_list):
                steps_to_add = len(self.graph_list) - step + 1

            # Create an element for each step in the current "row"
            for _ in range(steps_to_add):
                graph_item_args = {
                    'id_': step, 'text': self.graph_list[step - 1],
                    'fwd': direction, 'size': self.item_size}

                # If an action list was provided, add to the box definition
                if self.triggers:

                    # There is an offset of two when traversing the trigger list.
                    #  + Element 0 is the "READY" box and
                    #  + Element 1 is the starting element, so there is no
                    #      trigger to GET TO that state.
                    description = ''
                    if step != 1 and len(self.triggers) > step - 2:
                        description = "{prefix}:{trigger}".format(
                            prefix=self.TRIGGER_PREFIX,
                            trigger=self.triggers[step - 2])

                    graph_item_args['description'] = description

                blocks.append(GraphItem(**graph_item_args))
                step += 1

            # If at the end of a row, add an element for the first half of the
            # looping arrow. Then indicate that the line is reversing direction
            # (arrows were going left to right, now they should go right to
            # left.
            if (steps_to_add == self.items_per_line and
                    step <= len(self.graph_list)):

                blocks.append(
                    GraphItem(id_='a', item_type='next_line', fwd=direction,
                              size=self.item_size))
                direction = not direction
                blocks.append(GraphItem(
                    id_='b', item_type='next_line', next_line=True,
                    fwd=direction, size=self.item_size))

        # If going left_to_right
        if direction:
            # If the list of elements > elements per line,
            # determine how many blank elements will be needed to
            # create a list so that the list length % elements/line = 0
            # Append the empty blocks to the list
            if len(self.graph_list) > self.items_per_line:
                if (step - 1) % self.items_per_line != 0:
                    blanks = (self.items_per_line -
                              ((step - 1) % self.items_per_line))
                    for _ in range(blanks):
                        blocks.append(GraphItem(
                            id_='arrow', item_type='arrow', fwd=direction,
                            size=self.item_size))

        # Must be going right_to_left
        else:

            # Determine how many empty elements will be needed to create a
            # list so that the list length % elements/line = 0,
            # append those blocks to the list
            subtotal = len(blocks)
            while subtotal > line_length:
                subtotal -= line_length
            nulls = line_length - subtotal - 1

            for _ in range(nulls):
                blocks.append(GraphItem(id_=random.randint(100, 1000),
                                        item_type='arrow',
                                        size=self.item_size))
        # Add the end block
        blocks.append(GraphItem(id_=1000, item_type='end',
                                fwd=direction, size=self.item_size))
        return blocks

    def render(self) -> str:
        """
        Combine the list elements to create a string representation of the
        list.

        Returns:
            A single cumulative string repr of all elements
        """
        output = ''
        block_length = len(self.diagram)
        index = 0
        direction = 1

        # While there are blocks to be added
        while index < block_length:
            start = index
            stop = index + self.items_per_line + 2

            if stop > block_length:
                stop = block_length

            # If direction is reversed (using slice notation),
            # Swap the slice indices
            # e.g. if next set of blocks to add is [4:7:1] but in reverse,
            # the indices would change to [6:3:-1]
            if direction == -1:
                temp = start - 1
                start = stop - 1
                stop = temp

            first = True
            block = None
            # Combine the blocks into a row
            for single_block in self.diagram[start: stop: direction]:
                if first:
                    block = single_block
                    first = False
                else:
                    block += single_block
                index += 1
            # Add the row to the cumulative string
            output += str(block)

            # Switch directions
            direction = -1 if direction == 1 else 1

        return output


class GraphItem(object):
    """ Represents a single element in the diagram

    Note:
        object.entity = 5 element list:
            top line
            upper line
            middle line
            lower line
            bottom line

    """
    def __init__(self, id_, text='', item_type='standard', size=DEFAULT_SIZE,
                 fwd=True, next_line=False, description=None):
        self.id = id_
        self.text = text
        self.size = size
        self.type = str(item_type).lower()
        self.fwd = fwd
        self.next_line = next_line
        self.entity = self.build_block(description)

    def __add__(self, other) -> "GraphItem":
        """

        Args:
            other (GraphItem): GraphItem to add to current GraphItem (self)

        Returns:
            Updated element (self)
        """
        block_line = list()

        # Iterate across entity lines, and concatenate the lines
        for index in range(len(self.entity)):
            block_line.append('{0}{1}'.format(self.entity[index],
                                              other.entity[index]))
        update = GraphItem(id_='sum', size=self.size)
        update.entity = block_line
        return update

    def __repr__(self):
        """ Iterates through entity list and concatenates lines together """
        block = ''
        for line in self.entity:
            block = '{0}{1}\n'.format(block, line)
        return block

    def build_block(self, description: str = None) -> List[List[str]]:
        """
        Builds the block string list (top|upper|middle|lower|bottom)

        Args:
            description (str): Text to be placed above box

        Returns:
            list of strings
        """
        struct = list()
        if self.type == 'standard':
            struct = self._build_standard_item(description)
        elif self.type == 'start':
            struct = self._build_start_block()
        elif self.type == 'end':
            struct = self._build_end_block()
        elif self.type == 'next_line':
            struct = self._build_next_row(first_segment=not self.next_line)
        elif self.type == 'none':
            struct = self._build_null_block()
        elif self.type == 'arrow':
            struct = self._build_arrow_block()
        return struct

    def _build_standard_item(self, description: str = None) -> List[str]:
        """ Normal block with text and a step number

        Args:
            description: Text to be placed above the box

        Return:
            list of strings

        """
        description_format = '{0}'
        if description is None:
            description_format = 'STEP {0:<2}'
            description = self.id

        top_line_text = description_format.format(description)
        border = self._build_box_border()
        step_line = self._build_top_line(text=top_line_text)
        text_line = self._build_middle_line()
        blank_line = self._build_blank_line()
        return [step_line, border, text_line, border, blank_line]

    def _build_box_border(self, char: str = '-') -> str:
        """ Builds horizontal portions of the box

        Args:
            char: Character to use for string

        Returns:
            string representing the border

        """
        prefix = '   +' if self.fwd else '   +'
        suffix = '+   ' if self.fwd else '+   '
        box_fmt = '{prefix}{border}{suffix}'
        border_length = self.size - len(prefix) - len(suffix)
        border = box_fmt.format(border=char * border_length,
                                prefix=prefix, suffix=suffix)
        return border

    def _build_top_line(self, text: str) -> str:
        """ Builds the step number (or whatever) top line.

        Text is centered to length of box

        Args:
            text (str): Text to display above box

        Returns:
            string representing the identifier

        """
        fmt_str_1 = '{{id: ^{size}}}'.format(size=self.size)
        line = fmt_str_1.format(id=text, add=' ')
        return line

    def _build_middle_line(self, text: str = None, join: bool = True,
                           start: bool = False) -> str:
        """ Builds the middle line of a box

        Args:
            text (str): Text to have in box (if standard box)
            join (bool): If true, add arrows left-to-right
            start (bool): If a starting box, no arrow leader on side (direction based on join parameter)

        Returns:
            String representing the middle line

        """
        text = text or self.text
        if join:
            prefix = '-->|' if self.fwd else '---|'
            suffix = '|---' if self.fwd else '|<--'
        else:
            if start:
                prefix = '   |'
                suffix = '|---'
            else:
                prefix = '-->|' if self.fwd else '   |'
                suffix = '|   ' if self.fwd else '|<--'

        str_len = str(self.size - len(prefix) - len(suffix))
        fmt_str_2 = '{{prefix}}{{text: ^{0}}}{{suffix}}'.format(str_len)
        line = fmt_str_2.format(prefix=prefix, suffix=suffix,
                                text=text)
        return line

    def _build_blank_line(self) -> str:
        """ Builds a blank line the length of the graph element

        Returns:
            A string of spaces...

        """
        return ' ' * self.size

    def _build_arrow_block(self) -> List[str]:
        """ Builds a simple line in the middle, spanning the length the box

        Returns:
            List of strings representing a line

        """
        blank_line = self._build_blank_line()
        line = '-' * self.size
        return [blank_line, blank_line, line, blank_line, blank_line]

    def _build_start_block(self) -> List[str]:
        """ Builds the start/ready block

        Returns:
            List of strings representing the start/ready box

        """
        self.fwd = True
        self.text = 'READY'
        return self._build_terminal()

    def _build_end_block(self) -> List[str]:
        """ Builds the end block
        Returns:
            List of strings representing the end box

        """
        self.text = 'END'
        return self._build_terminal()

    def _build_terminal(self) -> List[str]:
        """ Builds a box that is at the beginning or end of a sequence

        Will only have 1 leader on one side

        Returns:
            List of strings representing a terminal block

        """
        start = True if self.text.lower() == 'ready' else False
        border = self._build_box_border(char="=")
        step_line = self._build_top_line(text='')
        text_line = self._build_middle_line(join=False, start=start)
        blank_line = self._build_blank_line()
        return [step_line, border, text_line, border, blank_line]

    def _build_next_row(self, first_segment: bool = True) -> List[str]:
        """ Builds the line continuations first_segment determines
        if upper or lower block.

        Args:
            first_segment: Is this the first segment?
                If True, build "top half" of loop;
                False = Build "bottom half" of loop

        Returns:
            List of strings representing of end-of-row loop arrow

        """
        connector = '|   '
        space = ' ' * (self.size - len(connector))
        blank_line = self._build_blank_line()

        # Left_to_Right
        if self.fwd:

            # Top Half
            if first_segment:
                self.id = 'FWD:DOWN    ---V'
                struct = [blank_line, blank_line, '-->+', '   |', '   |']

            # Bottom Half
            else:
                self.id = 'BACK:ACROSS +-->'
                arrow = '+---'
                top_line = '{0}{1}'.format(space, connector)
                middle_line = '{0}{1}'.format(space, connector)
                bottom_line = '{0}{1}'.format(space, arrow)
                struct = [top_line, middle_line, bottom_line, blank_line,
                          blank_line]

        # Right_To_Left
        else:
            # Top Half
            if first_segment:
                self.id = 'BACK:DOWN   V---'
                arrow = '+<--'
                top_line = blank_line
                middle_line = '{0}{1}'.format(space, arrow)
                bottom_line = '{0}{1}'.format(space, connector)
                struct = [top_line, top_line, middle_line, bottom_line,
                          bottom_line]

            # Bottom Half
            else:
                self.id = 'FWD:ACROSS  <--+'
                struct = ['   |', '   |', '---+', blank_line, blank_line]

        return struct

    def _build_null_block(self) -> List[str]:
        """ Builds a null block (just space, no characters)

        Returns:
            String representation of empty block (e.g. spacer)

        """
        line = self._build_blank_line()
        return [line, line, line, line, line]
