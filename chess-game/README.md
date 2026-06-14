# ♔ Chess Master

A fully-featured chess game with AI opponent built in Python.

## Features

- **Complete Chess Rules**: All standard moves including castling, en passant, and pawn promotion
- **AI Opponent**: Four difficulty levels (Easy, Medium, Hard, Expert) using minimax with alpha-beta pruning
- **Beautiful GUI**: Dark-themed interface with smooth animations and highlights
- **Move History**: Full game log in algebraic notation
- **Captured Pieces**: Visual display of captured pieces
- **Sound Effects**: Audio feedback for moves, captures, checks, castling, and promotions
- **Game Controls**: Undo moves, flip board, adjust difficulty, toggle sound

## Installation

```bash
cd chess-game
python main.py
```

No external dependencies required! (pygame is optional for enhanced sound)

## How to Play

1. **Click** a white piece to select it
2. **Green dots** show legal moves
3. **Click** a highlighted square to move
4. The AI will respond automatically
5. Use the **Controls** panel for game options

## Controls

| Button | Description |
|--------|-------------|
| New Game | Start a fresh game |
| Undo Move | Undo your last two moves |
| Flip Board | View from black's perspective |
| AI Difficulty | Change AI strength (1-4) |
| Sound | Toggle sound effects |
| Rules | View chess rules |

## Project Structure

```
chess-game/
├── main.py           # Entry point
├── chess_engine.py   # Game logic and rules
├── chess_ai.py       # AI opponent (minimax + alpha-beta)
├── chess_gui.py      # GUI with all features
├── sound_effects.py  # Sound generation
└── requirements.txt  # Dependencies
```
