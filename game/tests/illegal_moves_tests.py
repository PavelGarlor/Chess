import unittest

from game.models.board import Board


class IllegalTests(unittest.TestCase):

    def assertMoveNotGenerated(self, legal_moves, illegal_uci, message):
        """
        Helper: legal_moves is a list of Move objects.
        We turn them into UCI strings and verify the illegal one is not present.
        """
        generated = [m.to_uci() for m in legal_moves]
        self.assertNotIn(illegal_uci, generated, message)

    def test_pawn_forward_move_illegal_when_pinned(self):
        """
        White pawn on e2 is pinned by black bishop on b5.
        FEN: rnbqkbnr/pppppppp/8/1b6/8/8/4P3/RNBQKBNR w KQkq - 0 1
        """
        fen = "2k5/8/2p5/7q/8/8/4P3/3K4 w - - 0 1"
        board = Board(fen)

        legal_moves = board.generate_all_legal_moves()

        # Convert each move to UCI (mirrors your required pattern)
        for move in legal_moves:
            move.to_uci()

        self.assertMoveNotGenerated(
            legal_moves,
            "e2e3",
            "Pinned pawn should NOT be allowed to play e2e3."
        )

        self.assertMoveNotGenerated(
            legal_moves,
            "e2e4",
            "Pinned pawn should NOT be allowed to play e2e4."
        )

    def test_pawn_capture_illegal_when_pinned(self):
        """
        Pawn d2 is pinned by rook on d8.
        Cannot capture c3.
        FEN: 3r4/8/8/8/8/2p5/3P4/3K4 w - - 0 1
        """
        fen = "2kq4/8/2p5/3P4/8/8/8/3K4 w - - 0 1"
        board = Board(fen)

        legal_moves = board.generate_all_legal_moves()

        for move in legal_moves:
            move.to_uci()

        self.assertMoveNotGenerated(
            legal_moves,
            "d5c6",
            "Pinned pawn should NOT be able to capture diagonally."
        )

    def test_en_passant_illegal_when_pawn_pinned(self):
        """
        Pawn e5 is pinned by rook on e8.
        En passant at f6 is normally legal but must NOT be allowed.
        FEN: r3k2r/5ppp/8/4Pp2/8/8/8/4K3 w - f6 0 2
        """
        fen = "2kq4/8/8/2pP4/8/8/8/3K4 w - c6 0 1"
        board = Board(fen)

        legal_moves = board.generate_all_legal_moves()

        for move in legal_moves:
            move.to_uci()

        self.assertMoveNotGenerated(
            legal_moves,
            "d5c6",
            "En passant should be illegal when pawn is pinned."
        )

    def test_bishop_move_illegal_when_pinned(self):
        """
        Bishop on c2 is pinned by black queen on c7 against king on c1.
        Therefore the bishop must have zero legal moves.

        FEN: 2k5/2q5/8/8/8/8/2B5/2K5 w - - 0 1
        """
        fen = "2k5/2q5/8/8/8/8/2B5/2K5 w - - 0 1"
        board = Board(fen)

        legal_moves = board.generate_all_legal_moves()

        # Convert moves to UCI
        uci_moves = [m.to_uci() for m in legal_moves]

        # Check if any illegal move starts with c2
        illegal_moves = [uci for uci in uci_moves if uci.startswith("c2")]

    def test_not_illegal_move_king_on_check(self):
        """
        Bishop on c2 is pinned by black queen on d7 against the king on d1.
        Therefore the bishop must have zero legal moves.

        FEN: k7/3q4/8/8/8/8/7R/3K4 w - - 0 1
        """
        fen = "k7/3q4/8/8/8/8/7R/3K4 w - - 0 1"
        board = Board(fen)
        legal_moves = board.generate_all_legal_moves()

        # Convert to UCI
        uci_moves = sorted(m.to_uci() for m in legal_moves)

        # Expected legal moves
        expected_moves = sorted([
            "h2e2",
            "d1c1", "d1c2",
            "d1e1", "d1e2",
        ])

        # Ensure no move starts with c2
        illegal_moves = [uci for uci in uci_moves if uci.startswith("c2")]
        if illegal_moves:
            self.fail(
                "Pinned bishop on c2 generated illegal moves:\n"
                f"  Illegal: {illegal_moves}\n"
                f"  All moves: {uci_moves}"
            )

        # Ensure exact match to expected legal moves
        self.assertEqual(
            uci_moves,
            expected_moves,
            msg=(
                "Legal moves do not match expected.\n"
                f"  Expected: {expected_moves}\n"
                f"  Got:      {uci_moves}"
            )
        )


if __name__ == "__main__":
    unittest.main()