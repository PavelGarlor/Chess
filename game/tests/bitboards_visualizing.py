import tkinter as tk
from tkinter import ttk, simpledialog
import json
import os

BOARD_SIZE = 8
BOARD_PIXELS = 300
SAVE_FILE = "bitboards.json"

# --------------------------
# Bitboard class
# --------------------------
class Bitboard:
    def __init__(self, value=0):
        self.value = value

    def toggle(self, sq):
        self.value ^= (1 << sq)

    def is_set(self, sq):
        return (self.value >> sq) & 1

# --------------------------
# Bitboard App
# --------------------------
class BitboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Bitboard Equation Visualizer")

        # Dictionary of named bitboards
        self.boards = {
            "A": Bitboard(),
            "B": Bitboard()
        }

        # Load persisted boards
        self.load_boards()

        self.selectedA = tk.StringVar(value="A")
        self.selectedB = tk.StringVar(value="B")
        self.operation = tk.StringVar(value="OR")
        self.shift_amount = tk.IntVar(value=0)

        self.make_layout()
        self.draw_main()

    # --------------------------
    # Persistence
    # --------------------------
    def save_boards(self):
        data = {name: bb.value for name, bb in self.boards.items()}
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)

    def load_boards(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                for name, value in data.items():
                    self.boards[name] = Bitboard(value)

    # --------------------------
    # UI layout
    # --------------------------
    def make_layout(self):
        container = tk.Frame(self.root)
        container.pack(padx=10, pady=10)

        # Left panel: saved boards
        left_panel = tk.Frame(container)
        left_panel.grid(row=0, column=0, sticky="n")

        tk.Label(left_panel, text="Saved Bitboards").pack()
        self.listbox = tk.Listbox(left_panel, height=12, width=18)
        self.listbox.pack(pady=5)
        self.refresh_listbox()

        tk.Button(left_panel, text="Create New Board", command=self.create_board).pack(fill="x")
        tk.Button(left_panel, text="Delete Selected", command=self.delete_board).pack(fill="x")
        tk.Button(left_panel, text="Load as A", command=lambda: self.load_board("A")).pack(fill="x")
        tk.Button(left_panel, text="Load as B", command=lambda: self.load_board("B")).pack(fill="x")

        # Center panel: canvases
        mid_panel = tk.Frame(container)
        mid_panel.grid(row=0, column=1, padx=20)

        tk.Label(mid_panel, text="Board A").grid(row=0, column=0)
        self.canvasA = tk.Canvas(mid_panel, width=BOARD_PIXELS, height=BOARD_PIXELS)
        self.canvasA.grid(row=1, column=0)
        self.canvasA.bind("<Button-1>", lambda e: self.on_click(e, self.boards[self.selectedA.get()]))

        tk.Label(mid_panel, text="Board B").grid(row=0, column=1)
        self.canvasB = tk.Canvas(mid_panel, width=BOARD_PIXELS, height=BOARD_PIXELS)
        self.canvasB.grid(row=1, column=1)
        self.canvasB.bind("<Button-1>", lambda e: self.on_click(e, self.boards[self.selectedB.get()]))

        # Right panel: operations
        op_panel = tk.Frame(container)
        op_panel.grid(row=0, column=2, sticky="n")

        tk.Label(op_panel, text="Operation").pack()
        for text, val in [
            ("A OR B", "OR"),
            ("A AND B", "AND"),
            ("A XOR B (bitwise add)", "XOR"),
            ("A << x", "SHIFT_A"),
            ("B << x", "SHIFT_B"),
        ]:
            ttk.Radiobutton(op_panel, text=text, variable=self.operation, value=val,
                            command=self.update_result).pack(anchor="w")
        tk.Button(op_panel, text="Negate A (RAM only)", command=lambda: self.negate_board("A")).pack(fill="x", pady=2)
        tk.Button(op_panel, text="Negate B (RAM only)", command=lambda: self.negate_board("B")).pack(fill="x", pady=2)

        tk.Label(op_panel, text="Shift Amount:").pack()
        tk.Spinbox(op_panel, from_=0, to=63, textvariable=self.shift_amount,
                   command=self.update_result).pack()

        tk.Label(op_panel, text="Result").pack(pady=10)
        self.canvasR = tk.Canvas(op_panel, width=BOARD_PIXELS, height=BOARD_PIXELS)
        self.canvasR.pack()

        tk.Button(op_panel, text="Save Result As...", command=self.save_result).pack(pady=5)

    # --------------------------
    # Utility functions
    # --------------------------
    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for name in self.boards.keys():
            self.listbox.insert(tk.END, name)

    def create_board(self):
        name = simpledialog.askstring("New Board", "Enter name:")
        if not name or name in self.boards:
            return
        self.boards[name] = Bitboard()
        self.refresh_listbox()
        self.save_boards()

    def delete_board(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        if name in ("A", "B"):
            return
        del self.boards[name]
        self.refresh_listbox()
        self.save_boards()

    def load_board(self, target):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        self.boards[target].value = self.boards[name].value
        self.draw_main()

    def save_result(self):
        name = simpledialog.askstring("Save Result", "Name for result:")
        if not name:
            return
        self.boards[name] = Bitboard(self.R.value)
        self.refresh_listbox()
        self.save_boards()

    # --------------------------
    # Drawing
    # --------------------------
    def draw_board(self, canvas, bb: Bitboard):
        canvas.delete("all")
        sq = BOARD_PIXELS // BOARD_SIZE
        for r in range(8):
            for c in range(8):
                bit = (7 - r) * 8 + c
                color = "black" if bb.is_set(bit) else "white"
                canvas.create_rectangle(c*sq, r*sq, (c+1)*sq, (r+1)*sq, fill=color, outline="gray")

    def draw_main(self):
        self.draw_board(self.canvasA, self.boards[self.selectedA.get()])
        self.draw_board(self.canvasB, self.boards[self.selectedB.get()])
        self.update_result()

    # --------------------------
    # Events
    # --------------------------
    def on_click(self, event, board: Bitboard):
        sq_size = BOARD_PIXELS // BOARD_SIZE
        c = event.x // sq_size
        r = event.y // sq_size
        bit = (7 - r) * 8 + c
        board.toggle(bit)
        self.draw_main()
        self.save_boards()

    def negate_board(self, name):
        # Negate the board in memory
        self.boards[name].value = (~self.boards[name].value) & ((1 << 64) - 1)
        # Redraw to reflect immediately
        self.draw_main()
        # DO NOT save to file — keeps persistence unchanged

    # --------------------------
    # Operations
    # --------------------------
    def bitwise_add(self, a, b):
        return a ^ b  # bitwise add without carry for chess

    def update_result(self):
        A = self.boards[self.selectedA.get()].value
        B = self.boards[self.selectedB.get()].value
        op = self.operation.get()

        if op == "OR":
            R = A | B
        elif op == "AND":
            R = A & B
        elif op == "XOR":
            R = self.bitwise_add(A, B)
        elif op == "SHIFT_A":
            R = (A << self.shift_amount.get()) & ((1 << 64) - 1)
        elif op == "SHIFT_B":
            R = (B << self.shift_amount.get()) & ((1 << 64) - 1)
        elif op == "NEG_A":
            R = (~A) & ((1 << 64) - 1)
        elif op == "NEG_B":
            R = (~B) & ((1 << 64) - 1)
        else:
            R = 0

        self.R = Bitboard(R)
        self.draw_board(self.canvasR, self.R)

# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = BitboardApp(root)
    root.mainloop()
