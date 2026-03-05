# AGENTS.md - Development Guide for AI Coding Agents

This document provides guidelines for AI coding agents working on this PyXFlow-based board games application (Sudoku and Chess).

## Project Overview

- **Framework**: [PyXFlow](https://manolo.github.io/pyxflow/) (Python wrapper for Vaadin web components)
- **Python Version**: 3.14
- **Main Dependencies**: pyxflow, python-chess
- **Architecture**: Server-side Python rendering web UI with Vaadin components
- **Entry Point**: Run as Python module (see below)

## Build, Run & Test Commands

### Running the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application (from project root directory)
python -m vaadin_game_boards

# Application opens at http://localhost:8080
```

### Testing

No formal test suite exists currently. Manual testing via browser:
- Navigate to http://localhost:8080 for Sudoku
- Navigate to http://localhost:8080/chess for Chess

### Dependency Management

```bash
# Install dependencies
pip install pyxflow python-chess

# If Stockfish chess engine is desired (optional)
# Install via system package manager (e.g., brew install stockfish)
```

## Project Structure

```
vaadin-game-boards/          # Main package (run as: python -m vaadin_game_boards)
  __main__.py                # Entry point - FlowApp().run()
  lib/
    __init__.py              # Empty
    sudoku_engine.py         # Puzzle generation & validation (backtracking solver)
    chess_engine.py          # Chess game logic (wraps python-chess)
    uci_engine.py            # UCI protocol wrapper for Stockfish
    snakefish/               # Custom chess engine implementation
      *.py                   # Bitboard-based chess engine components
  views/
    __init__.py              # Empty
    main_layout.py           # @AppShell with AppLayout + SideNav
    sudoku_view.py           # Sudoku UI (@Route "")
    chess_view.py            # Chess UI (@Route "chess")
  static/
    styles/
      sudoku.css             # Sudoku grid and cell styling
      chess.css              # Chess board styling
```

## Code Style Guidelines

### Imports

- **Order**: Standard library, third-party, local imports (separated by blank lines)
- **Style**: Prefer explicit imports over wildcard (`from x import y` not `from x import *`)
- **Grouping**: Group related imports together (e.g., all pyxflow.components)

Example:
```python
"""Module docstring at the top."""

import random
from copy import deepcopy

import chess
from pyxflow import Route, Menu, PageTitle
from pyxflow.components import (
    VerticalLayout, HorizontalLayout, Button,
)

from .main_layout import MainLayout
from ..lib.sudoku_engine import generate_puzzle
```

### Formatting

- **Line Length**: Aim for ~100 characters, but flexible for readability
- **Indentation**: 4 spaces (no tabs)
- **Strings**: Double quotes for strings (`"text"` not `'text'`)
- **Blank Lines**: Two blank lines between top-level definitions, one within classes
- **Trailing Commas**: Use in multi-line lists/dicts for cleaner diffs

### Types & Type Hints

- **Use type hints**: Function signatures should include parameter and return types
- **Modern syntax**: Use `|` for unions (e.g., `int | None` not `Optional[int]`)
- **Collection types**: Use built-in types (e.g., `list[int]` not `List[int]`)
- **Type annotations**: Use for class attributes when not obvious

Example:
```python
def generate_puzzle(clues: int = 36) -> tuple[list[list[int]], list[list[int]]]:
    """Generate a Sudoku puzzle."""
    ...

class SudokuView(VerticalLayout):
    def __init__(self):
        self.selected: tuple[int, int] | None = None
        self.cells: list[list[Div]] = []
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `SudokuView`, `ChessGame`)
- **Functions/Methods**: snake_case (e.g., `generate_puzzle`, `_refresh_grid`)
- **Private Methods**: Prefix with underscore (e.g., `_build_grid`, `_check_game_over`)
- **Constants**: UPPER_CASE (e.g., `DIFFICULTY`, `ENGINE_SNAKEFISH`)
- **Variables**: snake_case, descriptive names (e.g., `selected_square`, `legal_targets`)

### Docstrings

- **Module level**: Brief description at top of file
- **Functions**: Docstring for public functions explaining purpose, parameters, return value
- **Format**: Simple style, not necessarily full Google/NumPy format
- **Private methods**: Optional docstrings, use when logic is complex

Example:
```python
"""Sudoku puzzle generation and validation engine."""

def generate_puzzle(clues: int = 36) -> tuple[list[list[int]], list[list[int]]]:
    """Generate a Sudoku puzzle.
    
    Returns (puzzle, solution) where puzzle has 0s for empty cells.
    clues: number of filled cells (17-80). Lower = harder.
    """
```

### Error Handling

- **Validation**: Check inputs early and return boolean success indicators
- **Fail gracefully**: Use `if`/`else` checks rather than exceptions for expected failures
- **Warnings**: Use `warnings` module for non-critical issues
- **Silent failures**: Methods like `make_move()` return `False` on invalid moves

Example:
```python
def make_move(self, from_sq: int, to_sq: int) -> bool:
    """Attempt to make a player move. Returns True if successful."""
    move = chess.Move(from_sq, to_sq, promotion=promotion)
    if move in self.board.legal_moves:
        self.board.push(move)
        return True
    return False
```

## PyXFlow MCP Tools

PyXFlow has an MCP (Model Context Protocol) server with tools for documentation and examples:

**IMPORTANT**: Use PyXFlow MCP tools when working with PyXFlow components:
- Search PyXFlow documentation for component usage
- Get examples and best practices
- Understand component APIs and patterns

The MCP server is available at: `https://pyxflow-mcp.manolo-345.workers.dev/mcp`

Configuration for `.mcp.json`:
```json
{
  "mcpServers": {
    "pyxflow": {
      "type": "http",
      "url": "https://pyxflow-mcp.manolo-345.workers.dev/mcp"
    }
  }
}
```

## PyXFlow Patterns

### View Components

- Views inherit from layout components (e.g., `VerticalLayout`)
- Use decorators: `@Route(path, layout=MainLayout)`, `@Menu`, `@PageTitle`
- Build UI in `__init__` by adding child components with `self.add(...)`

### Event Handling

- Lambda callbacks: `Button("Text", lambda e: self._handler())`
- Capture loop variables: `lambda e, val=x: self._handler(val)`
- State updates: Call `_refresh_*()` methods after state changes

### Component Styling

- CSS classes: `component.add_class_name("my-class")`
- Direct styles: `component.get_style().set("property", "value")`
- Theme variants: `button.add_theme_variants(ButtonVariant.LUMO_PRIMARY)`
- Notifications: Use `Notification.show()` with position and variants

### Async Operations

- Use `asyncio.create_task()` for background tasks (e.g., engine moves)
- Access UI thread: `ui.access(lambda: self._update_ui())`
- Push updates: `@Push` decorator on layout enables server-push

## Chess Engine Notes

- **Two engines**: Snakefish (custom, bitboard-based) and Stockfish (external UCI)
- **Availability**: Snakefish always available, Stockfish requires binary in PATH
- **State sync**: Keep `chess.Board` and `SnakefishBoard` in sync
- **Move validation**: Always validate through `python-chess` library

## Common Patterns

### Grid Building Pattern

```python
def _build_grid(self):
    """Create cell divs in a grid."""
    for r in range(9):
        for c in range(9):
            cell = Div()
            cell.add_class_name("cell")
            cell.add_click_listener(lambda e, row=r, col=c: self._on_click(row, col))
            self.grid_div.add(cell)
```

### State Management Pattern

```python
def _refresh_ui(self):
    """Update all UI components from current state."""
    # Remove old classes
    cell.remove_class_name("old-class")
    # Add new classes based on state
    if self.selected == (r, c):
        cell.add_class_name("selected")
    # Update content
    cell.set_text(str(value))
```

### Cookie Persistence Pattern

```python
def _save_cookies(self):
    resp = Response.get_current()
    if resp:
        resp.add_cookie("key", "value", max_age=30*24*3600)
    else:
        # Fallback for push callbacks - use JS
        self.execute_js("document.cookie='key=value;...'")
```

## Important Notes for Agents

1. **No direct file I/O**: PyXFlow apps run in-memory; no file reading/writing to disk for game state
2. **Server-side rendering**: All UI logic runs in Python, not JavaScript
3. **Component reuse**: Create helper methods for repeated UI patterns
4. **State before UI**: Always update internal state first, then refresh UI
5. **Move validation**: Never skip move legality checks in chess
6. **Type safety**: Respect type hints; they prevent runtime errors
7. **CSS coordination**: Grid layouts require corresponding CSS definitions in static/styles/
8. **Testing**: Currently manual; test in browser after changes
9. **Documentation**: Write in English (code, docs, commits, PRs)
10. **No AI attribution**: Never mention Claude, AI, or automated generation in commits/PRs

## Entry Point Reminder

Run from the project root directory:
```bash
python -m vaadin_game_boards
```

The `__main__.py` file contains:
```python
from pyxflow import FlowApp
FlowApp().run()
```

FlowApp auto-discovers all `@Route` decorated classes in the package.
