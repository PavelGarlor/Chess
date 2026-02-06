import time
import json
from datetime import datetime
from game.models.board_state import BoardState

TEST_NAME = "Initial Version - no improvements"
UPDATE_EVERY = 1000  # Update console every 1,000 nodes


def perft(board: BoardState, depth: int, turn: str, callback=None):
    """Return number of possible games to a certain depth with throttled real-time updates."""
    if depth == 0:
        if callback:
            callback(1)  # count this leaf node
        return 1

    moves = board.all_legal_moves(turn)
    total = 0

    for move in moves:
        captured, moves_done, status = board.make_move(move)
        next_turn = "white" if turn == "black" else "black"
        total += perft(board, depth - 1, next_turn, callback)
        board.undo_move(moves_done, captured)

    return total


def visualize_perft(
        initial_fen: str,
        max_depth: int = 4,
        test_name: str = "DefaultTest",
        save_file: str = "perft_results.json"
):
    """Run perft and store results with time, nodes, and NPS with throttled live updates."""

    # Load previous results
    try:
        with open(save_file, "r") as f:
            all_results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_results = []

    test_id = max([item.get("test_id", 0) for item in all_results], default=0) + 1

    board = BoardState(initial_fen)
    turn = board.is_whites_turn

    results = {
        "test_id": test_id,
        "test_name": test_name,
        "fen": initial_fen,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "depths": []
    }

    for d in range(1, max_depth + 1):
        start = time.perf_counter()
        nodes_so_far = 0

        # Define throttled callback
        def progress_callback(nodes=1):
            nonlocal nodes_so_far
            nodes_so_far += nodes
            if nodes_so_far % UPDATE_EVERY == 0:
                elapsed = time.perf_counter() - start
                print(
                    f"\rDepth {d} | Nodes: {nodes_so_far:,} | "
                    f"Elapsed: {elapsed:.2f}s", end=""
                )

        # Run perft with callback
        total_nodes = perft(board, d, turn, callback=progress_callback)
        elapsed = time.perf_counter() - start
        nps = total_nodes / elapsed if elapsed > 0 else 0

        # Finish line for depth
        print(
            f"\rDepth {d}: {total_nodes:,} nodes | "
            f"Time: {elapsed:.4f}s | "
            f"NPS: {nps:,.0f} nodes/sec"
        )

        results["depths"].append({
            "depth": d,
            "nodes": total_nodes,
            "time_seconds": round(elapsed, 4),
            "nps": int(nps)
        })

    all_results.append(results)
    with open(save_file, "w") as f:
        json.dump(all_results, f, indent=4)

    print(f"\nResults saved to {save_file} (test_id={test_id})")


if __name__ == "__main__":
    initial_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    visualize_perft(initial_FEN, max_depth=5, test_name=TEST_NAME)
