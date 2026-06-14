"""
Chess Game GUI - Beautiful tkinter interface with full game features.
Includes AI opponent, move history, captured pieces, and game controls.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Optional, List, Tuple

from chess_engine import (
    ChessBoard, ChessPiece, Move, PieceColor, PieceType,
    Position, PIECE_SYMBOLS
)
from chess_ai import ChessAI
from sound_effects import SoundManager


class PromotionDialog:
    """Modal dialog for pawn promotion selection."""

    def __init__(self, parent: tk.Toplevel, color: PieceColor) -> None:
        self.result: Optional[PieceType] = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Promote Pawn")
        self.dialog.geometry("240x180")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg="#2d2d2d")

        tk.Label(
            self.dialog, text="Choose promotion piece:",
            font=("Arial", 12, "bold"), fg="white", bg="#2d2d2d"
        ).pack(pady=(10, 5))

        frame = tk.Frame(self.dialog, bg="#2d2d2d")
        frame.pack(pady=5)

        for i, piece_type in enumerate([PieceType.QUEEN, PieceType.ROOK,
                                         PieceType.BISHOP, PieceType.KNIGHT]):
            btn = tk.Button(
                frame,
                text=PIECE_SYMBOLS[(color, piece_type)],
                font=("Arial", 36),
                bg="#3d3d3d",
                fg="white",
                activebackground="#555",
                activeforeground="white",
                width=2,
                height=1,
                command=lambda pt=piece_type: self._select_piece(pt),
                cursor="hand2",
            )
            btn.grid(row=0, column=i, padx=8)

        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        self.dialog.wait_window()

    def _select_piece(self, piece_type: PieceType):
        self.result = piece_type
        self.dialog.destroy()


class ChessGUI:
    """Main chess game GUI with all features."""

    SQUARE_SIZE = 80
    BOARD_PADDING = 10

    COLORS_BOARD = {
        "light": "#F0D9B5",
        "dark": "#B58863",
        "light_highlight": "#FFEB5D",
        "dark_highlight": "#F7F769",
        "selected": "#7FFF00",
        "check": "#FF6B6B",
        "last_move": "#CDD26A",
    }

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("♔ Chess Master")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        self.board = ChessBoard()
        self.ai = ChessAI(PieceColor.BLACK, difficulty=3)
        self.sound = SoundManager(enabled=True)

        self.selected_square: Optional[Position] = None
        self.legal_moves: List[Move] = []
        self.player_color = PieceColor.WHITE
        self.game_over = False
        self.last_move: Optional[Move] = None
        self.check_square: Optional[Position] = None
        self.move_count = 0

        self._setup_ui()
        self._update_board()

    def _setup_ui(self) -> None:
        self.root.configure(bg="#1a1a2e")

        # Main container
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top bar
        top_frame = tk.Frame(main_frame, bg="#1a1a2e")
        top_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            top_frame, text="♔ CHESS MASTER",
            font=("Georgia", 20, "bold"), fg="#e0d5c1", bg="#1a1a2e"
        ).pack(side=tk.LEFT)

        self.status_label = tk.Label(
            top_frame, text="Your turn (White)",
            font=("Arial", 11), fg="#a0a0a0", bg="#1a1a2e"
        )
        self.status_label.pack(side=tk.RIGHT)

        # Content frame
        content_frame = tk.Frame(main_frame, bg="#1a1a2e")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Game controls
        left_panel = tk.Frame(content_frame, bg="#16213e", width=180)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        # Board frame
        board_frame = tk.Frame(content_frame, bg="#1a1a2e")
        board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right panel - Move history
        right_panel = tk.Frame(content_frame, bg="#16213e", width=220)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_panel.pack_propagate(False)

        self._setup_board_area(board_frame)
        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_board_area(self, parent: tk.Frame) -> None:
        # Captured pieces by black (top)
        cap_frame_top = tk.Frame(parent, bg="#1a1a2e")
        cap_frame_top.pack(fill=tk.X, pady=(0, 5))
        self.cap_label_top = tk.Label(
            cap_frame_top, text="", font=("Arial", 14),
            fg="#e0d5c1", bg="#1a1a2e"
        )
        self.cap_label_top.pack()

        # Board wrapper
        board_wrapper = tk.Frame(parent, bg="#0f3460", padx=self.BOARD_PADDING,
                                  pady=self.BOARD_PADDING)
        board_wrapper.pack()

        self.canvas = tk.Canvas(
            board_wrapper, width=self.SQUARE_SIZE * 8,
            height=self.SQUARE_SIZE * 8,
            bg="#0f3460", highlightthickness=0
        )
        self.canvas.pack()

        # File labels
        files_frame = tk.Frame(parent, bg="#0f3460")
        files_frame.pack()
        tk.Label(files_frame, text="a b c d e f g h",
                 font=("Arial", 10), fg="#a0a0a0", bg="#0f3460").pack()

        # Captured pieces by white (bottom)
        cap_frame_bottom = tk.Frame(parent, bg="#1a1a2e")
        cap_frame_bottom.pack(fill=tk.X, pady=(5, 0))
        self.cap_label_bottom = tk.Label(
            cap_frame_bottom, text="", font=("Arial", 14),
            fg="#e0d5c1", bg="#1a1a2e"
        )
        self.cap_label_bottom.pack()

        self.canvas.bind("<Button-1>", self._on_board_click)

    def _setup_left_panel(self, parent: tk.Frame) -> None:
        tk.Label(
            parent, text="⚙ CONTROLS",
            font=("Georgia", 14, "bold"), fg="#e0d5c1", bg="#16213e"
        ).pack(pady=(10, 5))

        btn_frame = tk.Frame(parent, bg="#16213e")
        btn_frame.pack(pady=5)

        buttons = [
            ("New Game", self._new_game),
            ("Undo Move", self._undo_move),
            ("Flip Board", self._flip_board),
            ("AI Difficulty", self._set_difficulty),
            ("Sound", self._toggle_sound),
            ("Rules", self._show_rules),
        ]

        for text, cmd in buttons:
            btn = tk.Button(
                btn_frame, text=text, font=("Arial", 10),
                bg="#0f3460", fg="#e0d5c1", activebackground="#1a5276",
                activeforeground="white", cursor="hand2",
                relief=tk.FLAT, padx=15, pady=8,
                command=cmd,
            )
            btn.pack(fill=tk.X, padx=10, pady=2)

        # Player info
        info_frame = tk.Frame(parent, bg="#16213e")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        self.player_info = tk.Label(
            info_frame, text="You: White\nAI: Black",
            font=("Arial", 9), fg="#a0a0a0", bg="#16213e"
        )
        self.player_info.pack(anchor=tk.W)

    def _setup_right_panel(self, parent: tk.Frame) -> None:
        tk.Label(
            parent, text="📜 MOVE HISTORY",
            font=("Georgia", 14, "bold"), fg="#e0d5c1", bg="#16213e"
        ).pack(pady=(10, 5))

        # Move list
        list_frame = tk.Frame(parent, bg="#0f3460", highlightthickness=1,
                               highlightbackground="#1a5276")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.move_text = tk.Text(
            list_frame, font=("Courier", 10), bg="#0a1628",
            fg="#a0d5c1", wrap=tk.WORD, state=tk.DISABLED,
            height=20, width=25, relief=tk.FLAT
        )
        move_scrollbar = tk.Scrollbar(list_frame, command=self.move_text.yview,
                                      bg="#1a5276")
        self.move_text.configure(yscrollcommand=move_scrollbar.set)

        self.move_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        move_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Captured pieces display
        tk.Label(
            parent, text="CAPTURED PIECES",
            font=("Georgia", 12, "bold"), fg="#e0d5c1", bg="#16213e"
        ).pack(pady=(10, 5))

        self.captured_display = tk.Label(
            parent, text="", font=("Arial", 12),
            fg="#a0a0a0", bg="#16213e"
        )
        self.captured_display.pack(fill=tk.X, padx=10)

    def _setup_board(self) -> None:
        self.canvas.delete("all")

        for row in range(8):
            for col in range(8):
                x1 = col * self.SQUARE_SIZE
                y1 = row * self.SQUARE_SIZE
                x2 = x1 + self.SQUARE_SIZE
                y2 = y1 + self.SQUARE_SIZE

                is_light = (row + col) % 2 == 0
                color = self.COLORS_BOARD["light"] if is_light else self.COLORS_BOARD["dark"]

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        self._highlight_last_move()
        self._highlight_check()
        self._highlight_legal_moves()
        self._draw_pieces()

    def _draw_pieces(self) -> None:
        self.canvas.delete("pieces")

        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(Position(row, col))
                if piece:
                    x = col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                    y = row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2

                    symbol = PIECE_SYMBOLS[(piece.color, piece.piece_type)]
                    color = "black" if piece.color == PieceColor.BLACK else "white"
                    outline = "white" if piece.color == PieceColor.BLACK else "black"

                    self.canvas.create_text(
                        x, y, text=symbol, font=("Arial", 36),
                        fill=color, tags="pieces"
                    )

    def _highlight_last_move(self) -> None:
        if self.last_move:
            for pos in [self.last_move.from_pos, self.last_move.to_pos]:
                x1 = pos.col * self.SQUARE_SIZE
                y1 = pos.row * self.SQUARE_SIZE
                x2 = x1 + self.SQUARE_SIZE
                y2 = y1 + self.SQUARE_SIZE

                is_light = (pos.row + pos.col) % 2 == 0
                color = (self.COLORS_BOARD["light_highlight"] if is_light
                         else self.COLORS_BOARD["dark_highlight"])

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="", tags="highlight"
                )

    def _highlight_check(self) -> None:
        if self.board.is_in_check(self.board.current_turn):
            king_pos = self.board.find_king(self.board.current_turn)
            if king_pos:
                x1 = king_pos.col * self.SQUARE_SIZE
                y1 = king_pos.row * self.SQUARE_SIZE
                x2 = x1 + self.SQUARE_SIZE
                y2 = y1 + self.SQUARE_SIZE

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=self.COLORS_BOARD["check"],
                    outline="", tags="highlight"
                )

    def _highlight_legal_moves(self) -> None:
        for move in self.legal_moves:
            x = move.to_pos.col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            y = move.to_pos.row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2

            piece = self.board.get_piece(move.to_pos)
            if piece:
                self.canvas.create_oval(
                    x - 25, y - 25, x + 25, y + 25,
                    outline="#333333", width=4, tags="highlight"
                )
            else:
                self.canvas.create_oval(
                    x - 12, y - 12, x + 12, y + 12,
                    fill="#333333", outline="", tags="highlight"
                )

    def _on_board_click(self, event: tk.Event) -> None:
        if self.game_over or self.board.current_turn != self.player_color:
            return

        col = (event.x - self.BOARD_PADDING) // self.SQUARE_SIZE
        row = (event.y - self.BOARD_PADDING) // self.SQUARE_SIZE

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        pos = Position(row, col)
        piece = self.board.get_piece(pos)

        if self.selected_square is None:
            if piece and piece.color == self.player_color:
                self.selected_square = pos
                self.legal_moves = self.board.get_legal_moves(pos)
                self._setup_board()
        else:
            if piece and piece.color == self.player_color and pos != self.selected_square:
                self.legal_moves = self.board.get_legal_moves(pos)
                self.selected_square = pos
                self._setup_board()
                return

            moves = [m for m in self.legal_moves
                     if m.from_pos == self.selected_square and m.to_pos == pos]

            if moves:
                if len(moves) == 1 and moves[0].promotion_piece:
                    self._handle_promotion(self.selected_square, pos)
                else:
                    self._execute_move(moves[0])
            else:
                self.selected_square = None
                self.legal_moves = []
                self._setup_board()

    def _handle_promotion(self, from_pos: Position, to_pos: Position) -> None:
        promo_dialog = PromotionDialog(self.root, self.player_color)
        if promo_dialog.result:
            moves = [m for m in self.legal_moves
                     if m.from_pos == from_pos and m.to_pos == to_pos and
                     m.promotion_piece == promo_dialog.result]
            if moves:
                self._execute_move(moves[0])

    def _execute_move(self, move: Move) -> None:
        self.board.make_move(move)
        self.last_move = move
        self.selected_square = None
        self.legal_moves = []
        self.move_count += 1

        self.sound.play_sound(self._get_move_sound(move))
        self._setup_board()
        self._update_move_history()
        self._update_captured_display()
        self._check_game_status()

        if not self.game_over and self.board.current_turn != self.player_color:
            self.status_label.config(text="AI is thinking...")
            self.root.after(100, self._make_ai_move)

    def _make_ai_move(self) -> None:
        def _ai_thread():
            move = self.ai.get_best_move(self.board)
            if move:
                self.root.after(0, lambda: self._execute_ai_move(move))
            else:
                self._check_game_status()

        threading.Thread(target=_ai_thread, daemon=True).start()

    def _execute_ai_move(self, move: Move) -> None:
        self.board.make_move(move)
        self.last_move = move
        self.move_count += 1

        self.sound.play_sound(self._get_move_sound(move))
        self._setup_board()
        self._update_move_history()
        self._update_captured_display()
        self._check_game_status()

        if not self.game_over:
            self.status_label.config(text="Your turn (White)")

    def _get_move_sound(self, move: Move) -> str:
        if move.captured and move.piece.piece_type == PieceType.PAWN:
            return "capture"
        if move.is_castling:
            return "castling"
        if self.board.is_in_check(
                PieceColor.BLACK if move.piece.color == PieceColor.WHITE else PieceColor.WHITE
        ):
            return "check"
        if move.promotion_piece:
            return "promotion"
        return "move"

    def _check_game_status(self) -> None:
        status = self.board.get_game_status()

        if status == "checkmate":
            self.game_over = True
            winner = status.split("_")[1]
            if winner == self.player_color.value:
                self.status_label.config(text="🎉 Checkmate! You win!")
                self.sound.play_sound("checkmate")
                self.root.after(500, lambda: messagebox.showinfo(
                    "🎉 Victory!", "Congratulations! You won the game!"))
            else:
                self.status_label.config(text="😔 Checkmate! AI wins.")
                self.sound.play_sound("checkmate")
                self.root.after(500, lambda: messagebox.showinfo(
                    "Game Over", "The AI wins this time. Try again!"))
        elif status == "stalemate":
            self.game_over = True
            self.status_label.config(text="🤝 Stalemate!")
            self.root.after(500, lambda: messagebox.showinfo(
                "Draw", "The game is a stalemate draw."))
        elif status == "insufficient_material":
            self.game_over = True
            self.status_label.config(text="🤝 Draw!")
            self.root.after(500, lambda: messagebox.showinfo(
                "Draw", "Insufficient material to continue."))

    def _update_move_history(self) -> None:
        self.move_text.configure(state=tk.NORMAL)
        text = ""
        moves = self.board.move_history
        for i in range(0, len(moves), 2):
            move_num = (i // 2) + 1
            white_move = moves[i].to_algebraic(self.board)
            black_move = moves[i + 1].to_algebraic(self.board) if i + 1 < len(moves) else ""
            text += f"{move_num}. {white_move} {black_move}\n"

        self.move_text.configure(state=tk.DISABLED)
        self.move_text.delete("1.0", tk.END)
        self.move_text.configure(state=tk.NORMAL)
        self.move_text.insert(tk.END, text)
        self.move_text.configure(state=tk.DISABLED)
        self.move_text.see(tk.END)

    def _update_captured_display(self) -> None:
        white_captured = self.board.captured_pieces[PieceColor.WHITE]
        black_captured = self.board.captured_pieces[PieceColor.BLACK]

        sort_key = {PieceType.PAWN: 1, PieceType.KNIGHT: 2, PieceType.BISHOP: 3,
                    PieceType.ROOK: 4, PieceType.QUEEN: 5}

        white_str = "".join(sorted(
            [PIECE_SYMBOLS[(PieceColor.WHITE, p.piece_type)]
             for p in white_captured],
            key=lambda x: sort_key.get(
                next((p.piece_type for p in white_captured
                      if PIECE_SYMBOLS[(PieceColor.WHITE, p.piece_type)] == x),
                     PieceType.PAWN), 1)
        ))

        black_str = "".join(sorted(
            [PIECE_SYMBOLS[(PieceColor.BLACK, p.piece_type)]
             for p in black_captured],
            key=lambda x: sort_key.get(
                next((p.piece_type for p in black_captured
                      if PIECE_SYMBOLS[(PieceColor.BLACK, p.piece_type)] == x),
                     PieceType.PAWN), 1)
        ))

        self.cap_label_top.config(text=black_str or "  ♟♞♝♜♛")
        self.cap_label_bottom.config(text=white_str or "  ♙♘♗♖♕")

    def _update_board(self) -> None:
        self._setup_board()

    def _new_game(self) -> None:
        self.board = ChessBoard()
        self.selected_square = None
        self.legal_moves = []
        self.game_over = False
        self.last_move = None
        self.move_count = 0
        self._setup_board()
        self._update_move_history()
        self._update_captured_display()
        self.status_label.config(text="Your turn (White)")

    def _undo_move(self) -> None:
        if self.move_count < 2:
            return

        self.board.undo_move()
        self.board.undo_move()
        self.last_move = self.board.move_history[-1] if self.board.move_history else None
        self.selected_square = None
        self.legal_moves = []
        self.game_over = False
        self.move_count -= 2

        self._setup_board()
        self._update_move_history()
        self._update_captured_display()
        self.status_label.config(text="Your turn (White)")

    def _flip_board(self) -> None:
        self.canvas.delete("all")

        for row in range(8):
            for col in range(8):
                actual_row = 7 - row
                actual_col = 7 - col

                x1 = col * self.SQUARE_SIZE
                y1 = row * self.SQUARE_SIZE
                x2 = x1 + self.SQUARE_SIZE
                y2 = y1 + self.SQUARE_SIZE

                is_light = (actual_row + actual_col) % 2 == 0
                color = (self.COLORS_BOARD["light"] if is_light
                         else self.COLORS_BOARD["dark"])

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        self._draw_pieces()

    def _set_difficulty(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("AI Difficulty")
        dialog.geometry("280x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#2d2d2d")

        tk.Label(
            dialog, text="Select Difficulty:",
            font=("Arial", 11, "bold"), fg="white", bg="#2d2d2d"
        ).pack(pady=(15, 5))

        difficulties = [
            ("Easy (Depth 1)", 1),
            ("Medium (Depth 2)", 2),
            ("Hard (Depth 3)", 3),
            ("Expert (Depth 4)", 4),
        ]

        self.diff_var = tk.IntVar(value=self.ai.difficulty)

        for text, value in difficulties:
            rb = tk.Radiobutton(
                dialog, text=text, variable=self.diff_var, value=value,
                font=("Arial", 10), bg="#2d2d2d", fg="white",
                selectcolor="#1a1a2e", cursor="hand2",
                command=lambda v=value: self._set_diff(v),
            )
            rb.pack(anchor=tk.W, padx=20, pady=2)

        tk.Label(
            dialog, text=f"Current: {self.ai.difficulty}",
            font=("Arial", 9), fg="#a0a0a0", bg="#2d2d2d"
        ).pack(pady=(10, 5))

    def _set_diff(self, value: int) -> None:
        self.ai.difficulty = value
        self.ai = ChessAI(PieceColor.BLACK, difficulty=value)

    def _toggle_sound(self) -> None:
        self.sound.enabled = not self.sound.enabled
        status = "enabled" if self.sound.enabled else "disabled"
        self.status_label.config(text=f"Sound {status}")

    def _show_rules(self) -> None:
        rules_text = (
            "♔ CHESS RULES\n\n"
            "• Move pieces to capture the opponent's king\n"
            "• Each piece moves differently (see below)\n"
            "• Check your king from danger!\n"
            "• Castling: Move king two squares toward a rook\n"
            "• En Passant: Special pawn capture\n"
            "• Pawn Promotion: Reach the end to promote\n\n"
            "PIECE MOVES:\n"
            "♔ King: One square any direction\n"
            "♕ Queen: Any number of squares any direction\n"
            "♖ Rook: Any number of squares straight\n"
            "♗ Bishop: Any number of squares diagonal\n"
            "♘ Knight: L-shape (2+1)\n"
            "♙ Pawn: Forward one (two from start), capture diagonal\n"
        )
        messagebox.showinfo("Chess Rules", rules_text)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    game = ChessGUI()
    game.run()


if __name__ == "__main__":
    main()
