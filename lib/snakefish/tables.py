"""Pre-computed bitboard lookup tables for move generation."""

from . import bitboard
from .square import Square
from .constants import Rank, File, Color

_M = bitboard._M
EMPTY_BB = 0

RANKS = [(0x00000000000000FF << (8 * i)) & _M for i in range(8)]
FILES = [(0x0101010101010101 << i) & _M for i in range(8)]

RANK_MASKS = [RANKS[i // 8] for i in range(64)]
FILE_MASKS = [FILES[i % 8] for i in range(64)]

A1H8_DIAG = 0x8040201008040201
H1A8_ANTIDIAG = 0x0102040810204080

CENTER = 0x00003C3C3C3C0000


def _compute_diag_mask(i):
    diag = 8 * (i & 7) - (i & 56)
    north = -diag & (diag >> 31)
    south = diag & (-diag >> 31)
    return ((A1H8_DIAG >> south) << north) & _M

DIAG_MASKS = [_compute_diag_mask(i) for i in range(64)]


def _compute_antidiag_mask(i):
    diag = 56 - 8 * (i & 7) - (i & 56)
    north = -diag & (diag >> 31)
    south = diag & (-diag >> 31)
    return ((H1A8_ANTIDIAG >> south) << north) & _M

ANTIDIAG_MASKS = [_compute_antidiag_mask(i) for i in range(64)]


# -- King moves --

def _compute_king_moves(i):
    bb = 1 << i
    nw = ((bb & ~FILES[File.A]) << 7) & _M
    n  = (bb << 8) & _M
    ne = ((bb & ~FILES[File.H]) << 9) & _M
    e  = ((bb & ~FILES[File.H]) << 1) & _M
    se = (bb & ~FILES[File.H]) >> 7
    s  = bb >> 8
    sw = (bb & ~FILES[File.A]) >> 9
    w  = (bb & ~FILES[File.A]) >> 1
    return nw | n | ne | e | se | s | sw | w

KING_MOVES = [_compute_king_moves(i) for i in range(64)]


# -- Knight moves --

def _compute_knight_moves(i):
    bb = 1 << i
    m1 = ~(FILES[File.A] | FILES[File.B]) & _M
    m2 = ~FILES[File.A] & _M
    m3 = ~FILES[File.H] & _M
    m4 = ~(FILES[File.H] | FILES[File.G]) & _M

    s1 = ((bb & m1) << 6) & _M
    s2 = ((bb & m2) << 15) & _M
    s3 = ((bb & m3) << 17) & _M
    s4 = ((bb & m4) << 10) & _M
    s5 = (bb & m4) >> 6
    s6 = (bb & m3) >> 15
    s7 = (bb & m2) >> 17
    s8 = (bb & m1) >> 10
    return s1 | s2 | s3 | s4 | s5 | s6 | s7 | s8

KNIGHT_MOVES = [_compute_knight_moves(i) for i in range(64)]


# -- Pawn quiet moves --

def _compute_pawn_quiet_moves(color, i):
    bb = 1 << i
    starting_rank = RANKS[Rank.TWO] if color == Color.WHITE else RANKS[Rank.SEVEN]
    if color == Color.WHITE:
        s1 = (bb << 8) & _M
        s2 = ((bb & starting_rank) << 16) & _M
    else:
        s1 = bb >> 8
        s2 = (bb & starting_rank) >> 16
    return s1 | s2

PAWN_QUIETS = [[_compute_pawn_quiet_moves(color, i) for i in range(64)] for color in Color]


# -- Pawn attacks --

def _compute_pawn_attack_moves(color, i):
    bb = 1 << i
    if color == Color.WHITE:
        s1 = ((bb & ~FILES[File.A]) << 7) & _M
        s2 = ((bb & ~FILES[File.H]) << 9) & _M
    else:
        s1 = (bb & ~FILES[File.A]) >> 9
        s2 = (bb & ~FILES[File.H]) >> 7
    return s1 | s2

PAWN_ATTACKS = [[_compute_pawn_attack_moves(color, i) for i in range(64)] for color in Color]


# -- First rank moves (for sliding pieces) --

def _compute_first_rank_moves(i, occ):
    x = 1 << i
    occ = occ & 0xFF

    left_attacks = (x - 1) & 0xFF
    left_blockers = left_attacks & occ
    if left_blockers:
        leftmost = 1 << bitboard.msb_bitscan(left_blockers)
        left_garbage = (leftmost - 1) & 0xFF
        left_attacks ^= left_garbage

    right_attacks = ((~x) & ~(x - 1)) & 0xFF
    right_blockers = right_attacks & occ
    if right_blockers:
        rightmost = 1 << bitboard.lsb_bitscan(right_blockers)
        right_garbage = ((~rightmost) & ~(rightmost - 1)) & 0xFF
        right_attacks ^= right_garbage

    return left_attacks ^ right_attacks

FIRST_RANK_MOVES = [[_compute_first_rank_moves(i, occ) for occ in range(256)] for i in range(8)]
