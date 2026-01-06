import yfinance as yf
import pandas as pd
import os

class DataHandler:
    def __init__(self, data_path: str = None):
        self.data_path = data_path
        self._data_cache = None

    def load_data(self):
        if self._data_cache is None:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError(f"Fichier non trouvé : {self.data_path}")
            self._data_cache = pd.read_pickle(self.data_path)
        return self._data_cache

    def get(self, symbol: str, price = None, start: str = None, end: str = None) -> pd.DataFrame:
        if price == None:
            df = self.load_data()[symbol]
        else:
            df = self.load_data()[symbol][price]
        if start or end:
            df = df.loc[start:end]
        return df

    def get_multiple(self, symbols: list, price = ['Open', 'High', 'Low', 'Close', 'Volume'], start: str = None, end: str = None) -> dict:
        return {s: self.get(s, price, start, end) for s in symbols}
    
    def get_multiple_df(self, symbols: list, price, start: str = None, end: str = None) -> pd.DataFrame:
        data = self.load_data()
        adj_close_df = data.loc[start:end, pd.IndexSlice[symbols, price]]
        adj_close_df.columns = adj_close_df.columns.droplevel(1)
        
        return adj_close_df
    
    def download_from_yf(self):
        etf_tickers = [
        # ▶️ Indices US
        "SPY", "VOO", "VTI", "IVV", "QQQ", "DIA", "IWM",
        # ▶️ Marchés internationaux
        "VEA", "IEFA", "ACWI", "VT", "VXUS",
        # ▶️ Pays émergents
        "EEM", "VWO", "IEMG", "EMXC",
        # ▶️ Obligations
        "BND", "AGG", "TLT", "LQD", "HYG", "IEF", "SHY", "SGOV", "BIL", "SHV",
        # ▶️ Secteurs US
        "XLK", "XLF", "XLV", "XLY", "XLE", "XLI", "XLB", "XLU", "XLRE", "XLC",
        # ▶️ Matières premières
        "GLD", "SLV", "DBC", "USO", "DBA", "PPLT", "CPER",
        # ▶️ Immobilier
        "VNQ", "IYR", "SCHH", "REET",
        # ▶️ Stratégies / Facteurs
        "SPLV", "USMV", "MTUM", "QUAL", "VIG", "DVY", "RSP", "SPHD",
        # ▶️ Devise / hedging
        "UUP", "FXE", "FXF"
        ]
        df = yf.download(etf_tickers, period="max", auto_adjust=False, group_by='ticker')
        df.columns.names = ['Ticker', 'Price']
        df.to_pickle('etf.pkl')
        return df

