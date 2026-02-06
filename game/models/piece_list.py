class PieceList:
    """
    Maintains a list of squares occupied by a certain piece type.
    Only the first `num_pieces` elements in `occupied_squares` are valid.
    """

    def __init__(self, max_piece_count: int = 16):
        # Indices of squares occupied by given piece type
        self.occupied_squares = [0] * max_piece_count
        # Map from square index to index in `occupied_squares` array
        self._map = [0] * 64
        self._num_pieces = 0

    @property
    def count(self) -> int:
        """Number of pieces currently in the list."""
        return self._num_pieces

    def add_piece_at_square(self, square: int):
        """Add a piece at the given square."""
        self.occupied_squares[self._num_pieces] = square
        self._map[square] = self._num_pieces
        self._num_pieces += 1

    def remove_piece_at_square(self, square: int):
        """Remove a piece from the given square."""
        piece_index = self._map[square]  # index in occupied_squares
        last_square = self.occupied_squares[self._num_pieces - 1]
        # Move last element into removed element's slot
        self.occupied_squares[piece_index] = last_square
        self._map[last_square] = piece_index
        self._num_pieces -= 1

    def move_piece(self, start_square: int, target_square: int):
        """Move a piece from start_square to target_square."""
        piece_index = self._map[start_square]
        self.occupied_squares[piece_index] = target_square
        self._map[target_square] = piece_index

    def __getitem__(self, index: int) -> int:
        """Enable indexing like piece_list[i] to access occupied squares."""
        if index >= self._num_pieces:
            raise IndexError("Index out of bounds of occupied squares")
        return self.occupied_squares[index]
