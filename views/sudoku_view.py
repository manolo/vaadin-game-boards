"""Sudoku game view built with PyXFlow."""

from pyxflow import Route, Menu, PageTitle
from pyxflow.components import (
    VerticalLayout, HorizontalLayout, Button, ButtonVariant,
    Select, Notification, NotificationVariant,
    H2, Div, Span,
)
from pyxflow.components.horizontal_layout import Alignment

from .main_layout import MainLayout
from ..lib.sudoku_engine import generate_puzzle, check_board, DIFFICULTY


@Route("", layout=MainLayout)
@PageTitle("Sudoku")
@Menu(title="Sudoku", order=1, icon="vaadin:grid-small")
class SudokuView(VerticalLayout):
    def __init__(self):
        self.set_padding(True)
        self.set_spacing(True)

        self.selected: tuple[int, int] | None = None
        self.cells: list[list[Div]] = []
        self.board: list[list[int]] = []
        self.given: list[list[bool]] = []
        self.solution: list[list[int]] = []
        self.error_cells: set[tuple[int, int]] = set()
        self.difficulty = "Medium"

        # Header
        title = H2("Sudoku")
        title.get_style().set("margin", "0")

        # Difficulty selector
        self.diff_select = Select()
        self.diff_select.set_label("Difficulty")
        self.diff_select.set_items(list(DIFFICULTY.keys()))
        self.diff_select.set_value("Medium")
        self.diff_select.add_value_change_listener(
            lambda e: setattr(self, "difficulty", e.value)
        )

        new_game_btn = Button("New Game", lambda e: self._new_game())
        new_game_btn.add_theme_variants(ButtonVariant.LUMO_PRIMARY)

        check_btn = Button("Check", lambda e: self._check())

        controls = HorizontalLayout(self.diff_select, new_game_btn, check_btn)
        controls.add_class_name("controls-bar")
        controls.set_default_vertical_component_alignment(Alignment.END)

        # Grid
        self.grid_div = Div()
        self.grid_div.add_class_name("sudoku-grid")
        self._build_grid()

        # Number pad
        pad = Div()
        pad.add_class_name("number-pad")
        for n in range(1, 10):
            btn = Button(str(n), lambda e, num=n: self._enter_number(num))
            btn.add_theme_variants(ButtonVariant.LUMO_CONTRAST)
            pad.add(btn)
        erase_btn = Button("X", lambda e: self._enter_number(0))
        erase_btn.add_theme_variants(ButtonVariant.LUMO_ERROR)
        pad.add(erase_btn)

        # Layout: grid on left, pad on right
        game_panel = VerticalLayout(pad)
        game_panel.add_class_name("game-panel")
        game_panel.set_padding(False)

        wrapper = HorizontalLayout(self.grid_div, game_panel)
        wrapper.add_class_name("sudoku-wrapper")

        self.add(title, controls, wrapper)

        # Start game
        self._new_game()

    def _build_grid(self):
        """Create the 9x9 cell divs."""
        self.cells = []
        for r in range(9):
            row = []
            for c in range(9):
                cell = Div()
                cell.add_class_name("sudoku-cell")
                if c % 3 == 2 and c < 8:
                    cell.add_class_name("border-right")
                if r % 3 == 2 and r < 8:
                    cell.add_class_name("border-bottom")
                cell.add_click_listener(
                    lambda e, row=r, col=c: self._select_cell(row, col)
                )
                self.grid_div.add(cell)
                row.append(cell)
            self.cells.append(row)

    def _new_game(self):
        """Generate a new puzzle and update the grid."""
        clues = DIFFICULTY[self.difficulty]
        self.board, self.solution = generate_puzzle(clues)
        self.given = [[self.board[r][c] != 0 for c in range(9)] for r in range(9)]
        self.selected = None
        self.error_cells = set()
        self._refresh_grid()

    def _refresh_grid(self):
        """Update all cell displays from self.board."""
        for r in range(9):
            for c in range(9):
                cell = self.cells[r][c]
                val = self.board[r][c]

                cell.remove_class_name("given", "editable", "selected",
                                        "error", "same-value")

                if self.given[r][c]:
                    cell.add_class_name("given")
                else:
                    cell.add_class_name("editable")

                if (r, c) in self.error_cells:
                    cell.add_class_name("error")

                if self.selected == (r, c):
                    cell.add_class_name("selected")

                if (self.selected and val != 0
                        and self.board[self.selected[0]][self.selected[1]] == val
                        and (r, c) != self.selected):
                    cell.add_class_name("same-value")

                cell.set_text(str(val) if val != 0 else "")

    def _select_cell(self, row: int, col: int):
        """Select a cell for number entry."""
        self.selected = (row, col)
        self._refresh_grid()

    def _enter_number(self, num: int):
        """Place a number in the selected cell."""
        if self.selected is None:
            return
        r, c = self.selected
        if self.given[r][c]:
            Notification.show("This cell is fixed", 2000,
                              Notification.Position.BOTTOM_CENTER)
            return
        self.board[r][c] = num
        self.error_cells.discard((r, c))
        self._refresh_grid()

        # Check win
        if all(self.board[r][c] != 0 for r in range(9) for c in range(9)):
            errors = check_board(self.board)
            if not errors:
                n = Notification.show(
                    "Congratulations! Puzzle solved!", 5000,
                    Notification.Position.MIDDLE
                )
                n.add_theme_variants(NotificationVariant.LUMO_SUCCESS)

    def _check(self):
        """Validate current entries and highlight errors."""
        errors = check_board(self.board)
        self.error_cells = {(r, c) for r, c in errors if not self.given[r][c]}
        self._refresh_grid()
        if not self.error_cells:
            empty = sum(1 for r in range(9) for c in range(9) if self.board[r][c] == 0)
            if empty == 0:
                n = Notification.show("Puzzle solved!", 3000,
                                      Notification.Position.BOTTOM_CENTER)
                n.add_theme_variants(NotificationVariant.LUMO_SUCCESS)
            else:
                Notification.show(f"No errors so far! {empty} cells remaining.",
                                  3000, Notification.Position.BOTTOM_CENTER)
        else:
            n = Notification.show(
                f"{len(self.error_cells)} error(s) found",
                3000, Notification.Position.BOTTOM_CENTER
            )
            n.add_theme_variants(NotificationVariant.LUMO_ERROR)
