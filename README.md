# Board Games - PyXFlow App

A web-based board games application built with [PyXFlow](https://github.com/manolo/pyxflow), featuring classic Sudoku puzzles and Chess games.

## What is This?

This is a browser-based game collection that runs on Python. You can play:

- **Sudoku**: Generate and solve puzzles with three difficulty levels
- **Chess**: Play against the server using two different chess engines (Snakefish built-in, or Stockfish if installed)

The entire UI runs in your browser while the game logic executes server-side in Python. Built with PyXFlow, a Python framework that wraps Vaadin web components.

## Features

### Sudoku
- Multiple difficulty levels (Easy, Medium, Hard)
- Interactive 9x9 grid with number pad
- Real-time validation and error checking
- Hint system highlights duplicate numbers

### Chess
- Play against the server (powered by Snakefish or Stockfish engines)
- Click-and-click move interface
- Undo/Redo functionality
- Board flip for playing as Black
- Move history persistence via cookies
- Visual indicators for legal moves, last move, and check

## System Requirements

- **Python 3.14** (or compatible version)
- **PyXFlow** - Python web framework
- **python-chess** - Chess logic library
- **Stockfish** (optional) - For stronger chess engine

## Installation (First Time Setup)

If you need to set up the project from scratch:

```bash
# 1. Clone the repository
git clone https://github.com/manolo/vaadin-game-boards.git
cd vaadin-game-boards

# 2. Create virtual environment
python -m venv .venv

# 3. Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Optional: Install Stockfish for stronger chess engine
brew install stockfish  # macOS
# Or download from https://stockfishchess.org/
```

## Quick Start

```bash
# 1. Navigate to the project directory
cd vaadin-game-boards

# 2. Activate virtual environment (if not already activated)
source .venv/bin/activate

# 3. Run the application
python -m vaadin_game_boards
```

The server will start and automatically open your browser at http://localhost:8080

**Available Games:**
- **Sudoku**: http://localhost:8080 (default home page)
- **Chess**: http://localhost:8080/chess

Press `Ctrl+C` in the terminal to stop the server.

## Project Structure

```
vaadin-game-boards/
├── __main__.py           # Entry point
├── lib/                  # Game logic
│   ├── sudoku_engine.py  # Sudoku puzzle generation
│   ├── chess_engine.py   # Chess game logic
│   ├── uci_engine.py     # Stockfish UCI wrapper
│   └── snakefish/        # Custom chess engine
├── views/                # UI components
│   ├── main_layout.py    # App shell layout
│   ├── sudoku_view.py    # Sudoku game UI
│   └── chess_view.py     # Chess game UI
└── static/
    └── styles/           # CSS styling
```

## Development

See [AGENTS.md](AGENTS.md) for detailed development guidelines, code style, and architecture documentation.

## Technologies

- **PyXFlow**: Python web framework wrapping Vaadin components
- **python-chess**: Chess move validation and game logic
- **Snakefish**: Custom bitboard-based chess engine
- **Stockfish**: Optional external chess engine via UCI protocol

## License

Apache 2.0
