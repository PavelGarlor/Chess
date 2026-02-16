from game.models.board import Board
from game.move_generation.move_generator import MoveGenerator

initial_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# initial_fen = "8/8/8/4N3/8/8/8/8 w - - 0 1"
# initial_fen = "rnbqkbnr/pp1p1ppp/8/2p1p3/2PP4/8/PP2PPPP/RNBQKBNR w KQkq c6 0 1"

board = Board(initial_fen)

mg = MoveGenerator(board)

moves = mg.generate_all_moves()

print("Knight Moves:")
for i, move in enumerate(moves, start=1):
    print(f"{i:>3}.\t{move}")
