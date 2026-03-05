from . import bitboard
from .constants import (
    Color, Piece,
    CASTLE_ALL, CASTLE_WK, CASTLE_WQ, CASTLE_BK, CASTLE_BQ,
    CASTLING_RIGHTS_MASK,
    E1, G1, C1, H1, A1, D1, F1,
    E8, G8, C8, H8, A8, D8, F8,
)


class ChessBoard:
    __slots__ = (
        'pieces', 'combined_color', 'combined_all', 'color',
        'castling_rights', 'ep_square', 'halfmove_clock', 'zobrist_hash',
    )

    def __init__(self):
        self.pieces = [[0] * 6, [0] * 6]  # 2 sides, 6 piece bitboards
        self.combined_color = [0, 0]
        self.combined_all = 0
        self.color = Color.WHITE
        self.castling_rights = 0
        self.ep_square = -1  # -1 means no EP target
        self.halfmove_clock = 0
        self.zobrist_hash = 0

    def get_piece_bb(self, piece, color=None):
        if color is None:
            color = self.color
        return self.pieces[color][piece]

    def piece_on(self, sq, color=None):
        if color is None:
            color = self.color
        bb = 1 << sq
        pieces = self.pieces[color]
        for p in range(6):
            if pieces[p] & bb:
                return Piece(p)
        return None

    def set_square(self, sq, piece, color=None):
        if color is None:
            color = self.color
        bb = 1 << sq
        self.pieces[color][piece] |= bb
        self.combined_color[color] |= bb
        self.combined_all |= bb

    def clear_square(self, sq, color=None):
        if color is None:
            color = self.color
        bb = 1 << sq
        pieces = self.pieces[color]
        for p in range(6):
            if pieces[p] & bb:
                pieces[p] &= ~bb
                self.combined_color[color] &= ~bb
                self.combined_all &= ~bb
                return Piece(p)
        return None

    def apply_move(self, move):
        """Return a new board with the move applied. Handles castling and EP."""
        new = ChessBoard()
        new.pieces = [self.pieces[0][:], self.pieces[1][:]]
        new.combined_color = self.combined_color[:]
        new.combined_all = self.combined_all
        new.color = self.color
        new.castling_rights = self.castling_rights
        new.ep_square = -1
        new.halfmove_clock = self.halfmove_clock + 1

        src = move.src
        dest = move.dest
        me = self.color
        opp = ~me

        piece = self.piece_on(src, me)

        # Clear source
        new._raw_clear(src, piece, me)

        # Capture at destination (including opponent pieces)
        captured = new.piece_on(dest, opp)
        if captured is not None:
            new._raw_clear(dest, captured, opp)
            new.halfmove_clock = 0

        # En passant capture
        if piece == Piece.PAWN and dest == self.ep_square:
            ep_captured_sq = dest + (-8 if me == Color.WHITE else 8)
            new._raw_clear(ep_captured_sq, Piece.PAWN, opp)
            new.halfmove_clock = 0

        # Place piece at destination
        final_piece = move.promo if move.promo is not None else piece
        new._raw_set(dest, final_piece, me)

        # Pawn-specific
        if piece == Piece.PAWN:
            new.halfmove_clock = 0
            # Double pawn push sets EP target
            diff = dest - src
            if diff == 16:  # White double push
                new.ep_square = src + 8
            elif diff == -16:  # Black double push
                new.ep_square = src - 8

        # Castling execution - move the rook
        if piece == Piece.KING:
            if src == E1 and dest == G1:  # White kingside
                new._raw_clear(H1, Piece.ROOK, me)
                new._raw_set(F1, Piece.ROOK, me)
            elif src == E1 and dest == C1:  # White queenside
                new._raw_clear(A1, Piece.ROOK, me)
                new._raw_set(D1, Piece.ROOK, me)
            elif src == E8 and dest == G8:  # Black kingside
                new._raw_clear(H8, Piece.ROOK, me)
                new._raw_set(F8, Piece.ROOK, me)
            elif src == E8 and dest == C8:  # Black queenside
                new._raw_clear(A8, Piece.ROOK, me)
                new._raw_set(D8, Piece.ROOK, me)

        # Update castling rights
        new.castling_rights &= CASTLING_RIGHTS_MASK[src]
        new.castling_rights &= CASTLING_RIGHTS_MASK[dest]

        new.color = opp
        return new

    def make_null_move(self):
        """Return a new board with side to move flipped (null move for NMP)."""
        new = ChessBoard()
        new.pieces = [self.pieces[0][:], self.pieces[1][:]]
        new.combined_color = self.combined_color[:]
        new.combined_all = self.combined_all
        new.color = ~self.color
        new.castling_rights = self.castling_rights
        new.ep_square = -1
        new.halfmove_clock = self.halfmove_clock
        new.zobrist_hash = self.zobrist_hash
        return new

    def _raw_clear(self, sq, piece, color):
        bb = 1 << sq
        nbb = ~bb
        self.pieces[color][piece] &= nbb
        self.combined_color[color] &= nbb
        self.combined_all &= nbb

    def _raw_set(self, sq, piece, color):
        bb = 1 << sq
        self.pieces[color][piece] |= bb
        self.combined_color[color] |= bb
        self.combined_all |= bb

    def init_game(self):
        self.pieces[Color.WHITE][Piece.PAWN]   = 0x000000000000FF00
        self.pieces[Color.WHITE][Piece.KNIGHT] = 0x0000000000000042
        self.pieces[Color.WHITE][Piece.BISHOP] = 0x0000000000000024
        self.pieces[Color.WHITE][Piece.ROOK]   = 0x0000000000000081
        self.pieces[Color.WHITE][Piece.QUEEN]  = 0x0000000000000008
        self.pieces[Color.WHITE][Piece.KING]   = 0x0000000000000010

        self.pieces[Color.BLACK][Piece.PAWN]   = 0x00FF000000000000
        self.pieces[Color.BLACK][Piece.KNIGHT] = 0x4200000000000000
        self.pieces[Color.BLACK][Piece.BISHOP] = 0x2400000000000000
        self.pieces[Color.BLACK][Piece.ROOK]   = 0x8100000000000000
        self.pieces[Color.BLACK][Piece.QUEEN]  = 0x0800000000000000
        self.pieces[Color.BLACK][Piece.KING]   = 0x1000000000000000

        for p in Piece:
            for c in Color:
                self.combined_color[c] |= self.pieces[c][p]

        self.combined_all = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]
        self.castling_rights = CASTLE_ALL
        self.ep_square = -1
        self.halfmove_clock = 0

        # Compute initial Zobrist hash
        from .zobrist import compute_hash
        self.zobrist_hash = compute_hash(self)
