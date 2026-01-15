import tkinter as tk
from tkinter import ttk
from utils.options_utils import save_yaml

def open_pairs_trading_settings(self):
    window = tk.Toplevel(self.root)
    window.title("Paramètres Pairs Trading")

    spread_window = tk.StringVar(value=str(self.pairs_trading_config.get("window", 252)))
    z_enter = tk.StringVar(value=str(self.pairs_trading_config.get("z_enter", 2)))
    z_exit = tk.StringVar(value=str(self.pairs_trading_config.get("z_exit", 1)))

    def save():
        try:
            self.pairs_trading_config["window"] = int(spread_window.get())
            self.pairs_trading_config["z_enter"] = float(z_enter.get())
            self.pairs_trading_config["z_exit"] = float(z_exit.get())
            save_yaml(self.pairs_trading_config, "config/pairs_trading.yaml")
            window.destroy()
        except ValueError:
            tk.messagebox.showerror("Erreur", "Entrée invalide")

    ttk.Label(window, text="Fenêtre du Z-score").grid(row=0, column=0, sticky='w', padx=10, pady=5)
    ttk.Entry(window, textvariable=spread_window).grid(row=0, column=1, padx=10)

    ttk.Label(window, text="Seuil d'entrée (Z)").grid(row=1, column=0, sticky='w', padx=10, pady=5)
    ttk.Entry(window, textvariable=z_enter).grid(row=1, column=1, padx=10)

    ttk.Label(window, text="Seuil de sortie (Z)").grid(row=2, column=0, sticky='w', padx=10, pady=5)
    ttk.Entry(window, textvariable=z_exit).grid(row=2, column=1, padx=10)

    ttk.Button(window, text="Enregistrer", command=save).grid(row=3, column=0, columnspan=2, pady=10)
