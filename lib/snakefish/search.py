"""Search with iterative deepening, alpha-beta, quiescence, TT, null move pruning."""

from . import movegen
from . import evaluation

# Transposition table
_TT_SIZE = 1 << 20  # ~1M entries
_TT_MASK = _TT_SIZE - 1

# TT flags
_EXACT = 0
_LOWER = 1  # beta cutoff (score >= beta)
_UPPER = 2  # all-node (score <= alpha)

# TT entry: (zobrist_hash, depth, score, flag, best_move_src, best_move_dest)
_tt = [None] * _TT_SIZE


def _tt_probe(h):
    entry = _tt[h & _TT_MASK]
    if entry is not None and entry[0] == h:
        return entry
    return None


def _tt_store(h, depth, score, flag, best_move):
    idx = h & _TT_MASK
    old = _tt[idx]
    # Replace if empty or shallower
    if old is None or old[1] <= depth:
        src = best_move.src if best_move else -1
        dest = best_move.dest if best_move else -1
        _tt[idx] = (h, depth, score, flag, src, dest)


def _find_tt_move(board, entry):
    """Reconstruct a Move object from TT entry if valid."""
    if entry is None or entry[4] < 0:
        return None
    from .move import Move
    return Move(entry[4], entry[5])


def quiescence(board, alpha, beta):
    """Quiescence search: evaluate captures until position is quiet."""
    stand_pat = evaluation.evaluate(board)

    if stand_pat >= beta:
        return beta

    # Delta pruning
    if stand_pat + 1000 < alpha:
        return alpha

    if stand_pat > alpha:
        alpha = stand_pat

    for move in movegen.gen_legal_captures_ordered(board):
        new_board = board.apply_move(move)
        score = -quiescence(new_board, -beta, -alpha)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board, depth, alpha, beta, ply, do_null=True):
    """Negamax with alpha-beta, TT, and null move pruning."""
    alpha_orig = alpha

    # TT probe
    h = board.zobrist_hash
    if not h:
        from .zobrist import compute_hash
        h = compute_hash(board)
        board.zobrist_hash = h

    entry = _tt_probe(h)
    tt_move = _find_tt_move(board, entry)

    if entry is not None and entry[1] >= depth:
        tt_score = entry[2]
        tt_flag = entry[3]
        if tt_flag == _EXACT:
            return tt_score
        elif tt_flag == _LOWER:
            alpha = max(alpha, tt_score)
        elif tt_flag == _UPPER:
            beta = min(beta, tt_score)
        if alpha >= beta:
            return tt_score

    # Quiescence at leaf
    if depth <= 0:
        return quiescence(board, alpha, beta)

    # Null move pruning
    if (do_null and depth >= 3 and not movegen.in_check(board)):
        null_board = board.make_null_move()
        null_score = -negamax(null_board, depth - 1 - 2, -beta, -beta + 1, ply + 1, False)
        if null_score >= beta:
            return beta

    best_move = None
    has_moves = False

    for move in movegen.gen_legal_moves_ordered(board, tt_move):
        has_moves = True
        new_board = board.apply_move(move)
        score = -negamax(new_board, depth - 1, -beta, -alpha, ply + 1, True)

        if score >= beta:
            _tt_store(h, depth, beta, _LOWER, move)
            return beta

        if score > alpha:
            alpha = score
            best_move = move

    if not has_moves:
        if movegen.in_check(board):
            return -(evaluation.CHECKMATE_SCORE - ply)
        return 0  # Stalemate

    # TT store
    if alpha <= alpha_orig:
        flag = _UPPER
    else:
        flag = _EXACT
    _tt_store(h, depth, alpha, flag, best_move)

    return alpha


def best_move(board, max_depth):
    """Iterative deepening search. Returns the best move."""
    best = None

    for depth in range(1, max_depth + 1):
        current_best = None
        alpha = -evaluation.CHECKMATE_SCORE - 1
        beta = evaluation.CHECKMATE_SCORE + 1

        # Get TT move from previous iteration
        h = board.zobrist_hash
        if not h:
            from .zobrist import compute_hash
            h = compute_hash(board)
            board.zobrist_hash = h
        entry = _tt_probe(h)
        tt_move = _find_tt_move(board, entry)

        for move in movegen.gen_legal_moves_ordered(board, tt_move):
            new_board = board.apply_move(move)
            score = -negamax(new_board, depth - 1, -beta, -alpha, 1, True)
            if score > alpha:
                alpha = score
                current_best = move

        if current_best is not None:
            best = current_best

    return best
