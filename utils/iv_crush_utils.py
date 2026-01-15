import yfinance as yf
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box

def last_before(df, target_date):
    """
    Retourne la dernière date disponible dans df.index avant target_date.
    """
    dates = df.index[df.index < target_date]
    if len(dates) == 0:
        return None
    return dates.max()

def first_after(df, target_date):
    """
    Retourne la première date disponible dans df.index après target_date.
    """
    dates = df.index[df.index > target_date]
    if len(dates) == 0:
        return None
    return dates.min()


def load_earnings_events():
    tickers = [
        "AAPL", "NVDA", "AMZN", "TSLA", "META",
        "MSFT", "GOOG", "AMD", "NFLX", "JPM"
    ]

    all_rows = []

    for t in tickers:
        print(f"Downloading earnings dates for {t}...")
        stock = yf.Ticker(t)

        try:
            df = stock.earnings_dates  # Yahoo Finance earnings history
            df = df.reset_index()      # Moves index to a column named "index"

            # RENAME "index" -> "earnings_date"
            df.rename(columns={"index": "earnings_date"}, inplace=True)

            # ADD a ticker column
            df["ticker"] = t

            all_rows.append(df)
        except Exception as e:
            print(f"Error for {t}: {e}")

    # Concatenate all dataframes
    full_df = pd.concat(all_rows, ignore_index=True)


    # rename column
    full_df.rename(columns={"Earnings Date": "earnings_date"}, inplace=True)

    # convert format
    full_df["earnings_date"] = (
        pd.to_datetime(full_df["earnings_date"])
        .dt.tz_convert(None)              # remove timezone like -05:00
        .dt.strftime("%Y-%m-%d")
    )

    # Save CSV
    full_df.to_csv("earnings_events_real.csv", index=False)

    print("\n✓ Fichier créé : earnings_events_real.csv")
    
def print_iv_report(res):
    console = Console()

    # Color helpers
    def money(x):
        return f"[green]${x:.2f}[/green]" if x >= 0 else f"[red]${x:.2f}[/red]"

    def pct(x):
        return f"[green]{x:+.1f}%[/green]" if x >= 0 else f"[red]{x:+.1f}%[/red]"

    def num(x):
        return f"[green]{x:+.2f}[/green]" if x >= 0 else f"[red]{x:+.2f}[/red]"

    # Compute changes
    stock_change = res["post_price"] - res["pre_close"]
    stock_change_pct = stock_change / res["pre_close"] * 100

    iv_crush = res["post_iv"] - res["pre_iv"]
    iv_crush_pct = iv_crush / res["pre_iv"] * 100

    call_change = res["post_call"] - res["pre_call"]
    call_change_pct = call_change / res["pre_call"] * 100

    put_change = res["post_put"] - res["pre_put"]
    put_change_pct = (put_change / res["pre_put"] * 100) if res["pre_put"] != 0 else 0

    straddle_change = res["post_straddle"] - res["pre_straddle"]
    straddle_change_pct = straddle_change / res["pre_straddle"] * 100

    pnl = res["short_straddle_pnl"]
    pnl_pct = pnl / res["pre_straddle"] * 100

    # Build compact table
    table = Table(
        title="📊 IV Crush Analysis — Compact Report",
        box=box.MINIMAL_DOUBLE_HEAD,
        show_lines=False,
        expand=False
    )
    table.add_column("Category", style="bold cyan", no_wrap=True)
    table.add_column("Summary", style="white")

    # --- STOCK ---
    table.add_row(
        "Stock",
        (
            f"Pre: {money(res['pre_close'])}   "
            f"Post: {money(res['post_price'])}   "
            f"Move: {num(stock_change)} ({pct(stock_change_pct)})"
        )
    )

    # --- IV ---
    table.add_row(
        "Implied Vol",
        (
            f"Pre: {res['pre_iv']:.2f}%   "
            f"Post: {res['post_iv']:.2f}%   "
            f"Crush: {num(iv_crush)} ({pct(iv_crush_pct)})"
        )
    )

    # --- CALL ---
    table.add_row(
        "ATM Call",
        (
            f"Pre: {money(res['pre_call'])}   "
            f"Post: {money(res['post_call'])}   "
            f"Δ: {num(call_change)} ({pct(call_change_pct)})"
        )
    )

    # --- PUT ---
    table.add_row(
        "ATM Put",
        (
            f"Pre: {money(res['pre_put'])}   "
            f"Post: {money(res['post_put'])}   "
            f"Δ: {num(put_change)} ({pct(put_change_pct)})"
        )
    )

    # --- STRADDLE ---
    table.add_row(
        "ATM Straddle",
        (
            f"Pre: {money(res['pre_straddle'])}   "
            f"Post: {money(res['post_straddle'])}   "
            f"Δ: {num(straddle_change)} ({pct(straddle_change_pct)})"
        )
    )

    # --- PNL ---
    table.add_row(
        "Short PnL",
        f"{num(pnl)} ({pct(pnl_pct)})"
    )

    console.print(table)

