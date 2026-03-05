"""Bitboard utilities using plain Python integers with 64-bit masking."""

# 64-bit mask -- Python ints are arbitrary precision, so we mask to emulate uint64.
_M = (1 << 64) - 1

EMPTY_BB = 0

# De Bruijn bit-scan lookup tables
_DEBRUIJN = 0x03f79d71b4cb0a89

_LSB_LOOKUP = [
     0,  1, 48,  2, 57, 49, 28,  3,
    61, 58, 50, 42, 38, 29, 17,  4,
    62, 55, 59, 36, 53, 51, 43, 22,
    45, 39, 33, 30, 24, 18, 12,  5,
    63, 47, 56, 27, 60, 41, 37, 16,
    54, 35, 52, 21, 44, 32, 23, 11,
    46, 26, 40, 15, 34, 20, 31, 10,
    25, 14, 19,  9, 13,  8,  7,  6,
]

_MSB_LOOKUP = [
     0, 47,  1, 56, 48, 27,  2, 60,
    57, 49, 41, 37, 28, 16,  3, 61,
    54, 58, 35, 52, 50, 42, 21, 44,
    38, 32, 29, 23, 17, 11,  4, 62,
    46, 55, 26, 59, 40, 36, 15, 53,
    34, 51, 20, 43, 31, 22, 10, 45,
    25, 39, 14, 33, 19, 30,  9, 24,
    13, 18,  8, 12,  7,  6,  5, 63,
]


def lsb_bitscan(bb):
    return _LSB_LOOKUP[(((bb & (-bb & _M)) * _DEBRUIJN) & _M) >> 58]


def msb_bitscan(bb):
    bb |= bb >> 1
    bb |= bb >> 2
    bb |= bb >> 4
    bb |= bb >> 8
    bb |= bb >> 16
    bb |= bb >> 32
    return _MSB_LOOKUP[((bb * _DEBRUIJN) & _M) >> 58]


def occupied_squares(bb):
    """Yield raw int square indices from a bitboard."""
    while bb:
        sq = lsb_bitscan(bb)
        yield sq
        bb &= bb - 1


def pop_count(bb):
    return bb.bit_count()


def is_set(bb, sq):
    return ((1 << sq) & bb) != 0


def clear_square(bb, sq):
    return (~(1 << sq) & _M) & bb


def set_square(bb, sq):
    return (1 << sq) | bb
