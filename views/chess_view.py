"""Chess game view built with PyXFlow."""

import asyncio

import chess
from pyxflow import Route, Menu, PageTitle, Request, Response
from pyxflow.components import (
    VerticalLayout, HorizontalLayout, Button, ButtonVariant,
    H2, Div, Span, Notification, NotificationVariant, Icon,
)
from pyxflow.components.horizontal_layout import Alignment

from .main_layout import MainLayout
from ..lib.chess_engine import (
    ChessGame, AVAILABLE_ENGINES, ENGINE_SNAKEFISH,
)

_COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 days


@Route("chess", layout=MainLayout)
@PageTitle("Chess")
@Menu(title="Chess", order=2, icon="vaadin:grid-bevel")
class ChessView(VerticalLayout):
    def __init__(self):
        self.set_padding(True)
        self.set_spacing(True)

        self.game = ChessGame()
        self.selected_square: int | None = None
        self.legal_targets: set[int] = set()
        self.cells: dict[int, Div] = {}
        self.flipped: bool = False

        # Restore state from cookies
        req = Request.get_current()
        if req:
            engine = req.get_cookie("chess_engine")
            if engine and engine in AVAILABLE_ENGINES:
                self.game.set_engine(engine, reset=False)
            color = req.get_cookie("chess_color")
            if color == "b":
                self.game.set_player_color(chess.BLACK)
                self.flipped = True
            moves = req.get_cookie("chess_moves")
            if moves:
                self.game.load_moves(moves)

        # Engine toggle button (avoids Select value-changed bugs in pyxflow)
        self.engine_btn = Button("", lambda e: self._toggle_engine())
        self.engine_btn.add_theme_variants(ButtonVariant.LUMO_ICON)
        self.engine_btn.add_class_name("chess-engine-btn")
        self._update_engine_btn()

        # Status bar
        self.status_label = Span(self.game.status_text)
        self.status_label.add_class_name("chess-status")

        # Controls
        new_game_btn = Button(Icon("vaadin:refresh"), lambda e: self._new_game())
        new_game_btn.add_theme_variants(ButtonVariant.LUMO_ICON)
        new_game_btn.set_tooltip_text("New Game")

        self.undo_btn = Button(Icon("vaadin:arrow-backward"), lambda e: self._undo())
        self.undo_btn.add_theme_variants(ButtonVariant.LUMO_ICON)
        self.undo_btn.set_tooltip_text("Undo")
        self.undo_btn.set_enabled(self.game.can_undo)

        self.redo_btn = Button(Icon("vaadin:arrow-forward"), lambda e: self._redo())
        self.redo_btn.add_theme_variants(ButtonVariant.LUMO_ICON)
        self.redo_btn.set_tooltip_text("Redo")
        self.redo_btn.set_enabled(self.game.can_redo)

        flip_btn = Button(Icon("vaadin:flip-v"), lambda e: self._flip_board())
        flip_btn.add_theme_variants(ButtonVariant.LUMO_ICON)
        flip_btn.set_tooltip_text("Flip Board")

        self.color_btn = Button("", lambda e: self._toggle_color())
        self.color_btn.add_theme_variants(ButtonVariant.LUMO_ICON)
        self.color_btn.add_class_name("chess-color-btn")
        self._update_color_btn()

        controls = HorizontalLayout(
            self.engine_btn, new_game_btn, self.undo_btn, self.redo_btn,
            flip_btn, self.color_btn,
        )
        controls.add_class_name("chess-controls")
        controls.set_default_vertical_component_alignment(Alignment.END)

        # Board
        self.board_div = Div()
        self.board_div.add_class_name("chess-board")
        self._build_board()

        # Status below board, right-aligned
        status_row = HorizontalLayout(self.status_label)
        status_row.add_class_name("chess-status-row")
        status_row.set_width_full()

        self.add(controls, self.board_div, status_row)
        self._refresh_board()

    def after_navigation(self):
        # If restored with engine's turn, let the engine play
        if not self.game.is_players_turn and not self.game.is_game_over:
            asyncio.create_task(self._engine_move_async())

    def _build_board(self):
        """Create the 8x8 board grid of Div cells."""
        if self.cells:
            self.board_div.remove(*self.cells.values())
        self.cells.clear()
        ranks = list(range(0, 8) if self.flipped else range(7, -1, -1))
        files = list(range(7, -1, -1) if self.flipped else range(8))
        for row_idx, rank in enumerate(ranks):
            for col_idx, file in enumerate(files):
                square = chess.square(file, rank)
                cell = Div()
                cell.add_class_name("chess-cell")
                if (rank + file) % 2 == 0:
                    cell.add_class_name("dark-square")
                else:
                    cell.add_class_name("light-square")
                # Coordinate labels on edges
                if row_idx == 7:
                    cell.add_class_name("coord-bottom")
                    cell.add_class_name(f"file-{chr(ord('a') + file)}")
                if col_idx == 0:
                    cell.add_class_name("coord-left")
                    cell.add_class_name(f"rank-{rank + 1}")
                cell.add_click_listener(
                    lambda e, sq=square: self._on_cell_click(sq)
                )
                self.board_div.add(cell)
                self.cells[square] = cell

    def _refresh_board(self):
        """Update all cell displays from game state."""
        last_move = self.game.last_move
        for square, cell in self.cells.items():
            cell.remove_class_name(
                "selected", "legal-target", "last-move", "check-king"
            )

            cell.remove_class_name("white-piece", "black-piece")
            piece_sym = self.game.get_piece_at(square)
            cell.set_text(piece_sym if piece_sym else "")
            if piece_sym:
                piece_obj = self.game.board.piece_at(square)
                if piece_obj and piece_obj.color == chess.WHITE:
                    cell.add_class_name("white-piece")
                else:
                    cell.add_class_name("black-piece")

            if square == self.selected_square:
                cell.add_class_name("selected")
            if square in self.legal_targets:
                cell.add_class_name("legal-target")
            if last_move and square in last_move:
                cell.add_class_name("last-move")

            if self.game.is_check:
                piece = self.game.board.piece_at(square)
                if (piece and piece.piece_type == chess.KING
                        and piece.color == self.game.board.turn):
                    cell.add_class_name("check-king")

        self.status_label.set_text(self.game.status_text)
        self.undo_btn.set_enabled(self.game.can_undo)
        self.redo_btn.set_enabled(self.game.can_redo)

    def _save_cookies(self):
        """Save move history, engine, and color to cookies."""
        moves = self.game.uci_moves
        engine = self.game.engine_name
        color = "w" if self.game.player_color == chess.WHITE else "b"
        resp = Response.get_current()
        if resp:
            resp.add_cookie("chess_moves", moves, max_age=_COOKIE_MAX_AGE)
            resp.add_cookie("chess_engine", engine, max_age=_COOKIE_MAX_AGE)
            resp.add_cookie("chess_color", color, max_age=_COOKIE_MAX_AGE)
        else:
            # Push callback - no HTTP response available, use JS
            self.execute_js(
                f"document.cookie='chess_moves='+encodeURIComponent('{moves}')"
                f"+';max-age={_COOKIE_MAX_AGE};path=/;SameSite=Lax';"
                f"document.cookie='chess_engine={engine}"
                f";max-age={_COOKIE_MAX_AGE};path=/;SameSite=Lax';"
                f"document.cookie='chess_color={color}"
                f";max-age={_COOKIE_MAX_AGE};path=/;SameSite=Lax';"
            )

    def _on_cell_click(self, square: int):
        """Handle cell click - select piece or make move."""
        if self.game.is_game_over or not self.game.is_players_turn:
            return

        # If a piece is selected and click is on a legal target, make move
        if self.selected_square is not None and square in self.legal_targets:
            self.game.make_move(self.selected_square, square)
            self.selected_square = None
            self.legal_targets = set()
            self._refresh_board()
            self._save_cookies()
            self._check_game_over()

            # Engine responds asynchronously via Push
            if not self.game.is_game_over:
                asyncio.create_task(self._engine_move_async())
            return

        # Select own piece
        if self.game.is_own_piece(square):
            self.selected_square = square
            self.legal_targets = set(self.game.get_legal_moves_from(square))
        else:
            self.selected_square = None
            self.legal_targets = set()

        self._refresh_board()

    async def _engine_move_async(self):
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.game.engine_move)
            ui = self.get_ui()
            if ui:
                ui.access(lambda: self._after_engine_move())
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _after_engine_move(self):
        self._refresh_board()
        self._save_cookies()
        self._check_game_over()

    def _update_engine_btn(self):
        from ..lib.chess_engine import ENGINE_SNAKEFISH, ENGINE_STOCKFISH
        name = self.game.engine_name
        icon = "\U0001f40d" if name == ENGINE_SNAKEFISH else "\U0001f41f"
        self.engine_btn.set_text(icon)
        if len(AVAILABLE_ENGINES) < 2:
            self.engine_btn.set_enabled(False)
            self.engine_btn.set_tooltip_text(f"{name} (no other engines available)")
        else:
            self.engine_btn.set_tooltip_text(f"{name} - click to switch engine")

    def _toggle_engine(self):
        idx = AVAILABLE_ENGINES.index(self.game.engine_name)
        new_engine = AVAILABLE_ENGINES[(idx + 1) % len(AVAILABLE_ENGINES)]
        self.game.set_engine(new_engine, reset=False)
        self._update_engine_btn()
        self._save_cookies()

    def _check_game_over(self):
        if self.game.is_checkmate:
            winner = "Black" if self.game.board.turn == chess.WHITE else "White"
            msg = f"Checkmate! {winner} wins!"
            variant = (NotificationVariant.LUMO_SUCCESS if winner == "White"
                       else NotificationVariant.LUMO_ERROR)
            n = Notification.show(msg, 5000, Notification.Position.MIDDLE)
            n.add_theme_variants(variant)
        elif self.game.is_stalemate:
            Notification.show("Stalemate - Draw!", 5000,
                              Notification.Position.MIDDLE)

    def _new_game(self):
        self.game.new_game()
        self.selected_square = None
        self.legal_targets = set()
        self._refresh_board()
        self._save_cookies()

    def _undo(self):
        if self.game.undo():
            self.selected_square = None
            self.legal_targets = set()
            self._refresh_board()
            self._save_cookies()

    def _redo(self):
        if self.game.redo():
            self.selected_square = None
            self.legal_targets = set()
            self._refresh_board()
            self._save_cookies()

    def _flip_board(self):
        self.flipped = not self.flipped
        self.selected_square = None
        self.legal_targets = set()
        self._build_board()
        self._refresh_board()

    def _toggle_color(self):
        if self.game.player_color == chess.WHITE:
            self.game.set_player_color(chess.BLACK)
            self.flipped = True
        else:
            self.game.set_player_color(chess.WHITE)
            self.flipped = False
        self.selected_square = None
        self.legal_targets = set()
        self._update_color_btn()
        self._build_board()
        self._refresh_board()
        self._save_cookies()
        if not self.game.is_players_turn and not self.game.is_game_over:
            asyncio.create_task(self._engine_move_async())

    def _update_color_btn(self):
        if self.game.player_color == chess.WHITE:
            self.color_btn.set_text("\u2654\ufe0e")
            self.color_btn.set_tooltip_text("Playing White - click to play as Black")
        else:
            self.color_btn.set_text("\u265a\ufe0e")
            self.color_btn.set_tooltip_text("Playing Black - click to play as White")
