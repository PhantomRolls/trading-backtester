import config
from strategies.base import BaseStrategy
from utils.backtest_utils import DataHandler
import datetime
import pandas as pd
import numpy as np
from core.execution import OrderExecutor
from core.compute_performance import PerformanceAnalyzer
from core.portfolio import Portfolio
from tabulate import tabulate
from utils.options_utils import load_yaml

class BuyAndHold(BaseStrategy):
    def __init__(self, preset):
        super().__init__()
        self.name = "Buy and Hold Strategy"
        self.config = load_yaml('config/buy_and_hold.yaml')
        self.preset = preset
        self.reallocation_window = self.config["reallocation_window"]
        self.reallocation_amount = self.config["reallocation_amount"]
        self.data_handler = DataHandler(data_path = "data/etf.pkl")
        self.assets_dict = self.config["portfolio_presets"].get(self.preset,{self.preset: 1})
        self.dates = self.data_handler.get(self.assets_dict.keys(), start=self.start, end=self.end).index
    
    
    def generate_orders(self):
        orders = {}
        day_orders = [] 
        first_date = self.dates[self.dates >= self.start][0]
        mask = [i % self.reallocation_window == 0 and i != 0 for i in range(len(self.dates))]
        allocation_dates = self.dates[mask]
        for asset, weight in self.assets_dict.items():
            if weight != 0:
                price = self.data_handler.get(asset, price='Adj Close').loc[first_date]
                day_orders.append({'symbol': asset, 'action': 'buy', 'size': weight*self.capital/price})
        orders[first_date] = day_orders
        if self.reallocation_amount != 0:
            for date in allocation_dates:
                day_orders = [] 
                for asset, weight in self.assets_dict.items():
                    if weight != 0:
                            price = self.data_handler.get(asset, price='Adj Close').loc[date]
                            day_orders.append({'symbol': asset, 'action': 'deposit', 'size': weight*self.reallocation_amount/price})
                orders[date] = day_orders
        return orders
     
    def run_benchmark(self, preset):
        self.assets_dict = self.config["portfolio_presets"].get(preset,{preset: 1})
        executor = OrderExecutor(data_handler=self.data_handler)
        self.orders = self.generate_orders()
        active_symbols = list(self.assets_dict.keys())
        portfolio = Portfolio(symbols=active_symbols, data_handler=self.data_handler, strategy=self)
        date_range = pd.date_range(start=self.start, end=self.end)
        total_fees = 0
        self.executed_orders = {}
        for date in date_range:
            if date not in self.dates:
                continue
            orders_today = self.orders.get(date, [])  
            executed = executor.execute(orders_today, date, order_time='Adj Close')
            total_fees += sum(order.get("fee", 0.0) for order in executed[date])
            self.executed_orders[date] = executed[date]
            portfolio.update(date, executed)
        portfolio_df = portfolio.get_history()
        self.analyzer = PerformanceAnalyzer(self.data_handler, portfolio_df, self.orders, strategy=self)
        if self.reallocation_amount == 0:
            stats = self.analyzer.compute_statistics(total_fees)
        else:
            stats = self.analyzer.compute_statistics_with_flows(self.reallocation_amount) 
        stats_df = pd.DataFrame.from_dict(stats, orient='index', columns=["Portefeuille"] if not preset=='SPY' else ['Benchmark'])
        return portfolio_df, stats_df
        
    def run_backtest(self, plot=False):
        benchmark_portfolio_df, benchmark_stats_df = self.run_benchmark('SPY')
        portfolio_df, stats_df = self.run_benchmark(preset=self.preset)
        all_stats = pd.concat([stats_df, benchmark_stats_df], axis=1)
        all_stats.index.name = "Statistique"
        table = tabulate(all_stats, headers="keys", tablefmt="fancy_grid")
        self.show_orders(self.executed_orders)
        print(table)
        if plot:
            self.analyzer.plot(benchmark=benchmark_portfolio_df['value'])
            from utils.excel_export import export_backtest_to_excel
            ohlc_dict = self.data_handler.get_multiple(self.assets_dict.keys())
            export_backtest_to_excel(
                filepath=f"output/{self.name}/Backtest_Report.xlsx",
                summary_stats=all_stats,
                equity_df=portfolio_df,
                weights_df=pd.DataFrame.from_dict(self.assets_dict, orient='index', columns=["Weights"]),
                ohlc_data=ohlc_dict,
                trades_df=None,
                frontier_df=getattr(self, "frontier_df", None)
            )

        return all_stats
            
  
