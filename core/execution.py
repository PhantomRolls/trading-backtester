from strategies.base import BaseStrategy

class OrderExecutor(BaseStrategy):
    def __init__(self, data_handler):
        super().__init__()
        self.slippage_pct = self.general_config["slippage"]
        self.fee_pct = self.general_config["fee_rate"]
        self.data_handler = data_handler

    def execute(self, orders, date, order_time='Open'):
        executed = {date: []}
        for order in orders:
            symbol = order['symbol']
            action = order['action']
            size = order['size']

            try:
                price = self.data_handler.get(symbol, price=order_time).loc[date]
            except KeyError:
                continue

            slippage = price * self.slippage_pct
            executed_price = price + slippage if action == 'buy' else price - slippage
            fee = executed_price * abs(size) * self.fee_pct
            cost = executed_price * size + (fee if action == 'buy' else -fee)

            executed[date].append({
                'symbol': symbol,
                'action': action,
                'size': size,
                'price': round(executed_price, 2),
                'cost': round(cost, 2),
                'fee': round(fee, 3)
            })
        return executed
