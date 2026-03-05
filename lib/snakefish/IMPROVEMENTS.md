# Snakefish Improvement Roadmap

Current state: pure-Python bitboard chess engine with alpha-beta search, iterative
deepening, quiescence search, transposition table, null move pruning, piece-square
tables, and full chess rules (castling, en passant). Used as a fallback engine when
Stockfish binary is not available.

## Missing Chess Rules - ALL DONE

### Castling - DONE
- `apply_move` handles castling (king+rook double move)
- Castling rights tracked and updated on king/rook move or rook capture
- `gen_castling_moves` generates castling moves with legality checks
- Engine can castle and understands opponent castling

### En Passant - DONE
- `apply_move` removes the captured pawn on en passant
- EP target square tracked and propagated
- `get_pawn_moves_bb` generates en passant captures
- Full EP support in move generation and execution

### Stalemate vs Checkmate Distinction - DONE
- `negamax` returns `0` for stalemate, `-(CHECKMATE - ply)` for checkmate
- Mate-distance scoring prefers faster mates and delays getting mated
- Uses `is_attacked` / `in_check` for detection

### Fifty-Move Rule / Threefold Repetition
- Halfmove clock tracked in board state
- Not yet enforced in search (not critical for casual play)
- Position history for repetition detection not implemented

## Search Improvements - ALL DONE

### Move Ordering (MVV-LVA) - DONE
- Captures scored by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
- TT best move searched first (score 1,000,000)
- Promotions get bonus score
- `gen_legal_moves_ordered` and `gen_legal_captures_ordered`

### Iterative Deepening - DONE
- Search depth 1, then 2, then 3... up to max_depth
- Previous best move passed via TT to next iteration
- Natural foundation for future time management

### Quiescence Search - DONE
- At depth 0, searches captures until position is quiet
- Stand-pat evaluation with delta pruning (margin = 1000 cp)
- Prevents horizon effect for tactical accuracy

### Transposition Table - DONE
- Zobrist hashing with deterministic random keys
- 1M-entry TT with depth-based replacement
- Stores: hash, depth, score, flag (EXACT/LOWER/UPPER), best move
- Probed before search, stored after

### Null Move Pruning - DONE
- If depth >= 3 and not in check, try null move with R=2 reduction
- Zero-window search for efficiency
- `make_null_move()` on ChessBoard

## Evaluation Improvements - ALL DONE

### Piece-Square Tables - DONE
- MG and EG tables for all 6 piece types (CPW Simplified values)
- Separate base piece values for MG and EG
- Black tables mirrored via sq ^ 56

### Pawn Structure - DONE
- Doubled pawns penalty (per extra pawn on same file)
- Isolated pawns penalty (no friendly pawns on adjacent files)
- Passed pawns bonus (quadratic scaling by rank advancement)

### King Safety - DONE
- Pawn shield bonus (friendly pawns on adjacent files)
- Open file penalty near king

### Bishop Pair Bonus - DONE
- +30 MG / +50 EG for having 2+ bishops

### Endgame vs Middlegame - DONE
- Game phase computed from piece weights (N=1, B=1, R=2, Q=4)
- Score = blend of MG and EG evaluations based on phase

## Performance Improvements - PARTIALLY DONE

### int.bit_count() for pop_count - DONE
- `pop_count` uses `bb.bit_count()` (Python 3.10+ C-optimized)

### Reduce Object Allocation - DONE
- `occupied_squares` yields raw ints instead of Square objects
- `Move` uses `__slots__` and stores plain int src/dest
- All bitboard operations accept raw ints

### Make/Unmake Instead of Copy
- NOT DONE - would require significant refactor
- Current copy-based approach works well enough at depth 4
- Future optimization if deeper search is needed

## Remaining Work

1. **Time management** - stop iterative deepening when time runs out
2. **Killer moves** - remember non-capture moves that caused beta cutoffs
3. **History heuristic** - improve quiet move ordering based on search history
4. **Make/unmake** - avoid board copies for deeper search
5. **Repetition detection** - threefold repetition draw
6. **Late move reductions** - reduce depth for moves late in the move list
