class Move:
    def __init__(self, start_pos: tuple[int, int], target_pos: tuple[int, int], promotion=None, castling=False,
                 en_passant=False):
        self.start_pos = start_pos
        self.target_pos = target_pos
        self.promotion = promotion
        self.castling = castling
        self.en_passant = en_passant

    def __str__(self):
        return f"{self.start_pos} -> {self.target_pos}"

    __repr__ = __str__  # optional, so lists of moves print nicely

    def to_uci(self):
        """
        Convert the move to UCI notation, e.g. (4,1)->(4,3) becomes 'e2e4'.
        Handles promotion if present.
        Assumes 0,0 = a1, 7,7 = h8 (white perspective).
        """

        def pos_to_square(pos):
            file = chr(ord('a') + pos[0])
            rank = str(pos[1] + 1)
            return file + rank

        uci_str = pos_to_square(self.start_pos) + pos_to_square(self.target_pos)

        # Append promotion piece in lowercase if present
        if self.promotion:
            # Expecting promotion class, e.g., Queen -> 'q'
            uci_str += self.promotion_symbol().lower()

        return uci_str

    def promotion_symbol(self):
        """Return the symbol for the promotion piece"""
        # Example: if self.promotion is Queen class, return 'q'
        if self.promotion is None:
            return ''
        # Assume the promotion class has a SYMBOL attribute like 'Q', 'R', etc.
        return getattr(self.promotion, 'SYMBOL', 'q')
