class Square:
    def __init__(self, index):
        self.index = int(index)

    @classmethod
    def from_position(cls, r, f):
        return cls((r.value << 3) | f.value)

    def to_bitboard(self):
        return 1 << self.index
