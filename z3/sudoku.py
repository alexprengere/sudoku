#!/usr/bin/env python3

import itertools
import sys
import z3


def rows():
    """Returns the indexes of rows."""
    return range(0, 9)


def cols():
    """Returns the indexes of columns."""
    return range(0, 9)


def sudoku_from_string(s):
    """Builds a sudoku from a string.

    Args:
        s: string representing a sudoku cell by cell from the top row to the
        bottom road. Admissible characters are 0-9 for known values, . for
        unknown values, and \n (ignored).

    Returns:
      A dictionary (int, int) -> int representing the known values of the
      puzzle. The first int in the tuple is the row (i.e.: y coordinate),
      the second int is the column (i.e.: x coordinate).
    """
    valid_chars = set([str(x) for x in range(1, 10)])
    valid_chars.add(".")
    sudoku = {}
    if len(s) != 81:
        raise ValueError("wrong input size")
    invalid_chars = set(s).difference(valid_chars)
    if invalid_chars:
        err_str = ", ".join(invalid_chars)
        raise ValueError("unexpected character(s): %s" % err_str)
    for r in rows():
        for c in cols():
            char = s[0]
            if char != ".":
                sudoku[(r, c)] = s[0]
            s = s[1:]
    return sudoku


def read_sudoku(f):
    """Reads a sudoku from a file-like object.

    Args:
        f: file object.

    Returns: dictionary (int, int) -> int. See sudoku_from_string for details.
    """
    invar = ""
    valid_chars = set([str(x) for x in range(1, 10)])
    valid_chars.add(".")
    for line in f:
        line = line.strip().replace(" ", "")
        invar = invar + line
    return sudoku_from_string(invar)


def solve_sudoku(known_values):
    """Solves a sudoku and prints its solution.

    Args:
      known_values: a dictionary of (int, int) -> int representing the known
                    values in a sudoku instance (i.e.: hints). The first int in
                    the tuple of the keys is the row (0-indexed), the second
                    one is the column (0-indexed).
    """
    # Create a Z3 solver
    s = z3.Solver()
    # Create a matrix of None, which will be replaced by Z3 variables. This
    # is our sudoku.
    cells = [[None for _ in cols()] for _ in rows()]
    for r in rows():
        for c in cols():
            # Z3 variables have a name
            v = z3.Int("c_%d_%d" % (r, c))
            # Keep a reference to the Z3 variable in our sudoku.
            cells[r][c] = v
            # If this cell contains a hint, then add a constraint that force
            # the current variable to be equal to the hint.
            if (r, c) in known_values:
                s.add(v == known_values[(r, c)])

    # This function adds all the constraints of a classic sudoku
    add_constraints(s, cells)

    if s.check() == z3.sat:
        # Retrieve the model from the solver. In this model all the variables
        # are grounded (i.e.: they have a value)
        m = s.model()
        for r in rows():
            for c in cols():
                # Retrieve the grounded value and print it.
                v = m.evaluate(cells[r][c])
                print(v, end=" ")
                # Add vertical spacing for a subgrid
                if (c + 1) % 3 == 0:
                    print("  ", end="")
            print()
            # Add horizontal spacing for a subgrid
            if (r + 1) % 3 == 0:
                print()
        print()


def add_constraints(s, cells):
    classic_constraints(s, cells)


def classic_constraints(s, cells):
    """Adds the classic sudoku constraints to a z3 solver.

    Args:
        s: z3.Solver instance.
        cells: a 9x9 list of lists, where each element is a z3.Int instance.
    """
    # All values must be 1 <= x <= 9.
    for r in rows():
        for c in cols():
            v = cells[r][c]
            s.add(v >= 1)
            s.add(v <= 9)

    # All cells on the same row must be distinct.
    for r in rows():
        s.add(z3.Distinct(cells[r]))

    # All cells on the same column must be distinct.
    for c in cols():
        col = [cells[r][c] for r in rows()]
        s.add(z3.Distinct(col))

    # All cells in a 3x3 subgrid must be distinct: for each top left cell of
    # each subgrid select all the other cells in the same subgrid.
    offsets = list(itertools.product(range(0, 3), range(0, 3)))
    for r in range(0, 9, 3):
        for c in range(0, 9, 3):
            group_cells = []
            for dy, dx in offsets:
                group_cells.append(cells[r + dy][c + dx])
            s.add(z3.Distinct(group_cells))


# Main: read a sudoku from a file or stdin
if __name__ == "__main__":
    if len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            known_values = read_sudoku(f)
    else:
        known_values = read_sudoku(sys.stdin)
    solve_sudoku(known_values)
