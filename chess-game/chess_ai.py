"""
Chess AI - Minimax with alpha-beta pruning and positional evaluation.
Provides an AI opponent with selectable difficulty levels.
"""

import random
import copy
from typing import Optional
from chess_engine import (
    ChessBoard, Move, ChessPiece, PieceColor, PieceType, Position
)


class ChessAI:
    """AI opponent using minimax with alpha-beta pruning."""

    PIECE_VALUES = {
        PieceType.PAWN: 100,
        PieceType.KNIGHT: 320,
        PieceType.BISHOP: 330,
        PieceType.ROOK: 500,
        PieceType.QUEEN: 900,
        PieceType.KING: 20000,
    }

    # Piece-square tables for positional evaluation
    PST = {
        PieceType.PAWN: [
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0,
        ],
        PieceType.KNIGHT: [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50,
        ],
        PieceType.BISHOP: [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20,
        ],
        PieceType.ROOK: [
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10, 10, 10, 10, 10,  5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            0,  0,  0,  5,  5,  0,  0,  0,
        ],
        PieceType.QUEEN: [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -5,  0,  5,  5,  5,  5,  0, -5,
            0,  0,  5,  5,  5,  5,  0, -5,
            -10,  5,  5,  5,  5,  5,  0,-10,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20,
        ],
        PieceType.KING: [
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            20, 20,  0,  0,  0,  0, 20, 20,
            20, 30, 10,  0,  0, 10, 30, 20,
        ],
    }

    def __init__(self, color: PieceColor, difficulty: int = 3):
        self.color = color
        self.difficulty = difficulty
        self.nodes_searched = 0
        self.captured_value = 0

    def get_best_move(self, board: ChessBoard) -> Optional[Move]:
        legal_moves = board.get_legal_moves()
        if not legal_moves:
            return None

        if self.difficulty == 1:
            return random.choice(legal_moves)

        depth = min(self.difficulty, 4)
        is_maximizing = (board.current_turn == self.color)

        best_move = legal_moves[0]
        best_eval = float('-inf') if is_maximizing else float('inf')

        random.shuffle(legal_moves)

        for move in legal_moves:
            new_board = self._simulate_move(board, move)
            eval_score = self._minimax(new_board, depth - 1, float('-inf'), float('inf'),
                                       not is_maximizing)

            if is_maximizing and eval_score > best_eval:
                best_eval = eval_score
                best_move = move
            elif not is_maximizing and eval_score < best_eval:
                best_eval = eval_score
                best_move = move

        return best_move

    def _minimax(self, board: ChessBoard, depth: int, alpha: float,
                 beta: float, is_maximizing: bool) -> float:
        self.nodes_searched += 1

        if depth == 0:
            return self._evaluate_board(board)

        legal_moves = board.get_legal_moves()

        if not legal_moves:
            if board.is_in_check(board.current_turn):
                return float('-inf') if is_maximizing else float('inf')
            return 0

        if is_maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                new_board = self._simulate_move(board, move)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_board = self._simulate_move(board, move)
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate_board(self, board: ChessBoard) -> float:
        score = 0
        for row in range(8):
            for col in range(8):
                piece = board.board[row][col]
                if piece:
                    material = self.PIECE_VALUES[piece.piece_type]
                    pst_index = (7 - row) * 8 + col
                    if piece.color == self.color:
                        pst = self.PST.get(piece.piece_type, [0] * 64)
                        score += material + pst[pst_index]
                    else:
                        pst = self.PST.get(piece.piece_type, [0] * 64)
                        score -= (material + pst[pst_index])

        score += len(board.get_legal_moves()) * 1
        return score

    def _simulate_move(self, board: ChessBoard, move: Move) -> ChessBoard:
        new_board = copy.deepcopy(board)
        new_board._execute_move(move)
        return new_board
