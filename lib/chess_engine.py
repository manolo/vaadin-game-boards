"""Chess game logic wrapper with pluggable engines (Snakefish / Stockfish)."""

import shutil
import warnings
import chess
import chess.svg

from .uci_engine import UCIEngine
from .snakefish.chessboard import ChessBoard as SnakefishBoard
from .snakefish.constants import Piece as SfPiece
from .snakefish import search as sf_search

# Pre-generated SVG strings for each piece (from python-chess)
PIECE_SVGS: dict[tuple[int, bool], str] = {}
for _pt in chess.PIECE_TYPES:
    for _color in chess.COLORS:
        PIECE_SVGS[(_pt, _color)] = str(chess.svg.piece(chess.Piece(_pt, _color)))

# Map snakefish promotion pieces to python-chess
_SF_PROMO_MAP = {
    SfPiece.QUEEN: chess.QUEEN,
    SfPiece.ROOK: chess.ROOK,
    SfPiece.BISHOP: chess.BISHOP,
    SfPiece.KNIGHT: chess.KNIGHT,
}

SNAKEFISH_DEPTH = 4
STOCKFISH_TIME_MS = 500

# Detect Stockfish binary
STOCKFISH_PATH = shutil.which("stockfish")

ENGINE_SNAKEFISH = "Snakefish"
ENGINE_STOCKFISH = "Stockfish"

AVAILABLE_ENGINES = [ENGINE_SNAKEFISH]
if STOCKFISH_PATH:
    AVAILABLE_ENGINES.append(ENGINE_STOCKFISH)


class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.player_color: bool = chess.WHITE
        self._engine_name = ENGINE_SNAKEFISH
        self._sf_board = SnakefishBoard()
        self._sf_board.init_game()
        self._stockfish: UCIEngine | None = None
        self.move_stack_display: list[str] = []
        self._redo_stack: list[chess.Move] = []

    @property
    def engine_name(self) -> str:
        return self._engine_name

    def set_engine(self, name: str, reset: bool = True):
        """Switch engine. Optionally starts a new game."""
        if name not in AVAILABLE_ENGINES:
            return
        self._engine_name = name
        if reset:
            self.new_game()

    def new_game(self):
        self.board.reset()
        self.move_stack_display.clear()
        self._redo_stack.clear()
        # Reset snakefish board
        self._sf_board = SnakefishBoard()
        self._sf_board.init_game()
        # Reset stockfish
        if self._engine_name == ENGINE_STOCKFISH:
            self._ensure_stockfish()
            self._stockfish.set_fen_position(self.board.fen())

    def load_moves(self, uci_moves: str) -> bool:
        """Replay a space-separated list of UCI moves. Returns True if successful."""
        self.board.reset()
        self.move_stack_display.clear()
        if not uci_moves or not uci_moves.strip():
            self._build_sf_board_from_position()
            return True
        try:
            # Support dot, comma, and space separators
            for ch in ".,' ":
                if ch in uci_moves:
                    sep = ch
                    break
            else:
                sep = "."
            for uci in uci_moves.strip().split(sep):
                move = chess.Move.from_uci(uci)
                if move not in self.board.legal_moves:
                    self.board.reset()
                    self.move_stack_display.clear()
                    return False
                san = self.board.san(move)
                self.board.push(move)
                self.move_stack_display.append(san)
        except (ValueError, IndexError):
            self.board.reset()
            self.move_stack_display.clear()
            return False
        self._build_sf_board_from_position()
        if self._engine_name == ENGINE_STOCKFISH:
            self._ensure_stockfish()
            self._stockfish.set_fen_position(self.board.fen())
        return True

    @property
    def uci_moves(self) -> str:
        """Return all moves as a dot-separated UCI string (cookie-safe)."""
        return ".".join(m.uci() for m in self.board.move_stack)

    def _build_sf_board_from_position(self):
        """Build snakefish board from current python-chess board position."""
        from .snakefish.constants import (
            Color as SfColor, Piece as SfPieceType,
            CASTLE_WK, CASTLE_WQ, CASTLE_BK, CASTLE_BQ,
        )
        sf = SnakefishBoard()
        piece_map = {
            chess.PAWN: SfPieceType.PAWN, chess.KNIGHT: SfPieceType.KNIGHT,
            chess.BISHOP: SfPieceType.BISHOP, chess.ROOK: SfPieceType.ROOK,
            chess.QUEEN: SfPieceType.QUEEN, chess.KING: SfPieceType.KING,
        }
        color_map = {chess.WHITE: SfColor.WHITE, chess.BLACK: SfColor.BLACK}
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                sf.set_square(sq, piece_map[piece.piece_type], color_map[piece.color])
        sf.color = color_map[self.board.turn]

        # Sync castling rights
        cr = 0
        if self.board.has_kingside_castling_rights(chess.WHITE):
            cr |= CASTLE_WK
        if self.board.has_queenside_castling_rights(chess.WHITE):
            cr |= CASTLE_WQ
        if self.board.has_kingside_castling_rights(chess.BLACK):
            cr |= CASTLE_BK
        if self.board.has_queenside_castling_rights(chess.BLACK):
            cr |= CASTLE_BQ
        sf.castling_rights = cr

        # Sync en passant
        if self.board.ep_square is not None:
            sf.ep_square = self.board.ep_square
        else:
            sf.ep_square = -1

        sf.halfmove_clock = self.board.halfmove_clock

        # Compute Zobrist hash
        from .snakefish.zobrist import compute_hash
        sf.zobrist_hash = compute_hash(sf)

        self._sf_board = sf

    def _ensure_stockfish(self):
        if self._stockfish is None and STOCKFISH_PATH:
            self._stockfish = UCIEngine(
                path=STOCKFISH_PATH,
                depth=15,
                threads=1,
                hash_mb=64,
            )
            self._stockfish.set_skill_level(10)

    def get_piece_at(self, square: int) -> str | None:
        piece = self.board.piece_at(square)
        if piece is None:
            return None
        return PIECE_SYMBOLS[piece.piece_type][piece.color]

    def get_legal_moves_from(self, square: int) -> list[int]:
        return [
            move.to_square
            for move in self.board.legal_moves
            if move.from_square == square
        ]

    def is_own_piece(self, square: int) -> bool:
        piece = self.board.piece_at(square)
        return piece is not None and piece.color == self.player_color

    def make_move(self, from_sq: int, to_sq: int) -> bool:
        """Attempt to make a player move. Returns True if successful."""
        piece = self.board.piece_at(from_sq)
        promotion = None
        if piece and piece.piece_type == chess.PAWN:
            rank = chess.square_rank(to_sq)
            if rank == 0 or rank == 7:
                promotion = chess.QUEEN

        move = chess.Move(from_sq, to_sq, promotion=promotion)
        if move in self.board.legal_moves:
            self._redo_stack.clear()
            san = self.board.san(move)
            self.board.push(move)
            self._build_sf_board_from_position()
            if self._stockfish and self._engine_name == ENGINE_STOCKFISH:
                self._stockfish.set_fen_position(self.board.fen())
            self.move_stack_display.append(san)
            return True
        return False

    def engine_move(self) -> bool:
        """Let the selected engine make a move. Returns True if a move was made."""
        if self.is_game_over:
            return False

        if self._engine_name == ENGINE_STOCKFISH:
            return self._stockfish_move()
        else:
            return self._snakefish_move()

    def _snakefish_move(self) -> bool:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            sf_move = sf_search.best_move(self._sf_board, SNAKEFISH_DEPTH)

        if sf_move is None:
            return False

        from_sq = sf_move.src
        to_sq = sf_move.dest
        promotion = _SF_PROMO_MAP.get(sf_move.promo) if sf_move.promo else None

        move = chess.Move(from_sq, to_sq, promotion=promotion)
        if move not in self.board.legal_moves:
            return False

        san = self.board.san(move)
        self.board.push(move)
        self._build_sf_board_from_position()
        self.move_stack_display.append(san)
        return True

    def _stockfish_move(self) -> bool:
        self._ensure_stockfish()
        self._stockfish.set_fen_position(self.board.fen())
        best = self._stockfish.get_best_move_time(STOCKFISH_TIME_MS)
        if best is None:
            return False

        move = chess.Move.from_uci(best)
        if move not in self.board.legal_moves:
            return False

        san = self.board.san(move)
        self.board.push(move)
        self._build_sf_board_from_position()
        self._stockfish.set_fen_position(self.board.fen())
        self.move_stack_display.append(san)
        return True

    def undo(self) -> bool:
        """Undo the last two moves (player + engine). Returns True if successful."""
        undone = 0
        while undone < 2 and self.board.move_stack:
            move = self.board.pop()
            self._redo_stack.append(move)
            if self.move_stack_display:
                self.move_stack_display.pop()
            undone += 1
        if undone > 0:
            self._build_sf_board_from_position()
            if self._stockfish and self._engine_name == ENGINE_STOCKFISH:
                self._stockfish.set_fen_position(self.board.fen())
            return True
        return False

    def redo(self) -> bool:
        """Redo up to two moves from the redo stack. Returns True if successful."""
        redone = 0
        while redone < 2 and self._redo_stack:
            move = self._redo_stack.pop()
            if move not in self.board.legal_moves:
                break
            san = self.board.san(move)
            self.board.push(move)
            self.move_stack_display.append(san)
            redone += 1
        if redone > 0:
            self._build_sf_board_from_position()
            if self._stockfish and self._engine_name == ENGINE_STOCKFISH:
                self._stockfish.set_fen_position(self.board.fen())
            return True
        return False

    @property
    def can_undo(self) -> bool:
        return len(self.board.move_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def set_player_color(self, color: bool):
        self.player_color = color

    @property
    def is_players_turn(self) -> bool:
        return self.board.turn == self.player_color

    @property
    def turn(self) -> str:
        return "White" if self.board.turn == chess.WHITE else "Black"

    @property
    def is_check(self) -> bool:
        return self.board.is_check()

    @property
    def is_checkmate(self) -> bool:
        return self.board.is_checkmate()

    @property
    def is_stalemate(self) -> bool:
        return self.board.is_stalemate()

    @property
    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    @property
    def status_text(self) -> str:
        if self.is_checkmate:
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            return f"Checkmate! {winner} wins!"
        if self.is_stalemate:
            return "Stalemate - Draw!"
        if self.is_game_over:
            return "Game over - Draw!"
        if self.is_players_turn:
            status = "Your turn"
        else:
            status = "Engine thinking..."
        if self.is_check:
            status += " (Check!)"
        return status

    @property
    def last_move(self) -> tuple[int, int] | None:
        if self.board.move_stack:
            move = self.board.peek()
            return (move.from_square, move.to_square)
        return None
