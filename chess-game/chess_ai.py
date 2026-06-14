"""
Chess AI - Optimized minimax with alpha-beta pruning and positional evaluation.
Uses iterative deepening with time limits and move ordering for efficiency.
"""

import random
import time
from typing import Optional, List
from chess_engine import (
    ChessBoard, Move, ChessPiece, PieceColor, PieceType, Position
)


class _QuickBoard:
    """Lightweight board for AI search — no deepcopy, just an int array."""

    __slots__ = (
        "sq", "turn", "wk", "bk", "ep", "castling", "halfmove",
        "move_history", "captured",
    )

    EMPTY = 0
    # Piece codes: positive = white, negative = black
    W_PAWN, W_KNIGHT, W_BISHOP, W_ROOK, W_QUEEN, W_KING = 1, 2, 3, 4, 5, 6
    B_PAWN, B_KNIGHT, B_BISHOP, B_ROOK, B_QUEEN, B_KING = -1, -2, -3, -4, -5, -6

    _CODE_TO_TYPE = {
        1: PieceType.PAWN, -1: PieceType.PAWN,
        2: PieceType.KNIGHT, -2: PieceType.KNIGHT,
        3: PieceType.BISHOP, -3: PieceType.BISHOP,
        4: PieceType.ROOK, -4: PieceType.ROOK,
        5: PieceType.QUEEN, -5: PieceType.QUEEN,
        6: PieceType.KING, -6: PieceType.KING,
    }

    _TYPE_TO_CODE = {
        PieceType.PAWN: 1, PieceType.KNIGHT: 2, PieceType.BISHOP: 3,
        PieceType.ROOK: 4, PieceType.QUEEN: 5, PieceType.KING: 6,
    }

    PIECE_VALUES = {
        PieceType.PAWN: 100, PieceType.KNIGHT: 320, PieceType.BISHOP: 330,
        PieceType.ROOK: 500, PieceType.QUEEN: 900, PieceType.KING: 20000,
    }

    PST = {
        PieceType.PAWN: (
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0,
        ),
        PieceType.KNIGHT: (
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50,
        ),
        PieceType.BISHOP: (
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20,
        ),
        PieceType.ROOK: (
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10, 10, 10, 10, 10,  5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            0,  0,  0,  5,  5,  0,  0,  0,
        ),
        PieceType.QUEEN: (
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -5,  0,  5,  5,  5,  5,  0, -5,
            0,  0,  5,  5,  5,  5,  0, -5,
            -10,  5,  5,  5,  5,  5,  0,-10,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20,
        ),
        PieceType.KING: (
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            20, 20,  0,  0,  0,  0, 20, 20,
            20, 30, 10,  0,  0, 10, 30, 20,
        ),
    }

    def __init__(self, board: ChessBoard):
        self.sq: List[int] = [0] * 64
        self.turn: int = 1 if board.current_turn == PieceColor.WHITE else -1
        self.wk: int = -1
        self.bk: int = -1
        self.ep: int = -1
        self.castling: int = 0
        self.halfmove: int = 0
        self.move_history: List[Move] = list(board.move_history)
        self.captured = {
            PieceColor.WHITE: list(board.captured_pieces[PieceColor.WHITE]),
            PieceColor.BLACK: list(board.captured_pieces[PieceColor.BLACK]),
        }
        for r in range(8):
            for c in range(8):
                p = board.board[r][c]
                if p:
                    code = self._TYPE_TO_CODE[p.piece_type] * (1 if p.color == PieceColor.WHITE else -1)
                    self.sq[r * 8 + c] = code
                    if p.piece_type == PieceType.KING:
                        if p.color == PieceColor.WHITE:
                            self.wk = r * 8 + c
                        else:
                            self.bk = r * 8 + c

    def _p(self, idx: int) -> Optional[ChessPiece]:
        code = self.sq[idx]
        if code == 0:
            return None
        t = self._CODE_TO_TYPE[code]
        color = PieceColor.WHITE if code > 0 else PieceColor.BLACK
        p = ChessPiece(color, t)
        p.has_moved = True  # simplified
        return p

    def get_piece(self, pos: Position) -> Optional[ChessPiece]:
        return self._p(pos.row * 8 + pos.col)

    def set_piece(self, pos: Position, code: int):
        self.sq[pos.row * 8 + pos.col] = code

    def get_square(self, pos: Position) -> int:
        return self.sq[pos.row * 8 + pos.col]

    def find_king(self, color: PieceColor) -> int:
        return self.wk if color == PieceColor.WHITE else self.bk

    def _is_attacked_by(self, pos: int, by_color: int) -> bool:
        """Check if square `pos` is attacked by `by_color` (1=white, -1=black)."""
        r, c = divmod(pos, 8)
        # Pawn attacks
        pawn_dir = -1 if by_color == 1 else 1  # white pawns attack upward (lower row)
        for dc in (-1, 1):
            nr, nc = r - pawn_dir, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if self.sq[nr * 8 + nc] == by_color * 1:  # white pawn = 1, black pawn = -1
                    return True
        # Knight attacks
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if self.sq[nr * 8 + nc] == by_color * 2:
                    return True
        # Bishop/Queen attacks (diagonals)
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                code = self.sq[nr * 8 + nc]
                if code != 0:
                    if code == by_color * 3 or code == by_color * 5:
                        return True
                    break
                nr += dr
                nc += dc
        # Rook/Queen attacks (straight)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                code = self.sq[nr * 8 + nc]
                if code != 0:
                    if code == by_color * 4 or code == by_color * 5:
                        return True
                    break
                nr += dr
                nc += dc
        # King attacks
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if self.sq[nr * 8 + nc] == by_color * 6:
                        return True
        return False

    def is_in_check(self, color: PieceColor) -> bool:
        king = self.find_king(color)
        if king == -1:
            return False
        opp = -self.turn
        return self._is_attacked_by(king, opp)

    def _gen_moves(self) -> List[tuple]:
        """Generate (from, to, captured, special) tuples for the current side."""
        moves: List[tuple] = []
        for idx in range(64):
            code = self.sq[idx]
            if code == 0 or (code > 0 and self.turn == -1) or (code < 0 and self.turn == 1):
                continue
            r, c = divmod(idx, 8)
            ptype = abs(code)
            sign = self.turn  # +1 for white, -1 for black

            if ptype == 1:  # Pawn
                fwd = sign * (-1)  # white moves to lower rows
                start_row = 6 if sign == 1 else 1
                promo_row = 0 if sign == 1 else 7

                # Forward
                nr = r + fwd
                if 0 <= nr < 8 and self.sq[nr * 8 + c] == 0:
                    if nr == promo_row:
                        for pt in [5, 4, 3, 2]:  # Q, R, B, N
                            moves.append((idx, nr * 8 + c, 0, ("promo", pt)))
                    else:
                        moves.append((idx, nr * 8 + c, 0, ()))
                        # Double push
                        if r == start_row and self.sq[(r + 2 * fwd) * 8 + c] == 0:
                            moves.append((idx, (r + 2 * fwd) * 8 + c, 0, ()))
                # Captures
                for dc in (-1, 1):
                    nc = c + dc
                    nr = r + fwd
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        target = self.sq[nr * 8 + nc]
                        if target != 0 and (target > 0) != (sign > 0):
                            if nr == promo_row:
                                for pt in [5, 4, 3, 2]:
                                    moves.append((idx, nr * 8 + nc, abs(target), ("promo", pt)))
                            else:
                                moves.append((idx, nr * 8 + nc, abs(target), ()))
                        # En passant
                        if self.ep == nr * 8 + nc:
                            moves.append((idx, nr * 8 + nc, 1, ("ep",)))

            elif ptype == 2:  # Knight
                for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        target = self.sq[nr * 8 + nc]
                        if (target == 0) or (target > 0) != (sign > 0):
                            moves.append((idx, nr * 8 + nc, abs(target) if target else 0, ()))

            elif ptype == 3:  # Bishop
                for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 8 and 0 <= nc < 8:
                        target = self.sq[nr * 8 + nc]
                        if target == 0:
                            moves.append((idx, nr * 8 + nc, 0, ()))
                        elif (target > 0) != (sign > 0):
                            moves.append((idx, nr * 8 + nc, abs(target), ()))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc

            elif ptype == 4:  # Rook
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 8 and 0 <= nc < 8:
                        target = self.sq[nr * 8 + nc]
                        if target == 0:
                            moves.append((idx, nr * 8 + nc, 0, ()))
                        elif (target > 0) != (sign > 0):
                            moves.append((idx, nr * 8 + nc, abs(target), ()))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc

            elif ptype == 5:  # Queen
                for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 8 and 0 <= nc < 8:
                        target = self.sq[nr * 8 + nc]
                        if target == 0:
                            moves.append((idx, nr * 8 + nc, 0, ()))
                        elif (target > 0) != (sign > 0):
                            moves.append((idx, nr * 8 + nc, abs(target), ()))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc

            elif ptype == 6:  # King
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            target = self.sq[nr * 8 + nc]
                            if (target == 0) or (target > 0) != (sign > 0):
                                moves.append((idx, nr * 8 + nc, abs(target) if target else 0, ()))

        return moves

    def _make(self, fr: int, to: int, captured: int, special: tuple) -> int:
        """Make a move on the quick board. Returns the piece that was at `fr`."""
        piece = self.sq[fr]
        self.sq[fr] = 0

        # En passant capture
        if "ep" in special:
            pawn_row = (fr // 8) - 1 if self.turn == 1 else (fr // 8) + 1
            self.sq[pawn_row * 8 + (to % 8)] = 0

        # Castling
        if "castle" in special:
            if to % 8 == 6:  # Kingside
                rook_src = fr // 8 * 8 + 7
                rook_dst = fr // 8 * 8 + 5
                self.sq[rook_dst] = self.sq[rook_src]
                self.sq[rook_src] = 0
            elif to % 8 == 2:  # Queenside
                rook_src = fr // 8 * 8 + 0
                rook_dst = fr // 8 * 8 + 3
                self.sq[rook_dst] = self.sq[rook_src]
                self.sq[rook_src] = 0

        # Promotion
        if "promo" in special:
            promo_code = self.turn * special[1]
            self.sq[to] = promo_code
        else:
            self.sq[to] = piece

        # Update king position
        if abs(piece) == 6:
            if piece > 0:
                self.wk = to
            else:
                self.bk = to

        self.turn = -self.turn
        return piece

    def _unmake(self, fr: int, to: int, captured: int, special: tuple, prev_piece: int):
        """Undo a move."""
        self.turn = -self.turn

        # Restore piece to its original square, clear destination
        self.sq[to] = 0
        self.sq[fr] = prev_piece

        if "ep" in special:
            pawn_row = (fr // 8) - 1 if self.turn == 1 else (fr // 8) + 1
            self.sq[pawn_row * 8 + (to % 8)] = -self.turn * 1

        if "castle" in special:
            if to % 8 == 6:
                self.sq[fr // 8 * 8 + 5] = self.turn * 4
                self.sq[fr // 8 * 8 + 7] = 0
            elif to % 8 == 2:
                self.sq[fr // 8 * 8 + 3] = self.turn * 4
                self.sq[fr // 8 * 8 + 0] = 0

        if abs(prev_piece) == 6:
            if prev_piece > 0:
                self.wk = fr
            else:
                self.bk = fr

    def _apply_move(self, fr: int, to: int, captured: int, special: tuple) -> int:
        """Make move and return evaluation of resulting position."""
        self._make(fr, to, captured, special)
        return self._evaluate()

    def _evaluate(self) -> float:
        """Always evaluate from white's perspective. Positive = good for white."""
        score = 0.0
        ptype_map = {1: PieceType.PAWN, 2: PieceType.KNIGHT, 3: PieceType.BISHOP,
                     4: PieceType.ROOK, 5: PieceType.QUEEN, 6: PieceType.KING}
        for idx in range(64):
            code = self.sq[idx]
            if code == 0:
                continue
            sign = 1 if code > 0 else -1
            abs_code = abs(code)
            pt = ptype_map.get(abs_code, PieceType.PAWN)
            material = self.PIECE_VALUES[pt]
            pst = self.PST.get(pt, (0,) * 64)
            if sign == 1:
                score += material + pst[idx]
            else:
                score -= material + pst[63 - idx]
        return score


class ChessAI:
    """Optimized AI opponent using iterative deepening minimax."""

    def __init__(self, color: PieceColor, difficulty: int = 3):
        self.color = color
        self.difficulty = difficulty
        self.nodes_searched = 0
        self.time_limit = {1: 0.5, 2: 1.5, 3: 3.0, 4: 5.0}.get(difficulty, 3.0)
        # Evaluation is always from white's perspective.
        # AI maximizes when white, minimizes when black.
        self._maximizing = (color == PieceColor.WHITE)

    def get_best_move(self, board: ChessBoard) -> Optional[Move]:
        qboard = _QuickBoard(board)
        moves = qboard._gen_moves()
        if not moves:
            return None

        if self.difficulty == 1:
            return self._pick_random_move(board, moves)

        # Sort moves for better alpha-beta pruning (captures first)
        moves.sort(key=lambda m: m[2], reverse=True)

        best_move = moves[0]
        best_eval = float('-inf') if self._maximizing else float('inf')
        alpha = float('-inf')
        beta = float('inf')
        depth = min(self.difficulty, 4)

        self.nodes_searched = 0
        start_time = time.time()

        # Iterative deepening — stops if time runs out
        for d in range(1, depth + 1):
            if time.time() - start_time > self.time_limit * 0.8:
                break
            best_eval, best_move = self._iter_deep(qboard, d, alpha, beta, best_move)
            alpha = max(alpha, best_eval) if self._maximizing else min(alpha, best_eval)

        return self._map_move(board, best_move)

    def _iter_deep(self, qboard: _QuickBoard, depth: int,
                   alpha: float, beta: float, best_move: tuple) -> tuple:
        return self._search(qboard, depth, alpha, beta, self._maximizing, best_move)

    def _search(self, qboard: _QuickBoard, depth: int,
                alpha: float, beta: float, maximizing: bool,
                best_move: tuple) -> tuple:
        if depth == 0:
            return qboard._evaluate(), best_move

        moves = qboard._gen_moves()
        # Filter out moves that leave king in check
        legal: List[tuple] = []
        for fr, to, cap, spec in moves:
            piece = qboard.sq[fr]
            qboard._make(fr, to, cap, spec)
            # After _make, self.turn has flipped.
            # Directly check if the moving side's king is attacked by the opponent.
            moving_side = PieceColor.BLACK if piece < 0 else PieceColor.WHITE
            attacker = PieceColor.WHITE if piece < 0 else PieceColor.BLACK
            king_pos = qboard.find_king(moving_side)
            in_check = king_pos != -1 and qboard._is_attacked_by(
                king_pos, 1 if attacker == PieceColor.WHITE else -1)
            qboard._unmake(fr, to, cap, spec, piece)
            if not in_check:
                legal.append((fr, to, cap, spec))

        if not legal:
            if qboard.is_in_check(
                    PieceColor.WHITE if qboard.turn == 1 else PieceColor.BLACK):
                return (float('-inf') if maximizing else float('inf')), best_move
            return 0, best_move

        if maximizing:
            eval_score = float('-inf')
            for fr, to, cap, spec in legal:
                piece = qboard.sq[fr]
                qboard._make(fr, to, cap, spec)
                val, _ = self._search(qboard, depth - 1, alpha, beta, False, best_move)
                qboard._unmake(fr, to, cap, spec, piece)
                if val > eval_score:
                    eval_score = val
                    best_move = (fr, to, cap, spec)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return eval_score, best_move
        else:
            eval_score = float('inf')
            for fr, to, cap, spec in legal:
                piece = qboard.sq[fr]
                qboard._make(fr, to, cap, spec)
                val, _ = self._search(qboard, depth - 1, alpha, beta, True, best_move)
                qboard._unmake(fr, to, cap, spec, piece)
                if val < eval_score:
                    eval_score = val
                    best_move = (fr, to, cap, spec)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return eval_score, best_move

    def _pick_random_move(self, board: ChessBoard, moves: list) -> Optional[Move]:
        fr, to, cap, spec = random.choice(moves)
        from_pos = Position(fr // 8, fr % 8)
        to_pos = Position(to // 8, to % 8)
        piece = board.get_piece(from_pos)
        if not piece:
            return None
        captured = board.get_piece(to_pos) if cap > 0 else None
        is_ep = "ep" in spec
        is_castle = "castle" in spec
        promo = PieceType.QUEEN if "promo" in spec else None
        return Move(from_pos, to_pos, piece, captured, is_ep, is_castle, promo)

    def _map_move(self, board: ChessBoard, qmove: tuple) -> Optional[Move]:
        fr, to, cap, spec = qmove
        from_pos = Position(fr // 8, fr % 8)
        to_pos = Position(to // 8, to % 8)
        piece = board.get_piece(from_pos)
        if not piece:
            return None
        captured = board.get_piece(to_pos) if cap > 0 else None
        is_ep = "ep" in spec
        is_castle = "castle" in spec
        promo = PieceType.QUEEN if "promo" in spec else None
        return Move(from_pos, to_pos, piece, captured, is_ep, is_castle, promo)
