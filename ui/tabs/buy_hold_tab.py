# ui/tabs/buy_hold_tab.py
import tkinter as tk
from tkinter import ttk
import importlib
import config
from ui.dialogs.buy_hold_settings import open_buy_and_hold_settings
from ui.widgets.value_label import ValueLabel
from utils.options_utils import save_yaml

def create_buy_hold_tab(app):
    frame = ttk.Frame(app.notebook)
    app.notebook.add(frame, text="Buy & Hold")

    header = ttk.Frame(frame)
    header.pack(fill="x", pady=5)
    
    ttk.Button(
        header, text="⚙️", width=3,
        command=lambda: open_buy_and_hold_settings(app)
    ).pack(side="right")

    ttk.Label(frame, text="Preset:").pack(pady=5)

    last_preset = app.buy_and_hold_config.get("buy_and_hold_preset", "balanced")
    preset_var = tk.StringVar(value=last_preset)

    def on_change(*_):
        app.buy_and_hold_config["buy_and_hold_preset"] = preset_var.get()
        save_yaml(app.buy_and_hold_config, "config/buy_and_hold.yaml")

    preset_var.trace_add("write", on_change)

    preset_menu = ttk.Combobox(
        frame,
        textvariable=preset_var,
        values=list(app.buy_and_hold_config["portfolio_presets"].keys())
    )
    preset_menu.pack()

    plot_var = tk.BooleanVar(value=app.plot_vars.get("Buy & Hold", False))
    ttk.Checkbutton(frame, text="Afficher le plot", variable=plot_var).pack(pady=3)

    # -------- Résultats du backtest --------
    result_frame = ttk.LabelFrame(frame, text="Résultats du Backtest")
    result_frame.pack(fill="x", padx=10, pady=10)

    STAT_CONFIG = {
        "Annualized Return (%)":     "%",
        "Annualized Volatility (%)": "%",
        "Sharpe Ratio":              "",
        "Max Drawdown (%)":          "%",
        "Total Return (%)":          "%",
        "Frais (%)":                 "%",
        "Diversification":           "",
    }

    stat_labels = {}

    # --- En-têtes alignés ---
    ttk.Label(result_frame, text="Statistique").grid(row=0, column=0, sticky="w", padx=5)
    ttk.Label(result_frame, text="Portefeuille").grid(row=0, column=1, sticky="w", padx=5)
    ttk.Label(result_frame, text="Benchmark").grid(row=0, column=2, sticky="w", padx=5)

    # --- Lignes du tableau ---
    row = 1
    for stat, suffix in STAT_CONFIG.items():
        ttk.Label(result_frame, text=stat).grid(row=row, column=0, sticky="w", padx=5)

        portfolio_lbl = ValueLabel(result_frame, label="", suffix=suffix)
        portfolio_lbl.grid(row=row, column=1, sticky="w", padx=10)

        benchmark_lbl = ValueLabel(result_frame, label="", suffix=suffix)
        benchmark_lbl.grid(row=row, column=2, sticky="w", padx=10)

        stat_labels[stat] = (portfolio_lbl, benchmark_lbl)
        row += 1


    # -------- Lancer le backtest --------
    def launch():
        from strategies.buy_and_hold import BuyAndHold
        importlib.reload(config)

        strategy = BuyAndHold(preset=preset_var.get())
        all_stats = strategy.run_backtest(plot=plot_var.get())  # retourne un DataFrame

        # 🔥 ICI on parcourt bien stat_labels
        for stat, (lbl_port, lbl_bench) in stat_labels.items():

            try:
                v_port = all_stats.loc[stat, "Portefeuille"]
                v_bench = all_stats.loc[stat, "Benchmark"]
            except:
                v_port = v_bench = None

            lbl_port.set(stat, v_port)
            lbl_bench.set(stat, v_bench)

    ttk.Button(frame, text="Lancer le backtest", command=launch).pack(pady=10)
