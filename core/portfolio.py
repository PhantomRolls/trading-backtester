import pandas as pd
from strategies.base import BaseStrategy

class Portfolio(BaseStrategy):
    def __init__(self, symbols, data_handler, strategy):
        super().__init__()
        self.cash = self.capital
        self.value = self.cash
        self.position_qty = {f"{symbol}_qty": 0 for symbol in symbols}
        self.symbols = symbols
        self.data_handler = data_handler
        self.strategy = strategy
        self.history = []

    def update(self, date, executed_orders):
        for order in executed_orders[date]:
            symbol = order['symbol']
            action = order['action']
            size = order['size']
            cost = order['cost']

            if action == 'buy':
                self.cash -= cost
                self.position_qty[f"{symbol}_qty"] += size
            elif action == 'sell':
                self.cash += abs(cost)
                self.position_qty[f"{symbol}_qty"] -= abs(size)
            elif action == 'exit':
                qty = self.position_qty[f"{symbol}_qty"]
                price = order['price']
                self.cash += qty * price
                self.position_qty[f"{symbol}_qty"] = 0
            elif action == 'deposit':
                self.position_qty[f"{symbol}_qty"] += size
        value = self.cash
        position_values = {}

        for symbol in self.symbols:
            price = self.data_handler.get(symbol).loc[[date]]
            if 'Adj Close' in price.columns:
                pos_value = self.position_qty[f"{symbol}_qty"] * price['Adj Close'].iloc[-1]
            else:
                pos_value = self.position_qty[f"{symbol}_qty"] * price['Close'].iloc[-1]
            value += pos_value
            position_values[symbol] = round(pos_value, 2)
            self.value = value


        self.history.append({
            'date': date,
            'cash': round(self.cash, 2),
            'value': round(value, 2),
            **self.position_qty,
            **position_values,  
        })

    def get_history(self):
        portfolio = pd.DataFrame(self.history).set_index('date')
        portfolio.to_csv(f'output/{self.strategy.name}/portfolio.csv')
        return portfolio