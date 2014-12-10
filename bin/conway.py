#!/usr/bin/env python
"""Conway's Game of Life, drawn to the terminal care of the Blessings lib

A board is represented like this::

    {(x, y): state,
     ...}

...where ``state`` is an int from 0..2 representing a color.

"""
# This line imports nested from contextlib
from contextlib import nested
# This line imports chain from itertools
from itertools import chain
# This line imports randint from random
from random import randint
# This line imports stdout from sys
from sys import stdout
# This line import sleep, time from time
from time import sleep, time
# This line imports Terminal from blessings
from blessings import Terminal
# This line defines a function
def main():
    """Play Conway's Game of Life on the terminal."""
    # This line defines a function and includes 'X' & 'Y' cords
    def die((x, y)):
        """Pretend any out-of-bounds cell is dead."""
        # This line says that if a cell "travels" beyond it's given boundries, then it will be become dead.
        if 0 <= x < width and 0 <= y < height:
            return x, y
    # Smaller means more crowded.
    LOAD_FACTOR = 9
    # Smaller means a bigger nudge.
    NUDGING_LOAD_FACTOR = LOAD_FACTOR * 3
    # Lines 38 - 43 creates variables for given code
    term = Terminal()
    width = term.width
    height = term.height
    board = random_board(width - 1, height - 1, LOAD_FACTOR)
    detector = BoredomDetector()
    cells = cell_strings(term)

    with nested(term.fullscreen(), term.hidden_cursor()):
        try:
            while True:
                frame_end = time() + 0.05
                board = next_board(board, die)
                draw(board, term, cells)

                # Lines 53 - 62 say that if the pattern is stuck in a loop, give it a nudge:
                if detector.is_bored_of(board):
                    board.update(random_board(width - 1,
                                              height - 1,
                                              NUDGING_LOAD_FACTOR))

                stdout.flush()
                sleep_until(frame_end)
                clear(board, term, height)
        except KeyboardInterrupt:
            pass

# This line defines a function
def sleep_until(target_time):
    """If the given time (in secs) hasn't passed, sleep until it arrives."""
    # This line creates a variable for time()
    now = time()
    # This line says that if "now" is less than the target_time, then the program will take "now" away from target_time (I think)
    if now < target_time:
        sleep(target_time - now)

# This line defines a function
def cell_strings(term):
    """Return the strings that represent each possible living cell state.

    Return the most colorful ones the terminal supports.

    """
    num_colors = term.number_of_colors
    if num_colors >= 16:
        funcs = term.on_bright_red, term.on_bright_green, term.on_bright_cyan
    elif num_colors >= 8:
        funcs = term.on_red, term.on_green, term.on_blue
    else:
        # For black and white, use the checkerboard cursor from the vt100
        # Alternate charset
        return (term.reverse(' '),
                term.smacs + term.reverse('a') + term.rmacs,
                term.smacs + 'a' + term.rmacs)
    # Wrap spaces in whatever pretty colors we chose:
    return [f(' ') for f in funcs]

# Defines a function
def random_board(max_x, max_y, load_factor):
    """Return a random board with given max x and y coords."""
    # I think that this returns "dict" to either it's original state or a given one.
    return dict(((randint(0, max_x), randint(0, max_y)), 0) for _ in
                xrange(int(max_x * max_y / load_factor)))

# Defines a function
def clear(board, term, height):
    """Clear the droppings of the given board."""
    # This says that if a specific area, then something will happen to it's Y cords
    for y in xrange(height):
        print term.move(y, 0) + term.clear_eol,

# This defines a function
def draw(board, term, cells):
    """Draw a board to the terminal."""
    # These three line edit the "X" "Y" cords for a cell.
    for (x, y), state in board.iteritems():
        with term.location(x, y):
            print cells[state],

# This defines a function
def next_board(board, wrap):
    """Given a board, return the board one interation later.

    Adapted from Jack Diedrich's implementation from his 2012 PyCon talk "Stop
    Writing Classes"

    :arg wrap: A callable which takes a point and transforms it, for example
        to wrap to the other edge of the screen. Return None to remove a point.

    """
    # I think this refreshes the board?
    new_board = {}

    # This considers all of the points and their neighbors
    points_to_recalc = set(board.iterkeys()) | set(chain(*map(neighbors, board)))
    
    # Lines 134 - 147 edit points_to_recalc neighbors
    for point in points_to_recalc:
        count = sum((neigh in board) for neigh in
                    (wrap(n) for n in neighbors(point) if n))
        if count == 3:
            state = 0 if point in board else 1
        elif count == 2 and point in board:
            state = 2
        else:
            state = None

        if state is not None:
            wrapped = wrap(point)
            if wrapped:
                new_board[wrapped] = state
    # I think that this refreshes the board or a specfic place of the board.
    return new_board

# This defines a function
def neighbors((x, y)):
    """Return the (possibly out of bounds) neighbors of a point."""
    # I think this might set the place of neighbors
    yield x + 1, y
    yield x - 1, y
    yield x, y + 1
    yield x, y - 1
    yield x + 1, y + 1
    yield x + 1, y - 1
    yield x - 1, y + 1
    yield x - 1, y - 1

# This describes how to make BoredomDetector
class BoredomDetector(object):
    """Detector of when the simulation gets stuck in a loop"""

    # Get bored after (at minimum) this many repetitions of a pattern
    REPETITIONS = 14

    # We can detect cyclical patterns of up to this many iterations
    PATTERN_LENGTH = 4

    # This defines a function
    def __init__(self):
        # Make is_bored_of() init the state the first time through
        self.iteration = self.REPETITIONS * self.PATTERN_LENGTH + 1

        self.num = self.times = 0
    # This defines a function
    def is_bored_of(self, board):
        """Return whether the simulation is probably in a loop.

        This is a stochastic guess. Basically, it detects whether the
        simulation has had the same number of cells a lot lately. May have
        false positives (like if you just have a screen full of gliders) or
        take awhile to catch on sometimes. I've even seen it totally miss the
        boat once. But it's simple and fast.

        """
    # Lines 191 - 196 add variation and edit repetitions
        self.iteration += 1
        if len(board) == self.num:
            self.times += 1
        is_bored = self.times > self.REPETITIONS
        if self.iteration > self.REPETITIONS * self.PATTERN_LENGTH or is_bored:
            
            # This adds little randomness in case things divide evenly into each other
            self.iteration = randint(-2, 0)
            self.num = len(board)
            self.times = 0
        return is_bored

# This line says that if __name__ is equal to __main__ then the program will revert it to main()
if __name__ == '__main__':
    main()
