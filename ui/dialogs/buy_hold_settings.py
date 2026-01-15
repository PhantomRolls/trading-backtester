import tkinter as tk
from tkinter import ttk
from utils.options_utils import save_yaml

def open_buy_and_hold_settings(self):
    window = tk.Toplevel(self.root)
    window.title("Paramètres Buy & Hold")

    reallocation_window = tk.StringVar(value=str(self.buy_and_hold_config.get("reallocation_window", 21)))
    rebalance_amount = tk.StringVar(value=str(self.buy_and_hold_config.get("reallocation_amount", 0)))

    def save():
        try:
            self.buy_and_hold_config["reallocation_window"] = int(reallocation_window.get())
            self.buy_and_hold_config["reallocation_amount"] = float(rebalance_amount.get())
            save_yaml(self.buy_and_hold_config, "config/buy_and_hold.yaml")
            window.destroy()
        except ValueError:
            tk.messagebox.showerror("Erreur", "Entrée invalide")

    ttk.Label(window, text="Période de réallocation (jours ouvrés)").grid(row=0, column=0, sticky='w', padx=10, pady=5)
    ttk.Entry(window, textvariable=reallocation_window).grid(row=0, column=1, padx=10)

    ttk.Label(window, text="Montant ajouté à chaque période ($)").grid(row=1, column=0, sticky='w', padx=10, pady=5)
    ttk.Entry(window, textvariable=rebalance_amount).grid(row=1, column=1, padx=10)

    ttk.Button(window, text="Enregistrer", command=save).grid(row=2, column=0, columnspan=2, pady=10)
