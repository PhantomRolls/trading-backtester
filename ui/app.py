# ui/app.py
from tkinter import ttk
from ui.tabs.param_tab import create_param_tab
from ui.tabs.buy_hold_tab import create_buy_hold_tab
from ui.tabs.pairs_trading_tab import create_pairs_trading_tab
from ui.tabs.markowitz_tab import create_markowitz_tab
from ui.tabs.iv_crush_tab import create_iv_crush_tab
import tkinter.scrolledtext as scrolledtext
from utils.options_utils import load_yaml, save_yaml


class StrategyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Backtest")

        # Load configs before creating UI
        self.general_config = load_yaml("config/general.yaml")
        self.buy_and_hold_config = load_yaml("config/buy_and_hold.yaml")
        self.pairs_trading_config = load_yaml("config/pairs_trading.yaml")
        self.markowitz_config = load_yaml("config/markowitz.yaml")
        self.asset_categories = load_yaml("config/asset_categories.yaml")
        self.plot_vars = {}

        # Notebook UI
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Create the tabs AFTER configs are loaded
        create_param_tab(self)
        create_buy_hold_tab(self)
        create_pairs_trading_tab(self)
        create_markowitz_tab(self)
        create_iv_crush_tab(self)


        # # Create console at bottom
        # self.console_output = scrolledtext.ScrolledText(
        #     self.root, height=12, state="disabled", wrap="word"
        # )
        # self.console_output.pack(fill="x", padx=5, pady=5)

        # # Redirect print() to console widget
        # import sys
        # sys.stdout = TextRedirector(self.console_output, "stdout")
        # sys.stderr = TextRedirector(self.console_output, "stderr")
        # # ----------------------------------------

