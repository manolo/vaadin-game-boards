"""Zobrist hashing for transposition table."""

import random

from . import bitboard
from .constants import Color, Piece

# Deterministic seed for reproducibility
_rng = random.Random(0xDEADBEEF)

def _rand64():
    return _rng.getrandbits(64)

# piece_keys[color][piece][square]
PIECE_KEYS = [[[_rand64() for _ in range(64)] for _ in range(6)] for _ in range(2)]

SIDE_KEY = _rand64()

# castling_keys[0..15] for each combination of castling rights
CASTLING_KEYS = [_rand64() for _ in range(16)]

# ep_keys[0..63] for each possible EP file (only files 0-7 matter, but index by square)
EP_KEYS = [_rand64() for _ in range(64)]


def compute_hash(board):
    """Compute full Zobrist hash from scratch."""
    h = 0
    for color in range(2):
        for piece in range(6):
            bb = board.pieces[color][piece]
            for sq in bitboard.occupied_squares(bb):
                h ^= PIECE_KEYS[color][piece][sq]

    if board.color == Color.BLACK:
        h ^= SIDE_KEY

    h ^= CASTLING_KEYS[board.castling_rights]

    if board.ep_square >= 0:
        h ^= EP_KEYS[board.ep_square]

    return h
