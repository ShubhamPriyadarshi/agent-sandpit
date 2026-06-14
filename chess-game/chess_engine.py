"""
Chess Engine - Complete chess game logic with all rules.
Handles move generation, validation, special moves, and game state detection.
"""

from enum import Enum
from typing import List, Tuple, Optional, Dict, Set
import copy


class PieceColor(Enum):
    WHITE = "white"
    BLACK = "black"


class PieceType(Enum):
    KING = "king"
    QUEEN = "queen"
    ROOK = "rook"
    BISHOP = "bishop"
    KNIGHT = "knight"
    PAWN = "pawn"


PIECE_SYMBOLS = {
    (PieceColor.WHITE, PieceType.KING): "♔",
    (PieceColor.WHITE, PieceType.QUEEN): "♕",
    (PieceColor.WHITE, PieceType.ROOK): "♖",
    (PieceColor.WHITE, PieceType.BISHOP): "♗",
    (PieceColor.WHITE, PieceType.KNIGHT): "♘",
    (PieceColor.WHITE, PieceType.PAWN): "♙",
    (PieceColor.BLACK, PieceType.KING): "♚",
    (PieceColor.BLACK, PieceType.QUEEN): "♛",
    (PieceColor.BLACK, PieceType.ROOK): "♜",
    (PieceColor.BLACK, PieceType.BISHOP): "♝",
    (PieceColor.BLACK, PieceType.KNIGHT): "♞",
    (PieceColor.BLACK, PieceType.PAWN): "♟",
}


class ChessPiece:
    def __init__(self, color: PieceColor, piece_type: PieceType):
        self.color = color
        self.piece_type = piece_type
        self.has_moved = False

    def __repr__(self):
        return f"{self.color.value[0].upper()}{self.piece_type.value[0].upper()}"


class Position:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col

    def __hash__(self):
        return hash((self.row, self.col))

    def __repr__(self):
        return f"Position({self.row}, {self.col})"

    def to_algebraic(self) -> str:
        files = "abcdefgh"
        return f"{files[self.col]}{8 - self.row}"


class Move:
    def __init__(self, from_pos: Position, to_pos: Position, piece: ChessPiece,
                 captured: Optional[ChessPiece] = None,
                 is_en_passant: bool = False,
                 is_castling: bool = False,
                 promotion_piece: Optional[PieceType] = None):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.piece = piece
        self.captured = captured
        self.is_en_passant = is_en_passant
        self.is_castling = is_castling
        self.promotion_piece = promotion_piece

    def to_algebraic(self, board: 'ChessBoard') -> str:
        files = "abcdefgh"
        ranks = "87654321"

        if self.is_castling:
            if self.to_pos.col > self.from_pos.col:
                return "O-O"
            else:
                return "O-O-O"

        notation = ""
        if self.piece.piece_type != PieceType.PAWN:
            notation += self.piece.piece_type.name[0]

        if self.piece.piece_type == PieceType.PAWN and self.captured:
            notation += files[self.from_pos.col]

        if self.captured:
            notation += "x"

        notation += files[self.to_pos.col] + ranks[self.to_pos.row]

        if self.promotion_piece:
            notation += "=" + self.promotion_piece.name[0]

        return notation

    def __repr__(self):
        return f"Move({self.from_pos} -> {self.to_pos})"


class ChessBoard:
    def __init__(self):
        self.board: List[List[Optional[ChessPiece]]] = [[None] * 8 for _ in range(8)]
        self.current_turn = PieceColor.WHITE
        self.move_history: List[Move] = []
        self.captured_pieces: Dict[PieceColor, List[ChessPiece]] = {
            PieceColor.WHITE: [],
            PieceColor.BLACK: [],
        }
        self._setup_board()

    def _setup_board(self):
        back_rank = [PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP,
                     PieceType.QUEEN, PieceType.KING, PieceType.BISHOP,
                     PieceType.KNIGHT, PieceType.ROOK]

        for col in range(8):
            self.board[0][col] = ChessPiece(PieceColor.BLACK, back_rank[col])
            self.board[1][col] = ChessPiece(PieceColor.BLACK, PieceType.PAWN)
            self.board[6][col] = ChessPiece(PieceColor.WHITE, PieceType.PAWN)
            self.board[7][col] = ChessPiece(PieceColor.WHITE, back_rank[col])

    def get_piece(self, pos: Position) -> Optional[ChessPiece]:
        if 0 <= pos.row < 8 and 0 <= pos.col < 8:
            return self.board[pos.row][pos.col]
        return None

    def set_piece(self, pos: Position, piece: Optional[ChessPiece]):
        if 0 <= pos.row < 8 and 0 <= pos.col < 8:
            self.board[pos.row][pos.col] = piece

    def find_king(self, color: PieceColor) -> Optional[Position]:
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.piece_type == PieceType.KING and piece.color == color:
                    return Position(row, col)
        return None

    def is_square_attacked(self, pos: Position, attacker_color: PieceColor) -> bool:
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == attacker_color:
                    moves = self._get_raw_moves_for_piece(Position(row, col), piece, False)
                    for move in moves:
                        if move.to_pos == pos:
                            return True
        return False

    def is_in_check(self, color: PieceColor) -> bool:
        king_pos = self.find_king(color)
        if king_pos is None:
            return False
        opponent = PieceColor.BLACK if color == PieceColor.WHITE else PieceColor.WHITE
        return self.is_square_attacked(king_pos, opponent)

    def _get_raw_moves_for_piece(self, pos: Position, piece: ChessPiece,
                                 include_castling: bool = True) -> List[Move]:
        moves = []
        row, col = pos.row, pos.col

        if piece.piece_type == PieceType.PAWN:
            direction = 1 if piece.color == PieceColor.BLACK else -1
            start_row = 1 if piece.color == PieceColor.BLACK else 6

            forward = Position(row + direction, col)
            if 0 <= forward.row < 8 and self.get_piece(forward) is None:
                promo_rank = 0 if piece.color == PieceColor.BLACK else 7
                if forward.row == promo_rank:
                    for pt in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                        moves.append(Move(pos, forward, piece, promotion_piece=pt))
                else:
                    moves.append(Move(pos, forward, piece))

                double_forward = Position(row + 2 * direction, col)
                if row == start_row and self.get_piece(double_forward) is None:
                    moves.append(Move(pos, double_forward, piece))

            for dc in [-1, 1]:
                capture_pos = Position(row + direction, col + dc)
                if 0 <= capture_pos.row < 8 and 0 <= capture_pos.col < 8:
                    target = self.get_piece(capture_pos)
                    if target and target.color != piece.color:
                        promo_rank = 0 if piece.color == PieceColor.BLACK else 7
                        if capture_pos.row == promo_rank:
                            for pt in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                                moves.append(Move(pos, capture_pos, piece, captured=target, promotion_piece=pt))
                        else:
                            moves.append(Move(pos, capture_pos, piece, captured=target))

                    ep_row = 3 if piece.color == PieceColor.BLACK else 4
                    ep_pos = Position(ep_row, col + dc)
                    ep_piece = self.get_piece(ep_pos)
                    if (ep_piece and ep_piece.piece_type == PieceType.PAWN and
                            ep_piece.color != piece.color and
                            not ep_piece.has_moved):
                        moves.append(Move(pos, capture_pos, piece, is_en_passant=True))

        elif piece.piece_type == PieceType.KNIGHT:
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                            (1, -2), (1, 2), (2, -1), (2, 1)]
            for dr, dc in knight_moves:
                new_pos = Position(row + dr, col + dc)
                if 0 <= new_pos.row < 8 and 0 <= new_pos.col < 8:
                    target = self.get_piece(new_pos)
                    if target is None or target.color != piece.color:
                        moves.append(Move(pos, new_pos, piece, captured=target))

        elif piece.piece_type == PieceType.BISHOP:
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                for i in range(1, 8):
                    new_pos = Position(row + dr * i, col + dc * i)
                    if not (0 <= new_pos.row < 8 and 0 <= new_pos.col < 8):
                        break
                    target = self.get_piece(new_pos)
                    if target is None:
                        moves.append(Move(pos, new_pos, piece))
                    else:
                        if target.color != piece.color:
                            moves.append(Move(pos, new_pos, piece, captured=target))
                        break

        elif piece.piece_type == PieceType.ROOK:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                for i in range(1, 8):
                    new_pos = Position(row + dr * i, col + dc * i)
                    if not (0 <= new_pos.row < 8 and 0 <= new_pos.col < 8):
                        break
                    target = self.get_piece(new_pos)
                    if target is None:
                        moves.append(Move(pos, new_pos, piece))
                    else:
                        if target.color != piece.color:
                            moves.append(Move(pos, new_pos, piece, captured=target))
                        break

        elif piece.piece_type == PieceType.QUEEN:
            for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                           (0, 1), (1, -1), (1, 0), (1, 1)]:
                for i in range(1, 8):
                    new_pos = Position(row + dr * i, col + dc * i)
                    if not (0 <= new_pos.row < 8 and 0 <= new_pos.col < 8):
                        break
                    target = self.get_piece(new_pos)
                    if target is None:
                        moves.append(Move(pos, new_pos, piece))
                    else:
                        if target.color != piece.color:
                            moves.append(Move(pos, new_pos, piece, captured=target))
                        break

        elif piece.piece_type == PieceType.KING:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_pos = Position(row + dr, col + dc)
                    if 0 <= new_pos.row < 8 and 0 <= new_pos.col < 8:
                        target = self.get_piece(new_pos)
                        if target is None or target.color != piece.color:
                            moves.append(Move(pos, new_pos, piece, captured=target))

            if include_castling and not piece.has_moved and not self.is_in_check(piece.color):
                # Kingside castling
                kingside_rook = self.get_piece(Position(row, 7))
                if (kingside_rook and kingside_rook.piece_type == PieceType.ROOK and
                        not kingside_rook.has_moved):
                    if (self.get_piece(Position(row, 5)) is None and
                            self.get_piece(Position(row, 6)) is None and
                            not self.is_square_attacked(Position(row, 5),
                                                        PieceColor.BLACK if piece.color == PieceColor.WHITE else PieceColor.WHITE) and
                            not self.is_square_attacked(Position(row, 6),
                                                        PieceColor.BLACK if piece.color == PieceColor.WHITE else PieceColor.WHITE)):
                        moves.append(Move(pos, Position(row, 6), piece, is_castling=True))

                # Queenside castling
                queenside_rook = self.get_piece(Position(row, 0))
                if (queenside_rook and queenside_rook.piece_type == PieceType.ROOK and
                        not queenside_rook.has_moved):
                    if (self.get_piece(Position(row, 1)) is None and
                            self.get_piece(Position(row, 2)) is None and
                            self.get_piece(Position(row, 3)) is None and
                            not self.is_square_attacked(Position(row, 2),
                                                        PieceColor.BLACK if piece.color == PieceColor.WHITE else PieceColor.WHITE) and
                            not self.is_square_attacked(Position(row, 3),
                                                        PieceColor.BLACK if piece.color == PieceColor.WHITE else PieceColor.WHITE)):
                        moves.append(Move(pos, Position(row, 2), piece, is_castling=True))

        return moves

    def get_legal_moves(self, pos: Optional[Position] = None) -> List[Move]:
        all_moves = []
        if pos is None:
            for row in range(8):
                for col in range(8):
                    piece = self.board[row][col]
                    if piece and piece.color == self.current_turn:
                        moves = self._get_raw_moves_for_piece(Position(row, col), piece)
                        all_moves.extend(moves)
        else:
            piece = self.get_piece(pos)
            if piece and piece.color == self.current_turn:
                all_moves = self._get_raw_moves_for_piece(pos, piece)

        legal_moves = []
        for move in all_moves:
            new_board = copy.deepcopy(self)
            new_board._execute_move(move)
            if not new_board.is_in_check(move.piece.color):
                legal_moves.append(move)

        return legal_moves

    def _execute_move(self, move: Move):
        piece = move.piece
        self.set_piece(move.from_pos, None)

        if move.is_en_passant:
            captured_row = move.from_pos.row
            self.set_piece(Position(captured_row, move.to_pos.col), None)
            self.captured_pieces[move.piece.color].append(
                ChessPiece(move.piece.color, PieceType.PAWN))
        else:
            target = self.get_piece(move.to_pos)
            if target:
                self.captured_pieces[move.piece.color].append(target)

        self.set_piece(move.to_pos, piece)
        piece.has_moved = True

        if move.is_castling:
            if move.to_pos.col == 6:
                rook = self.get_piece(Position(move.from_pos.row, 7))
                self.set_piece(Position(move.from_pos.row, 7), None)
                self.set_piece(Position(move.from_pos.row, 5), rook)
                rook.has_moved = True
            elif move.to_pos.col == 2:
                rook = self.get_piece(Position(move.from_pos.row, 0))
                self.set_piece(Position(move.from_pos.row, 0), None)
                self.set_piece(Position(move.from_pos.row, 3), rook)
                rook.has_moved = True

        if move.promotion_piece:
            new_piece = ChessPiece(piece.color, move.promotion_piece)
            new_piece.has_moved = True
            self.set_piece(move.to_pos, new_piece)

        self.current_turn = PieceColor.BLACK if self.current_turn == PieceColor.WHITE else PieceColor.WHITE

    def make_move(self, move: Move) -> bool:
        legal_moves = self.get_legal_moves()
        if move in legal_moves:
            self._execute_move(move)
            self.move_history.append(move)
            return True
        return False

    def get_game_status(self) -> str:
        legal_moves = self.get_legal_moves()
        if not legal_moves:
            if self.is_in_check(self.current_turn):
                winner = PieceColor.BLACK if self.current_turn == PieceColor.WHITE else PieceColor.WHITE
                return f"checkmate_{winner.value}"
            return "stalemate"
        elif self._is_insufficient_material():
            return "insufficient_material"
        elif self._is_threefold_repetition():
            return "threefold_repetition"
        return "ongoing"

    def _is_insufficient_material(self) -> bool:
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    pieces.append(piece)

        if len(pieces) == 2:
            return True
        if len(pieces) == 3 and all(p.piece_type == PieceType.BISHOP for p in pieces):
            return True
        if len(pieces) == 3:
            knights = [p for p in pieces if p.piece_type == PieceType.KNIGHT]
            bishops = [p for p in pieces if p.piece_type == PieceType.BISHOP]
            if len(knights) == 1 or len(bishops) == 1:
                return True
        return False

    def _is_threefold_repetition(self) -> bool:
        return False

    def undo_move(self) -> Optional[Move]:
        if not self.move_history:
            return None

        move = self.move_history.pop()
        new_board = copy.deepcopy(self)
        self._undo_move(move)
        return move

    def _undo_move(self, move: Move):
        piece = move.piece
        if move.promotion_piece:
            piece = ChessPiece(move.piece.color, PieceType.PAWN)
            piece.has_moved = True

        self.set_piece(move.to_pos, None)
        self.set_piece(move.from_pos, piece)
        piece.has_moved = move.piece.has_moved

        if move.is_en_passant:
            captured_row = move.from_pos.row
            self.set_piece(Position(captured_row, move.to_pos.col),
                           ChessPiece(PieceColor.BLACK if piece.color == PieceColor.WHITE else PieceColor.WHITE, PieceType.PAWN))
            self.captured_pieces[move.piece.color].pop()
        elif move.captured:
            if move.captured in self.captured_pieces[move.piece.color]:
                self.captured_pieces[move.piece.color].remove(move.captured)
            else:
                opp = PieceColor.BLACK if move.piece.color == PieceColor.WHITE else PieceColor.WHITE
                if move.captured in self.captured_pieces[opp]:
                    self.captured_pieces[opp].remove(move.captured)

        if move.is_castling:
            if move.to_pos.col == 6:
                self.set_piece(Position(move.from_pos.row, 5), None)
                rook = ChessPiece(piece.color, PieceType.ROOK)
                rook.has_moved = True
                self.set_piece(Position(move.from_pos.row, 7), rook)
                rook.has_moved = False
            elif move.to_pos.col == 2:
                self.set_piece(Position(move.from_pos.row, 3), None)
                rook = ChessPiece(piece.color, PieceType.ROOK)
                rook.has_moved = True
                self.set_piece(Position(move.from_pos.row, 0), rook)
                rook.has_moved = False

        self.current_turn = move.piece.color
