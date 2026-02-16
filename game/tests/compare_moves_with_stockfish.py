import time
import json
from datetime import datetime
from game.models.board import Board
import chess

TEST_NAME = "Initial Version - depth comparison with Stockfish"
SAVE_TEST = False
UPDATE_EVERY = 1000

# Known perft values
KNOWN_PERFT = {
    1: 20,
    2: 400,
    3: 8902,
    4: 197281,
    5: 4865609,
    6: 119060324
}


def perft(board: Board, depth: int, turn: str, callback=None, compare_with_stockfish=False):
    if depth == 0:
        if callback:
            callback(1)
        return 1
    moves = board.generate_all_legal_moves()
    total = 0

    # Compare with Stockfish at this node if requested
    if compare_with_stockfish:
        fen = board.board_data.fen  # Make sure Board has get_fen() returning correct FEN
        your_uci = set([m.to_uci() for m in moves])
        stockfish_uci = set([m.uci() for m in chess.Board(fen).legal_moves])

        extra_moves = your_uci - stockfish_uci
        missing_moves = stockfish_uci - your_uci

        if extra_moves or missing_moves:
            print(f"\n[Discrepancy at depth {depth} | FEN: {fen}]")
            print("My moves:", sorted(your_uci))
            print("st moves:", sorted(stockfish_uci))
            if extra_moves:
                print("Extra moves:", sorted(extra_moves))
            if missing_moves:
                print("Missing moves:", sorted(missing_moves))

    for move in moves:
        captured, moves_done, status = board.make_move(move)
        next_turn = "white" if turn == "black" else "black"
        total += perft(board, depth - 1, next_turn, callback, compare_with_stockfish)
        board.undo_move(moves_done)

    return total


def visualize_perft(initial_fen: str, max_depth: int = 4,
                    compare_stockfish_depth: int = 2,
                    test_name: str = "DefaultTest",
                    file_name: str = "perft_results.json",
                    save_file: bool = False):

    try:
        with open(file_name, "r") as f:
            all_results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_results = []

    test_id = max([item.get("test_id", 0) for item in all_results], default=0) + 1
    board = Board(initial_fen)
    turn = "white" if board.board_data.is_whites_turn else "black"

    results = {
        "test_id": test_id,
        "test_name": test_name,
        "fen": initial_fen,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "depths": []
    }

    for d in range(1, max_depth + 1):
        update_every = 20000 if d == 4 else UPDATE_EVERY
        start = time.perf_counter()
        nodes_so_far = 0

        def progress_callback(nodes=1):
            nonlocal nodes_so_far
            nodes_so_far += nodes
            if nodes_so_far % update_every == 0:
                elapsed = time.perf_counter() - start
                print(f"\rDepth {d} | Nodes: {nodes_so_far:,} | Elapsed: {elapsed:.2f}s", end="", flush=True)

        # Compare with Stockfish at root or shallow depths
        compare_node = d <= compare_stockfish_depth

        total_nodes = perft(board, d, turn, callback=progress_callback, compare_with_stockfish=True)
        elapsed = time.perf_counter() - start
        nps = total_nodes / elapsed if elapsed > 0 else 0

        expected = KNOWN_PERFT.get(d)
        status = ""
        if expected is not None:
            status = "  ✅" if total_nodes == expected else f"  ❌ (expected {expected:,})"

        print(f"\rDepth {d}: {total_nodes:,} nodes | Time: {elapsed:.4f}s | NPS: {nps:,.0f} nodes/sec{status}")

        results["depths"].append({
            "depth": d,
            "nodes": total_nodes,
            "expected": expected,
            "correct": (total_nodes == expected),
            "time_seconds": round(elapsed, 4),
            "nps": int(nps)
        })

    all_results.append(results)
    if save_file:
        with open(file_name, "w") as f:
            json.dump(all_results, f, indent=4)

    print(f"\nResults saved to {file_name} (test_id={test_id})")


if __name__ == "__main__":
    initial_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    visualize_perft(initial_FEN, max_depth=4, compare_stockfish_depth=2,
                    test_name=TEST_NAME, save_file=SAVE_TEST)
