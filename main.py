'''
A fully-filled sudoku grid can be transformed into a variety of essentially
equivalent grids.

From Wikipedia:
<https://en.wikipedia.org/w/index.php?title=Mathematics_of_Sudoku&oldid=1095869435>

    Two valid grids are essentially the same if one can be derived from the other, using a so-called validity preserving transformation (VPT). These transformations always transform a valid grid into another valid grid. There are two major types: symbol permutations (relabeling) and cell permutations (rearrangements). They are:

    - Relabeling symbols (9!)
      (Once all possible relabeling combinations are eliminated, except for
      one: for instance, keeping the top row fixed at [123456789], the number
      of fixed grids reduces to 18,383,222,420,692,992. This value is
      6,670,903,752,021,072,936,960 divided by 9!)

    and rearranging (shuffling):

    - Band permutations (3!)
    - Row permutations within a band (3!×3!×3!)
    - Stack permutations (3!)
    - Column permutations within a stack (3!×3!×3!)
    - Reflection, transposition and rotation (2)
      (Given a single transposition or quarter-turn rotation in conjunction
      with the above permutations, any combination of reflections,
      transpositions and rotations can be produced, so these operations only
      contribute a factor of 2)
'''

import itertools
from math import factorial
from random import randrange
import random

from sudoku_utils import parse, is_valid, serialize, ALL_DIGITS_STRING, show


zeros_string = '000000000000000000000000000000000000000000000000000000000000000000000000000000000'


def main():
    S('button#scramble').addEventListener('click', handle_scramble_click)
    S('#input').addEventListener('keydown', handle_input_keydown)


def handle_scramble_click(event=None):
    # Clean up and validate input
    puzzle_string = S('#input').value.strip()
    is_valid_input = (
        len(puzzle_string) == 81
        and set(puzzle_string) <= set('0123456789')
    )
    if not is_valid_input:
        browser.alert('invalid')
        return

    scrambled = scramble(puzzle_string)
    S('#result-string').innerHTML = scrambled

    for value, cell in zip(scrambled, SS('#result-grid .row > div')):
        if value != '0':
            cell.innerHTML = value
        else:
            cell.innerHTML = ''


def handle_input_keydown(event):
    if event.key == 'Enter':
        handle_scramble_click()


def scramble(digits):
    '''
    >>> random.seed(0, version=2)

    Can "scramble" a sudoku into an equivalent one
    >>> scrambled = scramble('483921657967345821251876493548132976729564138136798245372689514814253769695417382')
    >>> print(scrambled)
    698452371531687942742139568317526894854973126926814735289345617465791283173268459
    >>> show(parse(scrambled))
    6 9 8 4 5 2 3 7 1
    5 3 1 6 8 7 9 4 2
    7 4 2 1 3 9 5 6 8
    3 1 7 5 2 6 8 9 4
    8 5 4 9 7 3 1 2 6
    9 2 6 8 1 4 7 3 5
    2 8 9 3 4 5 6 1 7
    4 6 5 7 9 1 2 8 3
    1 7 3 2 6 8 4 5 9
    <BLANKLINE>

    Works for solved or unsolved sudokus
    >>> scrambled = scramble('003020600900305001001806400008102900700000008006708200002609500800203009005010300')
    >>> print(scrambled)
    000000000150706024008020300205064013060100000407058062000000000940507086001080200
    >>> show(parse(scrambled))
    0 0 0 0 0 0 0 0 0
    1 5 0 7 0 6 0 2 4
    0 0 8 0 2 0 3 0 0
    2 0 5 0 6 4 0 1 3
    0 6 0 1 0 0 0 0 0
    4 0 7 0 5 8 0 6 2
    0 0 0 0 0 0 0 0 0
    9 4 0 5 0 7 0 8 6
    0 0 1 0 8 0 2 0 0
    <BLANKLINE>
    '''
    digits = _relabel(digits)

    digits = _permute_bands(digits)
    digits = _permute_within_bands(digits)

    digits = _permute_stacks(digits)
    digits = _permute_within_stacks(digits)

    if random.choice([True, False]):
        digits = _transpose(digits)

    return digits


def _relabel(digits):
    translation_table = str.maketrans(ALL_DIGITS_STRING, ''.join(shuffle(ALL_DIGITS_STRING)))
    return digits.translate(translation_table)


def _permute_bands(digits):
    def copy_band(grid1, grid2, b1, b2):
        '''
        Copy band indexed by B1 from GRID1 into GRID2 (at index B2).

        Indices are 0 to 2 (inclusive).
        '''
        for source_row, target_row in zip(
            [b1 * 3 + i for i in range(3)],
            [b2 * 3 + i for i in range(3)]
        ):
            for c in range(9):
                grid2[target_row][c] = grid1[source_row][c]

    perm = shuffle([0, 1, 2])
    original = parse(digits)
    result = parse(zeros_string)
    for source_band, target_band in zip(range(3), perm):
        copy_band(original, result, source_band, target_band)
    return serialize(result)


def _permute_within_bands(digits):
    def copy_row(grid1, grid2, source_row, target_row):
        for c in range(9):
            grid2[target_row][c] = grid1[source_row][c]

    original = parse(digits)
    result = parse(zeros_string)

    for band_start in [0, 3, 6]:
        source_rows = range(band_start, band_start + 3)
        target_rows = shuffle(source_rows)
        for s_row, t_row in zip(source_rows, target_rows):
            copy_row(original, result, s_row, t_row)

    return serialize(result)


def _permute_stacks(digits):
    grid = parse(digits)
    grid = transpose_grid(grid)
    grid = parse(
        _permute_bands(serialize(grid))
    )
    grid = transpose_grid(grid)
    return serialize(grid)


def _permute_within_stacks(digits):
    grid = parse(digits)
    grid = transpose_grid(grid)
    grid = parse(
        _permute_within_bands(serialize(grid))
    )
    grid = transpose_grid(grid)
    return serialize(grid)


def _transpose(digits):
    grid = parse(digits)
    grid = transpose_grid(grid)
    return serialize(grid)


def nth_permutation(seq, n):
    '''
    n: zero-indexed
    '''
    # There are more performant ways to implement this, but this is perfectly
    # sufficient for this use case.

    # Maybe do a small optimization anyway -- this can be done in "constant
    # space"
    return list(itertools.permutations(seq))[n]


def transpose_grid(m):
    """
    >>> transpose_grid([[1, 2, 3], [4, 5, 6]])
    [[1, 4], [2, 5], [3, 6]]
    """
    return [list(i) for i in zip(*m)]


def shuffle(seq):
    lst = list(seq)
    random.shuffle(lst)
    return lst


if __name__ == '__main__':
    from browser import document
    import browser
    S = document.querySelector
    SS = document.querySelectorAll
    main()
