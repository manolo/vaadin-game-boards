from . import tables
from . import bitboard
from .bitboard import _M
from .constants import (
    Rank, File, Color, Piece,
    CASTLE_WK, CASTLE_WQ, CASTLE_BK, CASTLE_BQ,
    E1, G1, C1, D1, F1, B1,
    E8, G8, C8, D8, F8, B8,
)
from .move import Move


# ---------------------------------------------------------------------------
# Sliding piece attack helpers (raw int sq, raw int occupancy)
# ---------------------------------------------------------------------------

def get_diag_moves_bb(i, occ):
    f = i & 7
    occ = tables.DIAG_MASKS[i] & occ
    occ = ((tables.FILES[File.A] * occ) & _M) >> 56
    occ = (tables.FILES[File.A] * tables.FIRST_RANK_MOVES[f][occ]) & _M
    return tables.DIAG_MASKS[i] & occ


def get_antidiag_moves_bb(i, occ):
    f = i & 7
    occ = tables.ANTIDIAG_MASKS[i] & occ
    occ = ((tables.FILES[File.A] * occ) & _M) >> 56
    occ = (tables.FILES[File.A] * tables.FIRST_RANK_MOVES[f][occ]) & _M
    return tables.ANTIDIAG_MASKS[i] & occ


def get_rank_moves_bb(i, occ):
    f = i & 7
    occ = tables.RANK_MASKS[i] & occ
    occ = ((tables.FILES[File.A] * occ) & _M) >> 56
    occ = (tables.FILES[File.A] * tables.FIRST_RANK_MOVES[f][occ]) & _M
    return tables.RANK_MASKS[i] & occ


def get_file_moves_bb(i, occ):
    f = i & 7
    occ = tables.FILES[File.A] & (occ >> f)
    occ = ((tables.A1H8_DIAG * occ) & _M) >> 56
    first_rank_index = (i ^ 56) >> 3
    occ = (tables.A1H8_DIAG * tables.FIRST_RANK_MOVES[first_rank_index][occ]) & _M
    return (tables.FILES[File.H] & occ) >> (f ^ 7)


def get_bishop_attacks(sq, occ):
    return ((get_diag_moves_bb(sq, occ) ^ get_antidiag_moves_bb(sq, occ))
            & _M)


def get_rook_attacks(sq, occ):
    return ((get_rank_moves_bb(sq, occ) ^ get_file_moves_bb(sq, occ))
            & _M)


# ---------------------------------------------------------------------------
# Piece moveset functions (return bitboard of target squares)
# ---------------------------------------------------------------------------

def get_king_moves_bb(sq, board):
    return tables.KING_MOVES[sq] & (~board.combined_color[board.color] & _M)


def get_knight_moves_bb(sq, board):
    return tables.KNIGHT_MOVES[sq] & (~board.combined_color[board.color] & _M)


def get_pawn_moves_bb(sq, board):
    me = board.color
    opp = ~me
    opp_pieces = board.combined_color[opp]

    # EP target is also a valid attack target
    ep_bb = 0
    if board.ep_square >= 0:
        ep_bb = 1 << board.ep_square

    attacks = tables.PAWN_ATTACKS[me][sq] & (opp_pieces | ep_bb)

    quiets = 0
    if me == Color.WHITE:
        one_step = (1 << (sq + 8)) & ~board.combined_all
        if one_step:
            quiets = tables.PAWN_QUIETS[me][sq] & ~board.combined_all
    else:
        one_step = (1 << (sq - 8)) & ~board.combined_all
        if one_step:
            quiets = tables.PAWN_QUIETS[me][sq] & ~board.combined_all

    return attacks | quiets


def get_bishop_moves_bb(sq, board):
    return get_bishop_attacks(sq, board.combined_all) & (~board.combined_color[board.color] & _M)


def get_rook_moves_bb(sq, board):
    return get_rook_attacks(sq, board.combined_all) & (~board.combined_color[board.color] & _M)


def get_queen_moves_bb(sq, board):
    return get_rook_moves_bb(sq, board) | get_bishop_moves_bb(sq, board)


# ---------------------------------------------------------------------------
# Attack detection
# ---------------------------------------------------------------------------

def is_attacked(board, sq, by_color):
    """Check if square `sq` is attacked by `by_color`."""
    occ = board.combined_all

    # Pawn attacks: use the *defender's* pawn attack table
    defender = ~by_color
    if tables.PAWN_ATTACKS[defender][sq] & board.pieces[by_color][Piece.PAWN]:
        return True

    if tables.KNIGHT_MOVES[sq] & board.pieces[by_color][Piece.KNIGHT]:
        return True

    if tables.KING_MOVES[sq] & board.pieces[by_color][Piece.KING]:
        return True

    bishops_queens = board.pieces[by_color][Piece.BISHOP] | board.pieces[by_color][Piece.QUEEN]
    if get_bishop_attacks(sq, occ) & bishops_queens:
        return True

    rooks_queens = board.pieces[by_color][Piece.ROOK] | board.pieces[by_color][Piece.QUEEN]
    if get_rook_attacks(sq, occ) & rooks_queens:
        return True

    return False


def in_check(board):
    """Check if the side to move is in check."""
    king_bb = board.pieces[board.color][Piece.KING]
    if not king_bb:
        return False
    king_sq = bitboard.lsb_bitscan(king_bb)
    return is_attacked(board, king_sq, ~board.color)


# ---------------------------------------------------------------------------
# Move generators
# ---------------------------------------------------------------------------

def gen_piece_moves(src, board, piece):
    if piece == Piece.PAWN:
        moveset = get_pawn_moves_bb(src, board)
        src_bb = 1 << src
        white_promote = src_bb & tables.RANKS[Rank.SEVEN] != 0
        black_promote = src_bb & tables.RANKS[Rank.TWO] != 0
        if (board.color == Color.WHITE and white_promote) or (board.color == Color.BLACK and black_promote):
            for dest in bitboard.occupied_squares(moveset):
                yield Move(src, dest, Piece.QUEEN)
                yield Move(src, dest, Piece.ROOK)
                yield Move(src, dest, Piece.KNIGHT)
                yield Move(src, dest, Piece.BISHOP)
            return
    elif piece == Piece.KNIGHT:
        moveset = get_knight_moves_bb(src, board)
    elif piece == Piece.BISHOP:
        moveset = get_bishop_moves_bb(src, board)
    elif piece == Piece.ROOK:
        moveset = get_rook_moves_bb(src, board)
    elif piece == Piece.QUEEN:
        moveset = get_queen_moves_bb(src, board)
    elif piece == Piece.KING:
        moveset = get_king_moves_bb(src, board)
    else:
        raise RuntimeError("Invalid piece: %s" % str(piece))

    for dest in bitboard.occupied_squares(moveset):
        yield Move(src, dest)


def gen_castling_moves(board):
    """Generate castling moves if legal."""
    me = board.color
    opp = ~me
    rights = board.castling_rights
    occ = board.combined_all

    if me == Color.WHITE:
        if rights & CASTLE_WK:
            # Squares between king and rook must be empty, king not in/through check
            if not (occ & ((1 << F1) | (1 << G1))):
                if (not is_attacked(board, E1, opp) and
                    not is_attacked(board, F1, opp) and
                    not is_attacked(board, G1, opp)):
                    yield Move(E1, G1)
        if rights & CASTLE_WQ:
            if not (occ & ((1 << D1) | (1 << C1) | (1 << B1))):  # b1,c1,d1
                if (not is_attacked(board, E1, opp) and
                    not is_attacked(board, D1, opp) and
                    not is_attacked(board, C1, opp)):
                    yield Move(E1, C1)
    else:
        if rights & CASTLE_BK:
            if not (occ & ((1 << F8) | (1 << G8))):  # f8, g8
                if (not is_attacked(board, E8, opp) and
                    not is_attacked(board, F8, opp) and
                    not is_attacked(board, G8, opp)):
                    yield Move(E8, G8)
        if rights & CASTLE_BQ:
            if not (occ & ((1 << D8) | (1 << C8) | (1 << B8))):  # b8,c8,d8
                if (not is_attacked(board, E8, opp) and
                    not is_attacked(board, D8, opp) and
                    not is_attacked(board, C8, opp)):
                    yield Move(E8, C8)


def gen_moves(board):
    """Generate all pseudo-legal moves (including castling)."""
    for piece_type in range(6):
        piece_bb = board.pieces[board.color][piece_type]
        piece = Piece(piece_type)
        for src in bitboard.occupied_squares(piece_bb):
            yield from gen_piece_moves(src, board, piece)
    yield from gen_castling_moves(board)


def leaves_in_check(board, move):
    """Check if making `move` leaves the side to move in check."""
    new_board = board.apply_move(move)
    # After apply_move, color is flipped. We want to check if the *mover* is in check.
    me = board.color
    king_bb = new_board.pieces[me][Piece.KING]
    if not king_bb:
        return True
    king_sq = bitboard.lsb_bitscan(king_bb)
    return is_attacked(new_board, king_sq, ~me)


def gen_legal_moves(board):
    """Generate all legal moves."""
    for move in gen_moves(board):
        if not leaves_in_check(board, move):
            yield move


# ---------------------------------------------------------------------------
# Move ordering helpers (for search)
# ---------------------------------------------------------------------------

# Piece values for MVV-LVA ordering
_PIECE_VALUES = [100, 300, 300, 500, 900, 20000]


def score_move(board, move, tt_move=None):
    """Score a move for ordering. Higher = searched first."""
    if tt_move and move.src == tt_move.src and move.dest == tt_move.dest:
        return 1_000_000

    score = 0
    dest_bb = 1 << move.dest
    opp = ~board.color

    # Capture scoring: MVV-LVA
    for p in range(6):
        if board.pieces[opp][p] & dest_bb:
            score += 10 * _PIECE_VALUES[p]  # victim value
            # Subtract attacker value
            attacker = board.piece_on(move.src, board.color)
            if attacker is not None:
                score -= _PIECE_VALUES[attacker]
            break

    # EP capture
    if board.ep_square >= 0 and move.dest == board.ep_square:
        attacker = board.piece_on(move.src, board.color)
        if attacker == Piece.PAWN:
            score += 10 * _PIECE_VALUES[Piece.PAWN] - _PIECE_VALUES[Piece.PAWN]

    # Promotions
    if move.promo is not None:
        score += _PIECE_VALUES[move.promo]

    return score


def gen_legal_moves_ordered(board, tt_move=None):
    """Generate legal moves sorted by score (best first)."""
    moves = list(gen_legal_moves(board))
    moves.sort(key=lambda m: score_move(board, m, tt_move), reverse=True)
    return moves


def gen_legal_captures_ordered(board):
    """Generate legal captures sorted by MVV-LVA (for quiescence search)."""
    captures = []
    opp_pieces = board.combined_color[~board.color]
    ep_bb = (1 << board.ep_square) if board.ep_square >= 0 else 0
    target = opp_pieces | ep_bb

    for move in gen_legal_moves(board):
        if (1 << move.dest) & target:
            captures.append(move)

    captures.sort(key=lambda m: score_move(board, m), reverse=True)
    return captures
