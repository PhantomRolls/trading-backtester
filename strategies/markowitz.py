from strategies.base import BaseStrategy
from utils.backtest_utils import DataHandler
import pandas as pd
import numpy as np
import cvxpy as cp
from sklearn.covariance import LedoitWolf
from core.portfolio import Portfolio
from core.execution import OrderExecutor
from core.compute_performance import PerformanceAnalyzer
from tabulate import tabulate
from strategies.buy_and_hold import BuyAndHold
from tqdm import tqdm
import sys 
import tracemalloc
from utils.options_utils import load_yaml

class Markowitz(BaseStrategy):
    def __init__(self, assets):
        super().__init__()
        self.config = load_yaml('config/markowitz.yaml')
        self.name = "Markowitz Strategy"
        self.allocation_window = self.config["rebalance_window"]
        self.lookback_window = self.config["lookback_window"]
        self.risk_free_rate = self.config["risk_free_rate"]
        self.diversification = self.config["diversification"]
        self.data_handler = DataHandler(data_path = "data/etf.pkl")
        self.dates = self.data_handler.get(assets[0], start=self.start, end=self.end).index
        self.assets = assets
        

    
    def generate_orders(self, plot=False):
        orders = {} 
        gamma_series = {}
        mask = [i % self.allocation_window == 0 for i in range(len(self.dates))]
        reallocation_dates = self.dates[mask]
        pre_start = self.start - pd.Timedelta(days=self.lookback_window*2)   
        prices_df = self.data_handler.get_multiple_df(list(self.assets), price='Adj Close', start=pre_start)    
        prices_df_open = self.data_handler.get_multiple_df(list(self.assets), price='Open', start=pre_start)  
        weights_hist = [[0]*len(self.assets)]
        portfolio = Portfolio(symbols=self.assets, data_handler=self.data_handler, strategy=self)
        executor = OrderExecutor(data_handler=self.data_handler)
        total_fees = 0
        executed_orders = {}
        for i, date in enumerate(tqdm(self.dates[:-1], desc="Backtesting")):
            next_date = self.dates[i+1]
            day_orders = []
            idx = prices_df[self.assets[0]].index.get_loc(date)
            past_date = prices_df[self.assets[0]].index[idx - self.lookback_window]
            if date in reallocation_dates:
                valid_dates = prices_df.index[prices_df.index <= date]
                last_30_days = valid_dates[-self.lookback_window:]
                data = prices_df.loc[last_30_days]
                prev_weights = weights_hist[-1]
                weights, sharpe, gamma = self.optimize_sharpe(data)
                gamma_series[date] = gamma
                delta_weights = np.round(weights - prev_weights,2)
                for j, asset in enumerate(self.assets):
                    price = prices_df[asset].loc[date]
                    price_open = prices_df_open[asset].loc[next_date]
                    if delta_weights[j] < 0:
                        action = 'sell'
                        day_orders.append({'symbol': asset, 'action': action, 'size': delta_weights[j]*portfolio.value/price})
                    else:
                        action = 'buy'
                        day_orders.append({'symbol': asset, 'action': action, 'size': delta_weights[j]*portfolio.value/price})
                orders[next_date] = day_orders  
                weights_hist.append(weights) 
            day_orders = orders.get(date,[])
            executed = executor.execute(day_orders, date, order_time='Adj Close') 
            total_fees += sum(order.get("fee", 0.0) for order in executed[date])
            executed_orders[date] = executed[date]      
            portfolio.update(date, executed)           
        portfolio_df = portfolio.get_history()
        analyzer = PerformanceAnalyzer(self.data_handler, portfolio_df, orders, strategy=self)
        stats = analyzer.compute_statistics(total_fees)
        stats_df = pd.DataFrame.from_dict(stats, orient='index', columns=["Portefeuille"])
        benchmark_portfolio_df, benchmark_stats_df = self.run_benchmark(preset='SPY')
        all_stats = pd.concat([stats_df, benchmark_stats_df], axis=1)
        all_stats.index.name = "Statistique"
        table = tabulate(all_stats, headers="keys", tablefmt="fancy_grid")
        self.show_orders(executed_orders)
        print(table)
        if plot:
            analyzer.plot(benchmark_portfolio_df['value'])
        return all_stats
        
    def run_backtest(self, plot=False):
        return self.generate_orders(plot=plot)
        
     
    def markowitz_optimize(self, gamma, mean_returns, cov_matrix):
        n = len(mean_returns)
        w = cp.Variable(n)
        
        global_mean = mean_returns.mean()
        shrinkage_level = 0.5
        shrunk_returns = (1 - shrinkage_level) * mean_returns + shrinkage_level * global_mean
        expected_returns = w @ shrunk_returns
        variance = cp.quad_form(w, cov_matrix)
        objective = cp.Minimize(variance - gamma * expected_returns)
        
        div_proxy = n * cp.sum_squares(w)
        constraints = [
            cp.sum(w) == 1,
            w >= 0,
            div_proxy <= 1/self.diversification
        ]
        
        problem = cp.Problem(objective, constraints)
        problem.solve()
        weights = w.value
        return weights
    
    def optimize_sharpe(self, data):
        returns = data.pct_change().dropna()
        lw = LedoitWolf().fit(returns.values)
        cov_matrix = lw.covariance_ * 252
        mean_returns = returns.mean().values * 252
        gamma_list = np.linspace(0,1,100)
        best_sharpe = -np.inf
        best_weights = None
        best_gamma = None
        for gamma in gamma_list:
            weights = self.markowitz_optimize(gamma, mean_returns, cov_matrix)
            port_return = np.dot(weights, mean_returns)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else -np.inf
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = weights
                best_gamma = gamma
        return best_weights, best_sharpe, best_gamma
        

    def run_benchmark(self, preset='SPY'):
        strategy = BuyAndHold(preset=preset)
        return strategy.run_benchmark(preset=preset)
            
