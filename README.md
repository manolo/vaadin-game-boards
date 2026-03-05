# Board Games - PyXFlow App

A web-based board games application built with PyXFlow, featuring Sudoku and Chess games.

## Features

### Sudoku
- Multiple difficulty levels (Easy, Medium, Hard)
- Interactive 9x9 grid with number pad
- Real-time validation and error checking
- Hint system highlights duplicate numbers

### Chess
- Play against AI engines (Snakefish or Stockfish)
- Click-and-click move interface
- Undo/Redo functionality
- Board flip for playing as Black
- Move history persistence via cookies
- Visual indicators for legal moves, last move, and check

## Requirements

- Python 3.14
- PyXFlow
- python-chess
- Stockfish (optional, for Stockfish engine)

## Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install Stockfish
brew install stockfish  # macOS
# Or download from https://stockfishchess.org/
```

## Running the Application

```bash
# From parent directory
python -m kk
```

The application will start at http://localhost:8080

- Sudoku: http://localhost:8080
- Chess: http://localhost:8080/chess

## Project Structure

```
kk/
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

MIT
