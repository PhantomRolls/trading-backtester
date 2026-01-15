import tkinter as tk
from tkinter import ttk, messagebox
from ui.widgets.value_label import ValueLabel
from ui.widgets.status_indicator import StatusIndicator

def create_iv_crush_tab(app):
    frame = ttk.Frame(app.notebook)
    app.notebook.add(frame, text="IV Crush")

    # ------------------------------------------------------
    # Helper : label texte statique
    # ------------------------------------------------------
    def dyn_label(parent, text):
        var = tk.StringVar(value=text)
        ttk.Label(parent, textvariable=var).pack(side="left", padx=5)
        return var

    # ------------------------------------------------------
    # IBKR Connection
    # ------------------------------------------------------
    conn_frame = ttk.LabelFrame(frame, text="Interactive Brokers Connection")
    conn_frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(conn_frame, text="Host:").pack(side="left")
    host_var = tk.StringVar(value="127.0.0.1")
    ttk.Entry(conn_frame, textvariable=host_var, width=12).pack(side="left", padx=5)

    ttk.Label(conn_frame, text="Port:").pack(side="left")
    port_var = tk.StringVar(value="7497")
    ttk.Entry(conn_frame, textvariable=port_var, width=6).pack(side="left", padx=5)

    def connect_ibkr():
        try:
            from strategies.iv_crush.iv_crush import OptionsStrategy
            from strategies.iv_crush.ibkr import IBKR
            app.ibkr = IBKR()
            app.ibkr.connect(host=host_var.get(), port=int(port_var.get()))
            app.iv_crush_strategy = OptionsStrategy(app.ibkr)
            print("✔ IBKR connecté")
            indicator.set_green()
        except Exception as e:
            messagebox.showerror("Erreur IBKR", str(e))
            indicator.set_red()

    ttk.Button(conn_frame, text="Connect", command=connect_ibkr).pack(side="left", padx=10)

    indicator = StatusIndicator(conn_frame, size=12)
    indicator.pack(side="left", padx=8)

    # ------------------------------------------------------
    # Earnings Setup
    # ------------------------------------------------------
    setup = ttk.LabelFrame(frame, text="Earnings Analysis Setup")
    setup.pack(fill="x", padx=10, pady=10)

    ttk.Label(setup, text="Ticker:").pack(side="left")
    ticker_var = tk.StringVar(value="NVDA")
    ttk.Entry(setup, textvariable=ticker_var, width=8).pack(side="left", padx=5)

    ttk.Label(setup, text="Earnings Date:").pack(side="left")
    date_var = tk.StringVar(value="2025-11-19")
    ttk.Entry(setup, textvariable=date_var, width=12).pack(side="left", padx=5)

    ttk.Label(setup, text="Days to Expiry:").pack(side="left")
    dte_var = tk.StringVar(value="30")
    ttk.Entry(setup, textvariable=dte_var, width=5).pack(side="left", padx=5)

    # ------------------------------------------------------
    # Current Metrics (static)
    # ------------------------------------------------------
    current = ttk.LabelFrame(frame, text="Current Metrics")
    current.pack(fill="x", padx=10, pady=5)

    lbl_stock   = dyn_label(current, "Stock Price: N/A")
    lbl_vix     = dyn_label(current, "VIX Level: N/A")
    lbl_iv      = dyn_label(current, "Current IV: N/A")

    # ------------------------------------------------------
    # IV Crush Analysis (ValueLabel)
    # ------------------------------------------------------
    iv_frame = ttk.LabelFrame(frame, text="IV Crush Analysis")
    iv_frame.pack(fill="x", padx=10, pady=5)

    lbl_pre_iv  = ValueLabel(iv_frame, "Pre-Earnings IV", color="#004CFF", suffix="%")
    lbl_post_iv = ValueLabel(iv_frame, "Post-Earnings IV", color="#004CFF", suffix="%")
    lbl_crush   = ValueLabel(iv_frame, "IV Crush", color="#004CFF", suffix="%")

    lbl_pre_iv.pack(anchor="w", padx=5)
    lbl_post_iv.pack(anchor="w", padx=5)
    lbl_crush.pack(anchor="w", padx=5)

    # ------------------------------------------------------
    # Spot Prices (ValueLabel)
    # ------------------------------------------------------
    spot_frame = ttk.LabelFrame(frame, text="Spot vs Strike Analysis")
    spot_frame.pack(fill="x", padx=10, pady=5)

    lbl_pre_close = ValueLabel(spot_frame, "Pre-Earnings Spot", suffix="$")
    lbl_post_price = ValueLabel(spot_frame, "Post-Earnings Spot", suffix="$")

    lbl_pre_close.pack(anchor="w", padx=5)
    lbl_post_price.pack(anchor="w", padx=5)

    # ------------------------------------------------------
    # Straddle Pricing (dyn_label for simple text)
    # ------------------------------------------------------
    prices_frame = ttk.LabelFrame(frame, text="ATM Straddle Pricing")
    prices_frame.pack(fill="x", padx=10, pady=5)

    lbl_pre_call = dyn_label(prices_frame, "Pre Call: N/A")
    lbl_post_call = dyn_label(prices_frame, "Post Call: N/A")
    lbl_pre_put = dyn_label(prices_frame, "Pre Put: N/A")
    lbl_post_put = dyn_label(prices_frame, "Post Put: N/A")
    lbl_pre_straddle = dyn_label(prices_frame, "Pre Straddle: N/A")
    lbl_post_straddle = dyn_label(prices_frame, "Post Straddle: N/A")

    # ------------------------------------------------------
    # P/L (ValueLabel with secondary value)
    # ------------------------------------------------------
    pnl_frame = ttk.LabelFrame(frame, text="P/L")
    pnl_frame.pack(fill="x", padx=10, pady=5)

    lbl_pnl = ValueLabel(
        pnl_frame,
        label="Straddle P/L",
        suffix="$",
        secondary_suffix="%",
    )
    lbl_pnl.pack(anchor="w", padx=5)

    # ------------------------------------------------------
    # UPDATE UI
    # ------------------------------------------------------
    def update_fields(res):

        lbl_pre_iv.set("Pre-Earnings IV", res["pre_iv"])
        lbl_post_iv.set("Post-Earnings IV", res["post_iv"])
        lbl_crush.set("IV Crush", res["post_iv"] - res["pre_iv"])

        lbl_pre_close.set("Pre-Earnings Spot", res["pre_close"])
        lbl_post_price.set("Post-Earnings Spot", res["post_price"])

        lbl_pre_call.set(f"Pre Call: {res['pre_call']}")
        lbl_post_call.set(f"Post Call: {res['post_call']}")
        lbl_pre_put.set(f"Pre Put: {res['pre_put']}")
        lbl_post_put.set(f"Post Put: {res['post_put']}")

        lbl_pre_straddle.set(f"Pre Straddle: {res['pre_straddle']}")
        lbl_post_straddle.set(f"Post Straddle: {res['post_straddle']}")

        lbl_pnl.set("Straddle P/L", res["short_straddle_pnl"], res["pnl_pct"])

    # ------------------------------------------------------
    # ANALYZE
    # ------------------------------------------------------
    def analyze():

        if not hasattr(app, "iv_crush_strategy"):
            messagebox.showerror("Erreur", "Veuillez d'abord connecter IBKR.")
            return

        dte = int(dte_var.get())

        res = app.iv_crush_strategy.compute_iv_crush(
            ticker=ticker_var.get(),
            earnings_date=date_var.get(),
            strike="ATM",
            T=dte
        )

        update_fields(res)

    ttk.Button(setup, text="Analyze IV Crush", command=analyze).pack(side="left", padx=10)

    return frame
