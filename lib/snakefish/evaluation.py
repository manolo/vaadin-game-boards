"""Position evaluation with piece-square tables, pawn structure, and king safety."""

from . import bitboard
from . import tables
from .constants import Color, Piece, File
from . import pst

CHECKMATE_SCORE = 1_000_000

# File bitboards for pawn structure analysis
_FILES = tables.FILES


def evaluate(board):
    """Evaluate the position from the side-to-move's perspective."""
    mg_score = 0
    eg_score = 0
    phase = 0

    for color in (Color.WHITE, Color.BLACK):
        sign = 1 if color == board.color else -1

        for piece_type in range(6):
            bb = board.pieces[color][piece_type]
            count = bb.bit_count()

            # Material
            mg_score += sign * count * pst.PIECE_VALUE_MG[piece_type]
            eg_score += sign * count * pst.PIECE_VALUE_EG[piece_type]

            # Phase
            phase += count * pst.PHASE_WEIGHTS[piece_type]

            # PST values
            for sq in bitboard.occupied_squares(bb):
                # For white, use sq directly; for black, mirror vertically
                idx = sq if color == Color.WHITE else (sq ^ 56)
                mg_score += sign * pst.MG_TABLES[piece_type][idx]
                eg_score += sign * pst.EG_TABLES[piece_type][idx]

    # Bishop pair bonus
    for color in (Color.WHITE, Color.BLACK):
        sign = 1 if color == board.color else -1
        if board.pieces[color][Piece.BISHOP].bit_count() >= 2:
            mg_score += sign * 30
            eg_score += sign * 50

    # Pawn structure
    _eval_pawn_structure(board, board.color, 1, mg_score, eg_score)

    mg_pawn, eg_pawn = _pawn_structure_score(board)
    mg_score += mg_pawn
    eg_score += eg_pawn

    # King safety (middlegame only)
    mg_score += _king_safety(board)

    # Blend MG and EG based on game phase
    phase = min(phase, pst.TOTAL_PHASE)
    mg_weight = phase
    eg_weight = pst.TOTAL_PHASE - phase

    return (mg_score * mg_weight + eg_score * eg_weight) // pst.TOTAL_PHASE


def _pawn_structure_score(board):
    """Evaluate pawn structure: doubled, isolated, passed pawns."""
    mg = 0
    eg = 0

    for color in (Color.WHITE, Color.BLACK):
        sign = 1 if color == board.color else -1
        pawns = board.pieces[color][Piece.PAWN]
        opp_pawns = board.pieces[~color][Piece.PAWN]

        for f in range(8):
            file_pawns = pawns & _FILES[f]
            count = file_pawns.bit_count()

            # Doubled pawns penalty
            if count > 1:
                penalty = (count - 1) * 10
                mg -= sign * penalty
                eg -= sign * penalty * 2

            # Isolated pawns penalty (no friendly pawns on adjacent files)
            if count > 0:
                adjacent = 0
                if f > 0:
                    adjacent |= pawns & _FILES[f - 1]
                if f < 7:
                    adjacent |= pawns & _FILES[f + 1]
                if not adjacent:
                    mg -= sign * 15
                    eg -= sign * 20

        # Passed pawns bonus
        for sq in bitboard.occupied_squares(pawns):
            if _is_passed(sq, color, opp_pawns):
                rank = sq >> 3
                if color == Color.WHITE:
                    bonus = rank * rank * 3
                else:
                    bonus = (7 - rank) * (7 - rank) * 3
                mg += sign * bonus // 2
                eg += sign * bonus

    return mg, eg


def _is_passed(sq, color, opp_pawns):
    """Check if a pawn is passed (no opponent pawns blocking or on adjacent files ahead)."""
    f = sq & 7
    rank = sq >> 3

    for df in (f - 1, f, f + 1):
        if df < 0 or df > 7:
            continue
        file_mask = _FILES[df]
        blockers = opp_pawns & file_mask
        if not blockers:
            continue
        for opp_sq in bitboard.occupied_squares(blockers):
            opp_rank = opp_sq >> 3
            if color == Color.WHITE and opp_rank > rank:
                return False
            if color == Color.BLACK and opp_rank < rank:
                return False
    return True


def _eval_pawn_structure(board, color, sign, mg, eg):
    """Placeholder integrated into _pawn_structure_score."""
    pass


def _king_safety(board):
    """Evaluate king safety (pawn shield, open files near king)."""
    score = 0

    for color in (Color.WHITE, Color.BLACK):
        sign = 1 if color == board.color else -1
        king_bb = board.pieces[color][Piece.KING]
        if not king_bb:
            continue
        king_sq = bitboard.lsb_bitscan(king_bb)
        king_file = king_sq & 7
        pawns = board.pieces[color][Piece.PAWN]

        # Pawn shield bonus: count friendly pawns in front of king on adjacent files
        shield = 0
        for df in (king_file - 1, king_file, king_file + 1):
            if 0 <= df <= 7:
                file_pawns = pawns & _FILES[df]
                if file_pawns:
                    shield += 1

        score += sign * shield * 10

        # Open file penalty near king
        for df in (king_file - 1, king_file, king_file + 1):
            if 0 <= df <= 7:
                if not (pawns & _FILES[df]):
                    score -= sign * 15

    return score
