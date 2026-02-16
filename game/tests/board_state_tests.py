import unittest

from game.models.board import Board


class BoardStateTests(unittest.TestCase):

    def setUp(self):
        self.fen_list = [
            "rnbqkbnr/1ppppppp/p7/8/8/N7/PPPPPPPP/R3KBNR w KQkq - 0 2"
            # "rnbqkbnr/pp3p1p/2ppp1p1/8/3P1B2/N2Q4/PPP1PPPP/R3KBNR w KQkq - 0 1",
            # "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            # "rnbqkbnr/ppp1pppp/3p4/8/8/N1P5/PP1PPPPP/R1BQKBNR b KQkq - 1 1",
            # "rnb1kbnr/pppq1ppp/8/1B1pp3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1",
        ]

    def test_undo_move_should_recover_board_state(self):
        test_name = "undo_move_should_recover_board_state"
        print(f"[{test_name}] Running...")

        for fen_idx, fen in enumerate(self.fen_list, start=1):
            print(f"\n--- Testing FEN #{fen_idx} ---")
            print(f"FEN: {fen}")

            board = Board(fen)

            # Generate all legal moves for side to move
            moves = board.generate_all_legal_moves()

            self.assertGreater(len(moves), 0, f"No legal moves found for FEN #{fen_idx}")

            for idx, move in enumerate(moves, start=1):

                board_to_mutate = board.copy()

                captured_piece, moves_done, status = board_to_mutate.make_move(move)
                # Undo
                board_to_mutate.undo_move(moves_done)

                # Compare final board with original
                equal_boards = board == board_to_mutate

                self.assertTrue(
                    equal_boards,
                    f"Undo move failed for FEN #{fen_idx}, move #{idx}: {move}"
                )

        print(f"[{test_name}] ✅ All FENs passed.")


