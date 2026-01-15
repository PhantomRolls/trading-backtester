import tkinter as tk
from tkinter import ttk

class StatusIndicator(tk.Canvas):
    def __init__(self, parent, size=12):
        super().__init__(parent, width=size, height=size, highlightthickness=0)

        # Get correct background from ttk style
        style = ttk.Style()
        bg_color = style.lookup("TLabelframe", "background")
        if not bg_color:
            bg_color = parent.cget("bg") if "bg" in parent.keys() else "white"

        self.configure(bg=bg_color)

        self.size = size

        # Draw green circle (default: OFF → hidden)
        self.circle = self.create_oval(
            1, 1, size-1, size-1,
            fill="green", outline=""
        )

        # Draw red cross (two lines) → hidden initially
        self.cross1 = self.create_line(
            2, 2, size-2, size-2,
            fill="red", width=3
        )
        self.cross2 = self.create_line(
            2, size-2, size-2, 2,
            fill="red", width=3
        )

        self.itemconfigure(self.circle, state="hidden")
        self.itemconfigure(self.cross1, state="normal")
        self.itemconfigure(self.cross2, state="normal")

    def set_green(self):
        """Display green circle, hide red cross."""
        self.itemconfigure(self.circle, state="normal")
        self.itemconfigure(self.cross1, state="hidden")
        self.itemconfigure(self.cross2, state="hidden")

    def set_red(self):
        """Display red cross, hide green circle."""
        self.itemconfigure(self.circle, state="hidden")
        self.itemconfigure(self.cross1, state="normal")
        self.itemconfigure(self.cross2, state="normal")
