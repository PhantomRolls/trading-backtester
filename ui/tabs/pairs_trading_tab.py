# ui/tabs/pairs_trading_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import importlib
import config
from ui.dialogs.pairs_trading_settings import open_pairs_trading_settings
from ui.widgets.value_label import ValueLabel
from utils.options_utils import save_yaml


def create_pairs_trading_tab(app):
    frame = ttk.Frame(app.notebook)
    app.notebook.add(frame, text="Pairs Trading")

    # ---------- HEADER ----------
    header = ttk.Frame(frame)
    header.pack(fill="x", pady=5)

    ttk.Button(
        header, text="⚙️", width=3,
        command=lambda: open_pairs_trading_settings(app)
    ).pack(side="right")

    ttk.Label(frame, text="Paire (ex: AAPL,MSFT) :").pack()

    last_pair = app.pairs_trading_config.get("pair", "")
    pair_var = tk.StringVar(value=last_pair)

    def on_change_pair(*_):
        app.pairs_trading_config["pair"] = pair_var.get()
        save_yaml(app.pairs_trading_config, "config/pairs_trading.yaml")

    pair_var.trace_add("write", on_change_pair)
    ttk.Entry(frame, textvariable=pair_var).pack(pady=3)

    # Plot checkbox
    plot_var = tk.BooleanVar(value=app.plot_vars.get("Pairs Trading", False))
    ttk.Checkbutton(frame, text="Afficher le plot", variable=plot_var).pack()

    # ======================================================
    # Résultats du Backtest
    # ======================================================
    result_frame = ttk.LabelFrame(frame, text="Résultats du Backtest")
    result_frame.pack(fill="x", padx=10, pady=10)

    STAT_CONFIG = {
        "Annualized Return (%)": "%",
        "Annualized Volatility (%)": "%",
        "Sharpe Ratio": "",
        "Max Drawdown (%)": "%",
        "Win Rate (%)": "%",
        "Total Return (%)": "%",
        "Hedge Ratio": "",
        "Half-Life": "",
    }

    # En-têtes
    ttk.Label(result_frame, text="Statistique").grid(row=0, column=0, sticky="w")
    ttk.Label(result_frame, text="Portefeuille").grid(row=0, column=1, sticky="w")
    ttk.Label(result_frame, text="Benchmark").grid(row=0, column=2, sticky="w")

    pairs_labels = {}
    row = 1

    for stat, suffix in STAT_CONFIG.items():
        ttk.Label(result_frame, text=stat).grid(row=row, column=0, sticky="w", pady=2)

        lbl_port = ValueLabel(result_frame, label="", suffix=suffix)
        lbl_port.grid(row=row, column=1, sticky="w", padx=10)

        lbl_bench = ValueLabel(result_frame, label="", suffix=suffix)
        lbl_bench.grid(row=row, column=2, sticky="w", padx=10)

        pairs_labels[stat] = (lbl_port, lbl_bench)
        row += 1

    # ======================================================
    # Bouton : Lancer le backtest
    # ======================================================
    def launch():
        from strategies.pairs_trading import PairsTradingStrategy
        importlib.reload(config)

        pair_input = pair_var.get().strip()

        try:
            symbols = [s.strip().upper() for s in pair_input.split(",")]
            if len(symbols) != 2:
                raise ValueError
            pair = tuple(symbols)

        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer deux symboles séparés par une virgule.")
            return

        app.pairs_trading_config["pair"] = pair_input
        save_yaml(app.pairs_trading_config, "config/pairs_trading.yaml")

        strategy = PairsTradingStrategy(pair)
        all_stats = strategy.run_backtest(plot=plot_var.get())  # <- doit renvoyer DataFrame

        # Mise à jour du tableau
        for stat, (lbl_port, lbl_bench) in pairs_labels.items():
            try:
                v_port  = all_stats.loc[stat, "Portefeuille"]
                v_bench = all_stats.loc[stat, "Benchmark"]
            except:
                v_port = v_bench = None

            lbl_port.set(stat, v_port)
            lbl_bench.set(stat, v_bench)

    ttk.Button(frame, text="Lancer le backtest", command=launch).pack(pady=8)
