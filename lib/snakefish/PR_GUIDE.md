# Snakefish Engine Improvements - PR Guide

This document describes all improvements made to the snakefish engine and how to apply
them to the original numpy-based snakefish library.

## Overview of Changes

| Category | Change | Files |
|----------|--------|-------|
| Performance | `int.bit_count()` for pop_count | `bitboard.py` |
| Performance | Raw int squares instead of Square objects | All files |
| Performance | `__slots__` on Move class | `move.py` |
| Correctness | Castling support | `constants.py`, `chessboard.py`, `movegen.py` |
| Correctness | En passant support | `chessboard.py`, `movegen.py` |
| Correctness | Stalemate vs checkmate distinction | `search.py` |
| Correctness | Mate-distance scoring | `search.py` |
| Search | MVV-LVA move ordering | `movegen.py` |
| Search | Quiescence search | `search.py` |
| Search | Iterative deepening | `search.py` |
| Search | Zobrist hashing + transposition table | `zobrist.py`, `search.py` |
| Search | Null move pruning | `search.py`, `chessboard.py` |
| Evaluation | Piece-square tables (MG + EG) | `pst.py`, `evaluation.py` |
| Evaluation | Game phase blending | `evaluation.py` |
| Evaluation | Pawn structure (doubled, isolated, passed) | `evaluation.py` |
| Evaluation | King safety (pawn shield, open files) | `evaluation.py` |
| Evaluation | Bishop pair bonus | `evaluation.py` |

## Phase 1: Performance - Raw Int Squares

### Problem
Every call to `occupied_squares()` created `Square` objects, and every bitboard
operation went through `sq.to_bitboard()`. This added significant overhead in the
inner loops.

### Solution
- `occupied_squares()` now yields raw `int` indices (0-63)
- `is_set()`, `clear_square()`, `set_square()` accept raw ints, use `1 << sq`
- `Move.src` and `Move.dest` store plain ints
- `pop_count()` uses `bb.bit_count()` (Python 3.10+ C-optimized builtin)
- `Move` class uses `__slots__` to reduce memory

### numpy-specific notes
In the original numpy-based code:
- Replace `np.uint64` arithmetic with Python `int` where possible, or
  keep uint64 but use `int(sq)` when indexing lookup tables
- `np.count_nonzero(np.unpackbits(...))` can be replaced with `int(bb).bit_count()`

## Phase 2: Castling

### New constants (`constants.py`)
```python
CASTLE_WK = 1; CASTLE_WQ = 2; CASTLE_BK = 4; CASTLE_BQ = 8
E1 = 4; G1 = 6; C1 = 2; H1 = 7; A1 = 0; D1 = 3; F1 = 5
E8 = 60; G8 = 62; C8 = 58; H8 = 63; A8 = 56; D8 = 59; F8 = 61
CASTLING_RIGHTS_MASK[64]  # AND mask indexed by square
```

### Board state (`chessboard.py`)
- Added `castling_rights`, `ep_square`, `halfmove_clock` fields
- `apply_move()` handles castling rook movement
- `apply_move()` updates castling rights via `CASTLING_RIGHTS_MASK`
- `init_game()` sets `castling_rights = CASTLE_ALL`

### Move generation (`movegen.py`)
- `gen_castling_moves(board)`: checks rights, empty squares, and not-through-check
- `is_attacked(board, sq, by_color)`: general attack detection (extracted from `leaves_in_check`)
- `in_check(board)`: convenience wrapper

### numpy-specific notes
- Castling constants are plain Python ints, no numpy changes needed
- `CASTLING_RIGHTS_MASK` is a plain list, works the same way
- `apply_move` copies arrays; with numpy, use `.copy()` on the uint64 arrays

## Phase 3: En Passant

### Board state
- `ep_square` field (-1 when no EP target)
- `apply_move()` removes captured pawn on EP capture
- `apply_move()` sets EP target on double pawn push

### Move generation
- `get_pawn_moves_bb()` adds EP square bitboard to attack targets
- Legal move filtering catches EP-related discovered checks

## Phase 4: Stalemate + Mate Distance

### Changes in `search.py`
- When no legal moves: check `in_check()` to distinguish checkmate vs stalemate
- Checkmate: `-(CHECKMATE_SCORE - ply)` (faster mates score higher)
- Stalemate: `return 0`
- `ply` parameter threaded through negamax

## Phase 5: Search Enhancements

### Move Ordering (MVV-LVA)
- `score_move(board, move, tt_move)` in `movegen.py`
- Captures scored: 10 * victim_value - attacker_value
- TT move gets score 1,000,000 (always first)
- Promotions add piece value
- `gen_legal_moves_ordered(board, tt_move)` returns sorted list
- `gen_legal_captures_ordered(board)` for quiescence

### Quiescence Search
- At depth 0, search captures until position is quiet
- Stand-pat evaluation with delta pruning (margin = 1000 cp)
- Prevents horizon effect

### Iterative Deepening
- `best_move(board, max_depth)` loops depth 1 to max_depth
- Previous iteration's best move passed via TT to next iteration
- Natural integration with TT

### Zobrist Hashing + Transposition Table
- New file `zobrist.py` with deterministic random keys
- Keys: piece/color/square, side-to-move, castling rights, EP square
- `compute_hash(board)` for full computation
- TT: 1M entries, replacement by depth
- Entries: (hash, depth, score, flag, best_move_src, best_move_dest)
- Flags: EXACT, LOWER (beta cutoff), UPPER (all-node)

### Null Move Pruning
- If depth >= 3 and not in check, try null move with R=2 reduction
- Zero-window search: `(-beta, -beta + 1)`
- `make_null_move()` on ChessBoard flips side, clears EP

### numpy-specific notes
- Zobrist keys are plain Python ints (64-bit); numpy uint64 XOR works the same
- TT is a plain Python list; could use numpy structured array for cache efficiency
- Move ordering sorts Python lists; no numpy-specific changes needed

## Phase 6: Evaluation

### Piece-Square Tables (`pst.py`)
- Separate MG and EG tables for all 6 piece types
- Values from Chess Programming Wiki (Simplified Evaluation Function)
- Tables indexed by square (0=a1, 63=h8), white perspective
- Black mirrored via `sq ^ 56`
- Base piece values: MG and EG variants

### Game Phase Blending
- Phase = sum of piece weights (N=1, B=1, R=2, Q=4), max 24
- Score = (mg * phase + eg * (24 - phase)) / 24
- Smooth transition from opening/middlegame to endgame

### Pawn Structure
- Doubled pawns: penalty per extra pawn on same file
- Isolated pawns: penalty when no friendly pawns on adjacent files
- Passed pawns: bonus scaled by rank advancement (quadratic)

### King Safety
- Pawn shield: bonus for friendly pawns on files adjacent to king
- Open files: penalty for files near king with no friendly pawns

### Bishop Pair
- +30 MG / +50 EG bonus for having 2+ bishops

### Removed
- `eval_center()` - subsumed by PST
- `eval_mobility()` - crude proxy replaced by PST positional values

### numpy-specific notes
- PST tables are plain Python lists; could be numpy arrays for vectorized lookup
- `bit_count()` calls in evaluation are Python int method; numpy equivalent is
  `np.unpackbits` or converting to int first

## Testing Recommendations

### Perft Tests
Run perft (count leaf nodes at depth N) to verify move generation correctness:
- Starting position, depth 1: 20 nodes
- Starting position, depth 2: 400 nodes
- Starting position, depth 3: 8902 nodes
- Kiwipete position (`r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -`):
  depth 1 = 48, depth 2 = 2039

### Integration Test
The engine is used via `chess_engine.py` which validates every snakefish move
against python-chess legal move list. If snakefish generates an illegal move,
`_snakefish_move()` returns False and the move is rejected.

### Smoke Test
```python
from snakefish.chessboard import ChessBoard
from snakefish import search

board = ChessBoard()
board.init_game()
move = search.best_move(board, 4)
print(f"Best: {move.src} -> {move.dest}")  # Should complete in ~1s
```
