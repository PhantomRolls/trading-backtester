from abc import ABC, abstractmethod
import pandas as pd
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
import sys
import os
import json
from utils.options_utils import load_yaml

class BaseStrategy(ABC):
    def __init__(self):
        self.general_config = load_yaml('config/general.yaml')
        self.capital = self.general_config["capital"]
        self.start = pd.Timestamp(self.general_config["start_date"])
        self.end = pd.Timestamp(self.general_config["end_date"])


    def load_json_config(self, filename):
        path = os.path.join("config", filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def display_orders_colors(self, orders_dict):
        # Envoie le rendu Rich directement dans le vrai terminal
        console = Console(file=sys.__stdout__, force_terminal=True, color_system="truecolor")

        table = Table(title="📦 Ordres", title_style="bold cyan")
        table.add_column("Date", style="yellow")
        table.add_column("Symbole", style="green")
        table.add_column("Action", style="bold magenta")
        table.add_column("Quantité", justify="right", style="bright_blue")
        table.add_column("Prix", justify="right", style="cyan")
        table.add_column("Frais", justify="right", style="red")

        for date, day_orders in sorted(orders_dict.items()):
            first_row = True
            for order in day_orders:
                action = order['action'].lower()
                if action == "sell":
                    action_style = f"[bold red]{order['action']}[/]"
                elif action == "exit":
                    action_style = f"[bold yellow]{order['action']}[/]"
                else:
                    action_style = f"[bold green]{order['action']}[/]"
                table.add_row(
                    date.strftime("%Y-%m-%d") if first_row else "",
                    order['symbol'],
                    action_style,
                    str(order['size']),
                    str(order['price']),
                    str(order['fee']),
                )
                first_row = False

        console.print(table)

        
    def show_orders(self, executed_orders):
        if sys.__stdout__.isatty():
            self.display_orders_colors(executed_orders)
            return

        
    




