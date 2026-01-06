# ui/tabs/markowitz_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import importlib
import config
from ui.dialogs.markowitz_settings import open_markowitz_settings
from ui.widgets.tooltip import ToolTip
from ui.widgets.value_label import ValueLabel
from utils.options_utils import save_yaml

def create_markowitz_tab(app):
    """
    Crée l'onglet Markowitz dans le Notebook principal.
    """
    frame = ttk.Frame(app.notebook)
    app.notebook.add(frame, text="Markowitz")

    # ---------- HEADER ----------
    header = ttk.Frame(frame)
    header.pack(fill="x", pady=5)
    ttk.Button(header, text="⚙️", width=3,
               command=lambda: open_markowitz_settings(app)).pack(side="right")

    ttk.Label(frame, text="Actifs à inclure dans l’optimisation :").pack(pady=5)

    # Checkbox des actifs
    selected_assets = app.markowitz_config.get("assets", [])
    app.markowitz_vars = {
        asset: tk.BooleanVar(value=(asset in selected_assets))
        for asset in app.markowitz_config.get("asset_pool", [])
    }

    # ---------- Fenêtre de sélection des actifs ----------
    def open_asset_selector():
        top = tk.Toplevel(app.root)
        top.title("Sélection des actifs")
        top.geometry("900x850")

        container = ttk.Frame(top)
        container.pack(padx=20, pady=20, fill="both", expand=True)

        # ----- Données YAML -----
        ASSET_CATEGORIES = app.markowitz_config.get("asset_categories", {})
        start_dates = app.markowitz_config.get("start_dates", {})

        # ----- Grille -----
        col_count = 3
        for i in range(col_count):
            container.grid_columnconfigure(i, weight=1)

        current_col = 0
        current_row = 0

        # ----- Génération UI dynamique -----
        for category, assets in ASSET_CATEGORIES.items():

            lf = ttk.LabelFrame(container, text=category, padding=10)
            lf.grid(row=current_row, column=current_col, padx=10, pady=10, sticky="nsew")

            for sym, desc in assets.items():

                # garantir l’existence de la variable
                if sym not in app.markowitz_vars:
                    default_selected = sym in app.markowitz_config.get("assets", [])
                    app.markowitz_vars[sym] = tk.BooleanVar(value=default_selected)

                cb = ttk.Checkbutton(lf, text=f"{sym} – {desc}", variable=app.markowitz_vars[sym])
                cb.pack(anchor="w")

                # Tooltip date de début
                date_txt = start_dates.get(sym, "Inconnue")
                ToolTip(cb, f"Première date disponible : {date_txt}")

            # gestion du passage à la colonne suivante
            current_col += 1
            if current_col >= col_count:
                current_col = 0
                current_row += 1

    ttk.Button(frame, text="Choisir les actifs", command=open_asset_selector).pack(pady=4)

    # Checkbox pour le plot
    plot_var = tk.BooleanVar(value=app.plot_vars.get("Markowitz", False))
    ttk.Checkbutton(frame, text="Afficher le plot", variable=plot_var).pack()

    # ---------- Résultats Markowitz ----------
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

    # En-têtes alignés
    ttk.Label(result_frame, text="Statistique").grid(row=0, column=0, sticky="w", padx=5)
    ttk.Label(result_frame, text="Portefeuille").grid(row=0, column=1, sticky="w", padx=5)
    ttk.Label(result_frame, text="Benchmark").grid(row=0, column=2, sticky="w", padx=5)

    markowitz_labels = {}
    row = 1

    for stat, suffix in STAT_CONFIG.items():
        ttk.Label(result_frame, text=stat).grid(row=row, column=0, sticky="w", padx=5)

        portfolio_lbl = ValueLabel(result_frame, label="", suffix=suffix)
        portfolio_lbl.grid(row=row, column=1, sticky="w", padx=10)

        benchmark_lbl = ValueLabel(result_frame, label="", suffix=suffix)
        benchmark_lbl.grid(row=row, column=2, sticky="w", padx=10)

        markowitz_labels[stat] = (portfolio_lbl, benchmark_lbl)
        row += 1

    # ---------- Lancer ----------
    def launch():
        from strategies.markowitz import Markowitz
        importlib.reload(config)

        selected = [sym for sym, var in app.markowitz_vars.items() if var.get()]
        if not selected:
            messagebox.showerror("Erreur", "Veuillez sélectionner au moins un actif.")
            return

        app.markowitz_config["assets"] = selected
        save_yaml(app.markowitz_config, "config/markowitz.yaml")

        if len(selected) == 1:
            from strategies.buy_and_hold import BuyAndHold
            strategy = BuyAndHold(preset=selected[0])
        else:
            strategy = Markowitz(selected)

        all_stats = strategy.run_backtest(plot=plot_var.get())  # retourne un DataFrame

        # ---- Mise à jour UI ----
        for stat, (lbl_port, lbl_bench) in markowitz_labels.items():
            try:
                v_port  = all_stats.loc[stat, "Portefeuille"]
                v_bench = all_stats.loc[stat, "Benchmark"]
            except:
                v_port = v_bench = None

            lbl_port.set(stat, v_port)
            lbl_bench.set(stat, v_bench)


    ttk.Button(frame, text="Lancer l’optimisation", command=launch).pack(pady=10)
