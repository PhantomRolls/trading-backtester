# modules/ibkr.py
from ib_insync import *
from datetime import datetime
from datetime import timedelta, datetime

class IBKR:
    def __init__(self):
        self.ib = None
        self.is_connected = False

    # ------------------ Connexion ----------------------
    def connect(self, host="127.0.0.1", port=7497, client_id=1):
        try:
            self.ib = IB()
            self.ib.connect(host, port, clientId=client_id)

            if self.ib.isConnected():
                self.is_connected = True
                print("Connexion IBKR établie.")
                return True
            else:
                print("Échec de la connexion IBKR.")
                self.is_connected = False
                return False

        except Exception as e:
            print("Erreur IBKR :", e)
            self.ib = None
            self.is_connected = False
            return False

    # ------------------ Check ----------------------
    def _ensure(self):
        if not self.is_connected:
            raise RuntimeError("IBKR non connecté.")

    # ------------------ Data ----------------------
    def get_stock_history(self, ticker, end, barSizeSetting="1 day", duration="5 D"):
        if type(end) == str:
            end = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=4)
        self._ensure()
        contract = Stock(ticker, "SMART", "USD")

        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime=end,
            durationStr=duration,
            barSizeSetting=barSizeSetting,
            whatToShow="TRADES",
            useRTH=True
        )

        df = util.df(bars)
        df.set_index("date", inplace=True)
        return df

    def get_iv_history(self, ticker, end, barSizeSetting="1 day", duration="5 D"):
        if type(end) == str:
            end = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=4)
        self._ensure()
        contract = Stock(ticker, "SMART", "USD")

        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime=end,
            durationStr=duration,
            barSizeSetting=barSizeSetting,
            whatToShow="OPTION_IMPLIED_VOLATILITY",
            useRTH=True
        )
        df = util.df(bars)
        df.set_index("date", inplace=True)
        return df

    def get_vix_history(self, end, duration="5 D"):
        if type(end) == str:
            end = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=4)
        self._ensure()
        contract = Index("VIX", "CBOE", "USD")

        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime=end,
            durationStr=duration,
            barSizeSetting="1 day",
            whatToShow="TRADES",
            useRTH=True
        )
        df = util.df(bars)
        df.set_index("date", inplace=True)
        return df
    