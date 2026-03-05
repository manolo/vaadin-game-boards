"""Sudoku puzzle generation and validation engine."""

import random
from copy import deepcopy


def _is_valid(board: list[list[int]], row: int, col: int, num: int) -> bool:
    """Check if placing num at (row, col) is valid."""
    if num in board[row]:
        return False
    if any(board[r][col] == num for r in range(9)):
        return False
    box_r, box_c = 3 * (row // 3), 3 * (col // 3)
    for r in range(box_r, box_r + 3):
        for c in range(box_c, box_c + 3):
            if board[r][c] == num:
                return False
    return True


def _solve(board: list[list[int]]) -> bool:
    """Solve the board in place using backtracking."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for num in nums:
                    if _is_valid(board, r, c, num):
                        board[r][c] = num
                        if _solve(board):
                            return True
                        board[r][c] = 0
                return False
    return True


def generate_puzzle(clues: int = 36) -> tuple[list[list[int]], list[list[int]]]:
    """Generate a Sudoku puzzle.

    Returns (puzzle, solution) where puzzle has 0s for empty cells.
    clues: number of filled cells (17-80). Lower = harder.
    """
    solution = [[0] * 9 for _ in range(9)]
    _solve(solution)

    puzzle = deepcopy(solution)
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    to_remove = 81 - clues
    for r, c in cells[:to_remove]:
        puzzle[r][c] = 0

    return puzzle, solution


def check_board(board: list[list[int]]) -> list[tuple[int, int]]:
    """Return list of (row, col) positions with errors."""
    errors = []
    for r in range(9):
        for c in range(9):
            val = board[r][c]
            if val == 0:
                continue
            # Temporarily remove to check
            board[r][c] = 0
            if not _is_valid(board, r, c, val):
                errors.append((r, c))
            board[r][c] = val
    return errors


DIFFICULTY = {
    "Easy": 45,
    "Medium": 36,
    "Hard": 27,
}
