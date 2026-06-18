import tkinter as tk

BG = "#f4f0ea"
DSP_BG = "#ffffff"
MAIN_FG = "#1d1d1b"
EXPR_FG = "#b5b2ab"

N_BG = "#e8e4dc"
N_FG = "#1d1d1b"

OP_BG = "#e07a4e"
OP_FG = "#ffffff"

EQ_BG = "#2b2e52"
EQ_FG = "#ffffff"

U_BG = "#d3cfc7"
U_FG = "#3a3a3a"


class Calc:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simple Calculator")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.current = ""
        self.first = None
        self.operator = None

        self.build_ui()
        self.root.mainloop()

    def build_ui(self):
        tk.Label(
            self.root,
            text="Simple Calculator",
            font=("Helvetica", 10),
            fg=EXPR_FG,
            bg=BG
        ).pack(anchor="w", padx=20, pady=(16, 0))

        card = tk.Frame(self.root, bg=DSP_BG)
        card.pack(fill=tk.X, padx=18, pady=(6, 10))

        self.expr_var = tk.StringVar()
        tk.Label(
            card,
            textvariable=self.expr_var,
            font=("Helvetica", 11),
            fg=EXPR_FG,
            bg=DSP_BG,
            anchor="e",
            padx=16
        ).pack(fill=tk.X, pady=(14, 0))

        self.display_var = tk.StringVar(value="0")
        tk.Label(
            card,
            textvariable=self.display_var,
            font=("Helvetica", 44, "bold"),
            fg=MAIN_FG,
            bg=DSP_BG,
            anchor="e",
            padx=16,
            pady=10
        ).pack(fill=tk.X)

        grid = tk.Frame(self.root, bg=BG)
        grid.pack(padx=18, pady=(0, 18))

        layout = [
            [("AC", "ac", "u"), ("delete", "bk", "u"), ("", "none", "u"), ("÷", "/", "o")],
            [("7", "7", "n"), ("8", "8", "n"), ("9", "9", "n"), ("×", "*", "o")],
            [("4", "4", "n"), ("5", "5", "n"), ("6", "6", "n"), ("−", "-", "o")],
            [("1", "1", "n"), ("2", "2", "n"), ("3", "3", "n"), ("+", "+", "o")],
            [("0", "0", "n"), (".", ".", "n"), ("=", "=", "e")]
        ]

        styles = {
            "n": (N_BG, N_FG, ("Helvetica", 19)),
            "o": (OP_BG, OP_FG, ("Helvetica", 19, "bold")),
            "e": (EQ_BG, EQ_FG, ("Helvetica", 19, "bold")),
            "u": (U_BG, U_FG, ("Helvetica", 14))
        }

        for r, row in enumerate(layout):
            for c, (text, action, style) in enumerate(row):
                bg, fg, font = styles[style]

                tk.Button(
                    grid,
                    text=text,
                    font=font,
                    fg=fg,
                    bg=bg,
                    activebackground=bg,
                    activeforeground=fg,
                    relief="flat",
                    bd=0,
                    width=5,
                    height=2,
                    cursor="hand2",
                    command=lambda a=action: self.handle(a)
                ).grid(row=r, column=c, padx=4, pady=4)

    def handle(self, action):
        if action == "none":
            return

        if action.isdigit() or action == ".":
            self.add_digit(action)

        elif action in "+-*/":
            self.set_operator(action)

        elif action == "=":
            self.calculate()

        elif action == "ac":
            self.clear()

        elif action == "bk":
            self.backspace()

    def add_digit(self, digit):
        if digit == "." and "." in self.current:
            return

        self.current += digit
        self.display_var.set(self.current)

    def set_operator(self, op):
        if self.current == "":
            return

        self.first = float(self.current)
        self.operator = op

        symbols = {
            "+": "+",
            "-": "−",
            "*": "×",
            "/": "÷"
        }

        self.expr_var.set(f"{self.current} {symbols[op]}")
        self.current = ""

    def calculate(self):
        if self.first is None or self.current == "":
            return

        second = float(self.current)

        try:
            if self.operator == "+":
                result = self.first + second

            elif self.operator == "-":
                result = self.first - second

            elif self.operator == "*":
                result = self.first * second

            elif self.operator == "/":
                result = self.first / second

            result = str(int(result)) if result == int(result) else str(result)

            self.expr_var.set(
                f"{self.first} {self.operator} {second} ="
            )

            self.display_var.set(result)
            self.current = result

        except ZeroDivisionError:
            self.display_var.set("Error")
            self.expr_var.set("Cannot divide by zero")

    def clear(self):
        self.current = ""
        self.first = None
        self.operator = None

        self.display_var.set("0")
        self.expr_var.set("")

    def backspace(self):
        self.current = self.current[:-1]
        self.display_var.set(self.current if self.current else "0")


if __name__ == "__main__":
    Calc()