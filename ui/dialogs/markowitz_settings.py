import tkinter as tk
from tkinter import ttk
from utils.options_utils import save_yaml

def open_markowitz_settings(self):
    window = tk.Toplevel(self.root)
    window.title("Paramètres Markowitz")

    lookback_window = tk.StringVar(value=str(self.markowitz_config.get("lookback_window", 21)))
    rebalance_window = tk.StringVar(value=str(self.markowitz_config.get("rebalance_window", 21)))
    risk_free_rate = tk.StringVar(value=str(self.markowitz_config.get("risk_free_rate", 0.0)))
    diversification = tk.StringVar(value=str(self.markowitz_config.get("diversification", 0.0)))

    def save():
        try:
            self.markowitz_config["lookback_window"] = int(lookback_window.get())
            self.markowitz_config["rebalance_window"] = int(rebalance_window.get())
            self.markowitz_config["risk_free_rate"] = float(risk_free_rate.get())
            self.markowitz_config["diversification"] = float(diversification.get())
            save_yaml(self.markowitz_config, "config/markowitz.yaml")
            window.destroy()
        except ValueError:
            tk.messagebox.showerror("Erreur", "Entrée invalide")

    ttk.Label(window, text="Fenêtre d'optimisation").grid(row=0, column=0, sticky='w', padx=10, pady=5)
    ttk.Entry(window, textvariable=lookback_window).grid(row=0, column=1, padx=10)

    ttk.Label(window, text="Fenêtre de rééquilibrage").grid(row=1, column=0, sticky='w', padx=10, pady=5)
    ttk.Entry(window, textvariable=rebalance_window).grid(row=1, column=1, padx=10)

    ttk.Label(window, text="Taux sans risque (%)").grid(row=2, column=0, sticky='w', padx=10, pady=5)
    ttk.Entry(window, textvariable=risk_free_rate).grid(row=2, column=1, padx=10)

    ttk.Label(window, text="Diversification").grid(row=3, column=0, sticky='w', padx=10, pady=5)
    ttk.Entry(window, textvariable=diversification).grid(row=3, column=1, padx=10)

    ttk.Button(window, text="Enregistrer", command=save).grid(row=4, column=0, columnspan=2, pady=10)
