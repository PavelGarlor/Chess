import time
from typing import List
from game.models.board import Board
from ai_engine.versions.ai_player import PlayerAI
from ai_engine.versions.v1_minimax_simple import SimpleMinimax
from ai_engine.versions.v2_minimax_prunning import SimpleMinimaxPruning
from ai_engine.versions.v3_pruning_move_ordering import PruningMoveOrdering

import time
import threading




# ---------------------------------------
# FEN to test
# ---------------------------------------
fen_position = "rnb1kbnr/pppqpppp/4P3/3p4/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"

# ---------------------------------------
# Initialize AI agents
# ---------------------------------------
agents: List[PlayerAI] = [
    SimpleMinimax("black", "SimpleMinimax", depth=2),
    SimpleMinimaxPruning("black", "SimpleMinimaxPruning", depth=2),
    PruningMoveOrdering("black", "PruningMoveOrdering", depth=4),
]


def monitor_progress(agent  : PlayerAI):
    last = -1
    while agent.searching:
        if agent.positions_evaluated != last:
            print(f"\r[{agent.username}] Nodes searched: {agent.positions_evaluated}", end="")
            last = agent.positions_evaluated
        time.sleep(0.2)
    print()  # newline after finishing

# ---------------------------------------
# Run test
# ---------------------------------------
for agent in agents:
    board_state = Board(fen=fen_position)

    agent.positions_evaluated = 0
    agent.searching = True

    print(f"\n=== Testing {agent.username} ===")

    # Start progress monitor thread
    t = threading.Thread(target=monitor_progress, args=(agent,), daemon=True)
    t.start()

    start_time = time.time()
    move = agent.request_move(board_state)
    agent.searching = False   # stop monitoring
    end_time = time.time()

    t.join()  # wait for monitor to exit

    print(f"Best move: {move}")
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print(f"Nodes explored: {agent.positions_evaluated}")

