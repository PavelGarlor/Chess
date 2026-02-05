import time
from game.models.board_state import BoardState


def perft(board: BoardState, depth: int, turn: str):
    """Return number of possible games to a certain depth."""
    if depth == 0:
        return 1

    moves = board.all_legal_moves(turn)
    total = 0

    for move in moves:
        captured, moves_done, status = board.make_move(move)
        next_turn = "white" if turn == "black" else "black"
        total += perft(board, depth - 1, next_turn)
        board.undo_move(moves_done, captured)

    return total


def visualize_perft(initial_fen: str, max_depth: int = 4):
    board = BoardState(initial_fen)
    turn = board.current_turn

    for d in range(1, max_depth + 1):
        start = time.perf_counter()
        nodes = perft(board, d, turn)
        end = time.perf_counter()

        elapsed = end - start
        nps = nodes / elapsed if elapsed > 0 else 0

        print(
            f"Depth {d}: {nodes:,} nodes | "
            f"Time: {elapsed:.4f}s | "
            f"NPS: {nps:,.0f} nodes/sec"
        )


# RUN
initial_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
visualize_perft(initial_FEN, 4)
