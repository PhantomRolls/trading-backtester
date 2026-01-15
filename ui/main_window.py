# ui/main_window.py
import tkinter as tk
from ui.app import StrategyApp


def run_ui():
    root = tk.Tk()
    app = StrategyApp(root)

    # Centrage
    root.geometry("700x500")
    root.update_idletasks()
    w, h = 700, 500
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    root.mainloop()
