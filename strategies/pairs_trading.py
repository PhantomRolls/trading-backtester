import statsmodels.api as sm
from strategies.base import BaseStrategy
from utils.backtest_utils import DataHandler
import pandas as pd
from core.portfolio import Portfolio
from core.execution import OrderExecutor
from core.compute_performance import PerformanceAnalyzer
from tabulate import tabulate
from strategies.buy_and_hold import BuyAndHold
import sys 
import os
import json
import numpy as np
from utils.options_utils import load_yaml

class PairsTradingStrategy(BaseStrategy):
    def __init__(self, pair):
        super().__init__()
        self.name = "Pairs Trading Strategy"
        self.config = load_yaml("config/pairs_trading.yaml")
        self.pair   = pair
        self.window  = self.config["window"]
        self.z_enter = self.config["z_enter"]
        self.z_exit  = self.config["z_exit"]
        self.data_handler =  DataHandler(data_path = "data/s&p500.pkl")
    
    def generate_signals(self):     
        s1, s2 = self.pair
        df = self.compute_z_score()
        z = df['z_score']
        short = {}
        long = {}
        exit = {}
        in_position = False
        for current_date in z.index:
            if not in_position:
                if z.loc[current_date] > self.z_enter:
                    short[current_date] = True
                    long[current_date] = False
                    exit[current_date] = False
                    in_position = True
                elif z.loc[current_date] < -self.z_enter:
                    short[current_date] = False
                    long[current_date] = True
                    exit[current_date] = False
                    in_position = True 
                else:
                    short[current_date] = False
                    long[current_date] = False
                    exit[current_date] = False
                    in_position = False 
            else:
                if abs(z.loc[current_date]) < self.z_exit: 
                    short[current_date] = False
                    long[current_date] = False
                    exit[current_date] = True
                    in_position = False
                else:
                    short[current_date] = False
                    long[current_date] = False
                    exit[current_date] = False
                    in_position = True   
        signals = pd.DataFrame({
        "short": pd.Series(short),
        "long": pd.Series(long),
        "exit": pd.Series(exit),
        })     
        df = df.join(signals, how='left')
        data = self.data_handler.get_multiple([s1, s2], price='Close')
        df1, df2 = data[s1], data[s2]
        df["close_1"] = df1.loc[df.index]
        df["close_2"] = df2.loc[df.index]
        df.to_csv(f'output/{self.name}/{s1}_{s2}_signals.csv')
        return df


    def compute_spread(self):
        s1, s2 = self.pair
        spread = {}
        betas = {}
        pre_start = self.start - pd.Timedelta(days=2*365)
        df = self.data_handler.get_multiple([s1, s2], start=pre_start, end=self.end)
        df1, df2 = df[s1], df[s2]
        dates = df1.index[self.window-1:]
        for i, current_date in enumerate(dates, start=self.window):
            close1 = df1['Close'].iloc[i - self.window : i]
            close2 = df2['Close'].iloc[i - self.window : i]   
            X_reg   = sm.add_constant(close1)
            model = sm.OLS(close2, X_reg).fit()
            beta = model.params.iloc[1]
            alpha = model.params.iloc[0]
            spread_val = close2.iloc[-1] - (alpha + beta * close1.iloc[-1])
            spread[current_date] = spread_val
            betas[current_date] = beta
        df_result = pd.DataFrame({
        "spread": pd.Series(spread),
        "beta": pd.Series(betas)
        })
        df_result = df_result
        return df_result
    
    def compute_z_score(self):
        df = self.compute_spread()
        df["z_score"] = (df["spread"] - df["spread"].rolling(self.window).mean()) / df["spread"].rolling(self.window).std()
        df.dropna(inplace=True)
        df = df.loc[self.start:]
        return df
    
    def generate_orders(self):
        s1, s2 = self.pair
        df = self.generate_signals()
        orders = {}  
        dates = df.index.to_list()
        for i in range(len(dates)-1):
            date = dates[i]
            next_date = dates[i+1]
            row = df.loc[date]
            day_orders = []
            beta = row['beta']
            close1 = row['close_1']
            close2 = row['close_2']
            n_spread = self.capital/(close2+abs(beta)*close1)
            exposure1 = n_spread * abs(beta) * close1
            exposure2= n_spread * close2
            qty1 = int(exposure1 / close1)
            qty2 = int(exposure2 / close2)
            if row["long"]:
                day_orders.append({'symbol': s1, 'action': 'sell',  'size': qty1})
                day_orders.append({'symbol': s2, 'action': 'buy', 'size': qty2})
            elif row["short"]:
                day_orders.append({'symbol': s1, 'action': 'buy', 'size': qty1})
                day_orders.append({'symbol': s2, 'action': 'sell',  'size': qty2})
            elif row["exit"]:
                day_orders.append({'symbol': s1, 'action': 'exit', 'size': qty1})
                day_orders.append({'symbol': s2, 'action': 'exit', 'size': qty2})
            if day_orders:
                orders[next_date] = day_orders
        return orders
    
    
    def run_backtest(self, plot=False, benchmark=True):
        executor = OrderExecutor(data_handler=self.data_handler)
        signals = self.generate_signals()
        orders = self.generate_orders()
        portfolio = Portfolio(symbols=self.pair, data_handler=self.data_handler, strategy=self)
        date_range = pd.date_range(start=self.start, end=self.end)
        executed_orders = {}
        for date in date_range:
            if date not in signals.index:
                continue
            orders_today = orders.get(date, [])
            executed = executor.execute(orders_today, date, order_time='Open')
            executed_orders[date] = executed[date]
            portfolio.update(date, executed)
        portfolio_df = portfolio.get_history()
        analyzer = PerformanceAnalyzer(self.data_handler, portfolio_df, orders, strategy=self)
        stats = analyzer.compute_statistics()
        stats_df = pd.DataFrame.from_dict(stats, orient='index', columns=["Portefeuille"])
        benchmark_portfolio_df, benchmark_stats_df = self.run_benchmark(preset='SPY')
        all_stats = pd.concat([stats_df, benchmark_stats_df], axis=1)
        all_stats.index.name = "Statistique"
        table = tabulate(all_stats, headers="keys", tablefmt="fancy_grid")
        self.show_orders(executed_orders)
        print(table)
        if plot:
            analyzer.plot(benchmark_portfolio_df['value'] if benchmark else None)
        return all_stats

        
        
    def run_benchmark(self, preset='SPY'):
        strategy = BuyAndHold(preset=preset)
        return strategy.run_benchmark(preset=preset)
        
     
