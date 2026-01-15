import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from strategies.base import BaseStrategy

class PerformanceAnalyzer(BaseStrategy):
    def __init__(self, data_handler, portfolio_df: pd.DataFrame, orders: dict, strategy):
        super().__init__()
        self.risk_free_rate = 0
        self.df = portfolio_df.copy()
        self.stats = {}
        self.data_handler = data_handler
        self.orders = orders
        self.strategy = strategy
        self._prepare()

    def _prepare(self):
        self.df = self.df.sort_index()
        self.df["returns"] = self.df["value"].pct_change().dropna()
        self.df["cumulative_return"] = (1 + self.df["returns"]).cumprod()
        self.df["cum_max"] = self.df["value"].cummax()
        self.df["drawdown"] = self.df["value"] / self.df["cum_max"] - 1


    def compute_statistics(self, fees=0):
        total_return = self.df["cumulative_return"].iloc[-1] - 1
        annualized_return = (1 + total_return) ** (252 / len(self.df)) - 1
        annualized_volatility = self.df["returns"].std() * np.sqrt(252)
        sharpe = (annualized_return - self.risk_free_rate) / annualized_volatility if annualized_volatility > 0 else np.nan
        max_drawdown = self.df["drawdown"].min()
        diversification = self.diversification_effective()
        total_fees = self.compute_fees(fees)
        self.stats = {
            "Annualized Return (%)": round(annualized_return * 100, 2),
            "Annualized Volatility (%)": round(annualized_volatility * 100, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Max Drawdown (%)": round(max_drawdown * 100, 2),
            "Total Return (%)": round(total_return * 100, 2),
            "Frais (%)": round(total_fees, 2),
            "Diversification": round(diversification, 2),
        }
        return self.stats

    def diversification_effective(self):
        df = self.df.copy()
        asset_symbols = [
            col for col in df.columns
            if col.isalpha() and col.upper() == col and not (df[col] == 0).all()
        ]
        gross_value = df[asset_symbols].abs().sum(axis=1)
        df_weights = df[asset_symbols].abs().div(gross_value, axis=0).dropna()
        num = (df_weights ** 2).sum(axis=1)
        den = (df_weights.sum(axis=1)) ** 2
        h_series = num / den
        n = len(asset_symbols)
        return (1 / (n * h_series)).mean()
    
    def compute_fees(self, fees):
        df = self.df.copy()
        net_value = df["value"].iloc[-1]
        total_fees = (fees / (net_value + fees))*100
        return total_fees
        
        

    def compute_statistics_with_flows(self, reallocation_amount):
        total_value = self.df["value"].iloc[-1]
        end_date = self.df.index[-1]
        cash_flows = []
        for date in sorted(self.orders.keys()):
            capital = self.capital if date == min(self.orders.keys()) else reallocation_amount
            cash_flows.append((date, -capital))
        cash_flows.append((end_date, total_value))
        irr = self.xirr(cash_flows)
        total_invested = sum(-cf[1] for cf in cash_flows if cf[1] < 0)
        interests = total_value - total_invested
        self.stats = {
            "Money-Weighted Return (IRR %)": round(irr * 100, 2),
            "Total Capital Invested (€)": round(total_invested,2),
            "Portfolio Final Value (€)": round(total_value, 2),
            "Interests (€)": round(interests,2),
            "Total Return (%)": round(total_value/total_invested*100-100, 2),
        }
        return self.stats

    def xirr(self, cash_flows):
        def xnpv(rate):
            return sum([cf / (1 + rate) ** ((d - cash_flows[0][0]).days / 365) for d, cf in cash_flows])
        def xirr_newton():
            rate = 0.1
            for _ in range(100):
                f = xnpv(rate)
                f_prime = sum([
                    - (d - cash_flows[0][0]).days / 365 * cf / (1 + rate) ** (((d - cash_flows[0][0]).days / 365) + 1)
                    for d, cf in cash_flows
                ])
                rate -= f / f_prime
                if abs(f) < 1e-6:
                    return rate
            return rate
        return xirr_newton()
    
    def get_dataframe(self):
        return self.df
    
    
    def plot(self, benchmark=None):
        df = self.df.copy()
        asset_symbols = [
            col for col in df.columns
            if col.isalpha() and col.upper() == col and not (df[col] == 0).all()
        ]
        n_assets = len(asset_symbols)
        total_rows = 2 + n_assets
        if n_assets > 0:
            asset_height = 0.6
            row_heights = [0.6, 0.6] + [asset_height] * n_assets
        else:
            row_heights = [0.6, 0.6, 0.6]
        titles = (
            ["Valeur du portefeuille",
            "Poids des actifs (%)"] +
            [f"{sym} - Prix en chandeliers" for sym in asset_symbols]
        )
        specs = [[{}] for _ in range(total_rows)]
        for j in range(2, total_rows):
            specs[j] = [{'secondary_y': True}]
        portfolio = df["value"]
        fig = make_subplots(
            rows=total_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=titles,
            specs=specs
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=portfolio,
                name="Portfolio ($)",
                line=dict(color='green')
            ), row=1, col=1
        )
        if benchmark is not None:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=benchmark,
                    name="Benchmark ($)",
                    line=dict(color='navy')
                ), row=1, col=1
            )
            self.add_performance_fill(
                fig=fig,
                x=df.index,
                portfolio=portfolio,
                benchmark=benchmark,
                row=1,
                col=1
            )
        gross_value = df[asset_symbols].abs().sum(axis=1)
        df_weights = df[asset_symbols].abs().div(gross_value, axis=0)
        for sym in asset_symbols:
            fig.add_trace(
                go.Scatter(
                    x=df_weights.index,
                    y=df_weights[sym] * 100,
                    mode='lines',
                    stackgroup='one',
                    line_shape="hv",
                    name=sym
                ), row=2, col=1
            )

        for i, sym in enumerate(asset_symbols):
            ohlc = self.data_handler.get(sym).reindex(df.index)
            fig.add_trace(
                go.Candlestick(
                    x=ohlc.index,
                    open=ohlc['Open'], high=ohlc['High'],
                    low=ohlc['Low'], close=ohlc['Close'],
                    name=sym,
                    increasing_line_color='grey',
                    decreasing_line_color='red',
                    showlegend=False
                ), row=3+i, col=1, secondary_y=False
            )
            if 'Volume' in ohlc.columns:
                fig.add_trace(
                    go.Bar(
                        x=ohlc.index,
                        y=ohlc['Volume'],
                        name=f"{sym} - Volume",
                        opacity=0.3,
                        marker_color='lightblue',
                        showlegend=False
                    ), row=3+i, col=1, secondary_y=True
                )
            fig.update_xaxes(rangeslider_visible=False, row=3+i, col=1)
            fig.update_yaxes(
                range=[0, ohlc['Volume'].max() * 2],
                row=3+i, col=1,
                secondary_y=True
            )

            for timestamp, order_list in self.orders.items():
                for order in order_list:
                    if order["symbol"] != sym:
                        continue
                    base_price = ohlc.loc[timestamp, "Close"]
                    if order["action"] == "buy":
                        marker = dict(symbol="triangle-up", color="green", size=12)
                        price = base_price * 1
                    elif order["action"] == "sell":
                        marker = dict(symbol="triangle-down", color="red", size=12)
                        price = base_price * 1
                    elif order["action"] == "exit":
                        marker = dict(symbol="diamond", color="purple", size=10)
                        price = base_price
                    elif order["action"] == "deposit":
                        marker = dict(symbol="diamond", color="blue", size=10)
                        price = base_price
                    else:
                        continue
                    fig.add_trace(
                        go.Scatter(
                            x=[timestamp],
                            y=[price],
                            mode="markers",
                            marker=marker,
                            name=f"{sym} - {order['action']}",
                            showlegend=False
                        ), row=3+i, col=1
                    )

        fig.update_layout(
            height=800 + 250 * n_assets,
            template="plotly_dark",
            title_text="Performance complète du portefeuille",
            hovermode="x unified",
            margin=dict(t=80, b=40)
        )

        for r in range(1, total_rows):
            fig.update_xaxes(showticklabels=False, row=r, col=1)

        fig.write_html(f"output/{self.strategy.name}/portfolio_plot.html", auto_open=True)


    def add_performance_fill(self, fig, x, portfolio, benchmark, row, col):
        portfolio, benchmark = portfolio.align(benchmark, join='inner')
        mask = portfolio > benchmark
        segments = (mask != mask.shift()).cumsum()

        for seg_id in segments.unique():
            segment_mask = segments == seg_id
            p_seg = portfolio[segment_mask]
            b_seg = benchmark[segment_mask]
            x_seg = x[segment_mask]

            if len(p_seg) < 2:
                continue  # skip too short

            color = 'rgba(0,255,0,0.3)' if (p_seg > b_seg).iloc[0] else 'rgba(255,0,0,0.3)'

            # Upper curve
            fig.add_trace(go.Scatter(
                x=x_seg,
                y=p_seg,
                mode='lines',
                line=dict(width=0),
                showlegend=False
            ), row=row, col=col)

            # Lower curve + fill
            fig.add_trace(go.Scatter(
                x=x_seg,
                y=b_seg,
                mode='lines',
                fill='tonexty',
                fillcolor=color,
                line=dict(width=0),
                showlegend=False
            ), row=row, col=col)
