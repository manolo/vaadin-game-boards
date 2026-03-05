class Move(object):
    __slots__ = ('src', 'dest', 'promo')

    def __init__(self, src, dest, promo=None):
        """
        src and dest are plain int square indices (0-63).
        promo is Piece representing promotion.
        """
        self.src = src
        self.dest = dest
        self.promo = promo
