import pandas as pd    
from strategies.iv_crush.option_pricing import call, put, straddle
from strategies.iv_crush.ibkr import IBKR
from datetime import datetime, timedelta
from utils.iv_crush_utils import last_before, first_after

class OptionsStrategy():
    def __init__(self, ibkr: IBKR):
        self.ib = ibkr
        self.historical_data = {}
    
    def get_historical_data(self, ticker, end, barSizeSetting, duration):
        if type(end) == str:
            end = datetime.strptime(end, "%Y-%m-%d") 
        self.historical_data[ticker] = self.ib.get_stock_history(ticker=ticker, end=end, barSizeSetting=barSizeSetting, duration=duration)
        self.historical_data["VIX"] = self.ib.get_vix_history(end=end, duration=duration)
        self.historical_data[f"{ticker}_iv"] = self.ib.get_iv_history(ticker=ticker, end=end, barSizeSetting=barSizeSetting, duration=duration)
        return self.historical_data
    
    def compute_iv_crush(self, ticker, earnings_date, strike, T=30):
        if type(earnings_date) == str:
            earnings_date = datetime.strptime(earnings_date, "%Y-%m-%d").date()
        end = earnings_date + timedelta(days=6)
        self.get_historical_data(ticker, end=end, barSizeSetting="1 day", duration="7 D")
        prev_date = last_before(self.historical_data[f"{ticker}_iv"], earnings_date)
        post_date = first_after(self.historical_data[f"{ticker}_iv"], earnings_date)
        
        pre_close = self.historical_data[ticker].loc[earnings_date, "close"]
        post_open = self.historical_data[ticker].loc[post_date, "open"]
        post_close = self.historical_data[ticker].loc[post_date, "close"]
        post_price = ( post_open + post_close ) / 2

        pre_iv = self.historical_data[f"{ticker}_iv"].loc[prev_date, "close"]
        post_iv = self.historical_data[f"{ticker}_iv"].loc[post_date, "close"]
        
        if strike == "ATM":
            strike = pre_close
            
        pre_straddle = straddle(S=pre_close, K=strike, tau=T/365, sigma=pre_iv, r=0.04)
        post_straddle = straddle(S=post_price, K=strike, tau=T/365, sigma=post_iv, r=0.04)
        
        pre_call = call(S=pre_close, K=strike, tau=T/365, sigma=pre_iv, r=0.04)
        post_call = call(S=post_price, K=strike, tau=T/365, sigma=post_iv, r=0.04)
        pre_put = put(S=pre_close, K=strike, tau=T/365, sigma=pre_iv, r=0.04)
        post_put = put(S=post_price, K=strike, tau=T/365, sigma=post_iv, r=0.04)
        

        short_straddle_pnl = pre_straddle - post_straddle
        pnl_pct = short_straddle_pnl / pre_straddle
        
        result = {
            "pre_close": pre_close,
            "post_price": post_price,
            "pre_iv": pre_iv*100,
            "post_iv": post_iv*100,
            "pre_call": pre_call,
            "post_call": post_call,
            "pre_put": pre_put,
            "post_put": post_put,
            "pre_straddle": pre_straddle,
            "post_straddle": post_straddle,
            "short_straddle_pnl": short_straddle_pnl,
            "pnl_pct": pnl_pct
        }
        
        return result
        
        
        


