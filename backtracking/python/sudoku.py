import itertools


def read(rows):
    """Reads the list of rows and returns the sudoku dict.

    The sudoku dict maps an index to a known value. Unknown values are not written.
    Indices go from 0 to 80.
    """
    sudoku = {}
    i = 0
    for rn, row in enumerate(rows):
        if rn in (3, 7):
            continue
        j = 0
        for cn, c in enumerate(row.rstrip()):
            if cn in (3, 7):
                continue
            if c != ".":
                sudoku[i * 9 + j] = int(c)
            j += 1
        i += 1

    return sudoku


def show(sudoku):
    """Pretty print the content, kind of the opposite of `read`"""
    for k in range(81):
        i, j = k // 9, k % 9
        print(sudoku.get(k, "."), end="")
        if j in (2, 5):
            print(" ", end="")
        elif j == 8:
            print()
            if i in (2, 5):
                print()


def get_neighbor_indices(k):
    """Returns indices of cases on the same line/column/square as the index"""

    i, j = k // 9, k % 9

    # Same line indices
    for dj in range(9):
        if dj != j:
            yield i * 9 + dj

    # Same column indices
    for di in range(9):
        if di != i:
            yield di * 9 + j

    # Same square indices
    li = i // 3 * 3
    lj = j // 3 * 3
    for di in range(li, li + 3):
        for dj in range(lj, lj + 3):
            if (di, dj) != (i, j):
                yield di * 9 + dj


def solve(sudoku):
    """Solves the Sudoku in place, or raises ValueError if not solvable."""

    # Possibilities for each index are represented as bits in an integer
    # Bits 0 to 8 correspond to digits 1 to 9
    possibilities = {}
    for k in range(81):
        if k not in sudoku:
            possibilities[k] = 0x1FF
    unknown = set(possibilities)

    # Mapping of indices that affects other indices
    neighbors = {}
    for k in range(81):
        neighbors[k] = set(get_neighbor_indices(k)) & unknown

    # We remove the possibilities in same line/column/square
    for k, n in sudoku.items():
        mask = 1 << (n - 1)
        for di_dj in neighbors[k]:
            if possibilities[di_dj] & mask:
                possibilities[di_dj] &= ~mask

    stack = [(sudoku, possibilities)]
    while stack:
        state, poss = stack.pop()

        # First we sync the state with the latest changes of poss.
        # When the possibilities are reduced to 1 single value, we write to state
        # Then we loop to reduce other possibilities, and so on
        stuck = False
        backtrack = False
        while not stuck and not backtrack:
            stuck = True
            for k in list(poss):
                bits = poss[k]
                if bits == 0:
                    # No possibilities for this cell, we need to break out of both loops
                    # and backtrack
                    backtrack = True
                    break
                elif bits.bit_count() == 1:
                    state[k] = n = bits.bit_length()
                    del poss[k]  # remove from the possibilities
                    mask = 1 << (n - 1)
                    for di_dj in neighbors[k]:
                        if di_dj in poss and poss[di_dj] & mask:
                            poss[di_dj] &= ~mask
                            stuck = False

        if backtrack:
            continue

        # No more possibilities means we finished it
        if not poss:
            sudoku.update(state)
            return

        # Find the place with fewest possibilities, and add those to the stack
        min_k = min(poss, key=lambda k: (poss[k].bit_count(), k))

        for n in range(1, 10):
            mask = 1 << (n - 1)
            if not poss[min_k] & mask:
                continue
            new_state = state.copy()
            new_state[min_k] = n
            new_poss = poss.copy()
            del new_poss[min_k]
            for di_dj in neighbors[min_k]:
                if di_dj in new_poss and new_poss[di_dj] & mask:
                    new_poss[di_dj] &= ~mask

            stack.append((new_state, new_poss))

    raise ValueError("Not solvable")


def get_lines(sudoku):
    for i in range(9):
        yield [sudoku[i * 9 + j] for j in range(9) if i * 9 + j in sudoku]


def get_columns(sudoku):
    for j in range(9):
        yield [sudoku[i * 9 + j] for i in range(9) if i * 9 + j in sudoku]


def get_squares(sudoku):
    for li in (0, 3, 6):
        for lj in (0, 3, 6):
            yield [
                sudoku[i * 9 + j]
                for i in range(li, li + 3)
                for j in range(lj, lj + 3)
                if i * 9 + j in sudoku
            ]


def is_solved(sudoku):
    return all(
        set(numbers) == {1, 2, 3, 4, 5, 6, 7, 8, 9}
        for numbers in itertools.chain(
            get_lines(sudoku), get_columns(sudoku), get_squares(sudoku)
        )
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help="Sudoku files to solve")
    args = parser.parse_args()

    for file in args.files:
        with open(file) as f:
            sudoku = read(f)
            solve(sudoku)
            show(sudoku)
            assert is_solved(sudoku)
