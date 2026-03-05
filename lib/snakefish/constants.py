from enum import IntEnum

class Color(IntEnum):
    WHITE = 0
    BLACK = 1

    def __invert__(self):
        if self == Color.WHITE:
            return Color.BLACK
        else:
            return Color.WHITE


class Piece(IntEnum):
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5

class Rank(IntEnum):
    ONE = 0
    TWO = 1
    THREE = 2
    FOUR = 3
    FIVE = 4
    SIX = 5
    SEVEN = 6
    EIGHT = 7

class File(IntEnum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6
    H = 7

# Castling rights flags
CASTLE_WK = 1   # White kingside
CASTLE_WQ = 2   # White queenside
CASTLE_BK = 4   # Black kingside
CASTLE_BQ = 8   # Black queenside
CASTLE_ALL = CASTLE_WK | CASTLE_WQ | CASTLE_BK | CASTLE_BQ

# Key square indices
E1 = 4;  G1 = 6;  C1 = 2;  H1 = 7;  A1 = 0;  D1 = 3;  F1 = 5;  B1 = 1
E8 = 60; G8 = 62; C8 = 58; H8 = 63; A8 = 56; D8 = 59; F8 = 61; B8 = 57

# Castling rights mask: indexed by square, AND with castling_rights when
# a piece moves from or is captured on that square.
CASTLING_RIGHTS_MASK = [CASTLE_ALL] * 64
CASTLING_RIGHTS_MASK[E1] = CASTLE_ALL & ~(CASTLE_WK | CASTLE_WQ)
CASTLING_RIGHTS_MASK[H1] = CASTLE_ALL & ~CASTLE_WK
CASTLING_RIGHTS_MASK[A1] = CASTLE_ALL & ~CASTLE_WQ
CASTLING_RIGHTS_MASK[E8] = CASTLE_ALL & ~(CASTLE_BK | CASTLE_BQ)
CASTLING_RIGHTS_MASK[H8] = CASTLE_ALL & ~CASTLE_BK
CASTLING_RIGHTS_MASK[A8] = CASTLE_ALL & ~CASTLE_BQ
