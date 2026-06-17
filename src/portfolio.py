import json
from typing import List, Dict, Optional
from datetime import datetime
from src.trade import Trade

class Portfolio:
    """Manages a collection of trades and calculates portfolio metrics."""
    
    def __init__(self, filepath: str = 'data/trades.json'):
        self.filepath = filepath
        self.trades: List[Trade] = []
        self.current_prices: Dict[str, float] = {}
        self.load_trades()
    
    def add_trade(self, trade: Trade) -> None:
        """Add a new trade to the portfolio."""
        self.trades.append(trade)
        self.save_trades()
    
    def close_trade(self, trade_index: int, exit_price: float, exit_date: datetime) -> None:
        """Close an open trade."""
        if 0 <= trade_index < len(self.trades):
            self.trades[trade_index].exit_price = exit_price
            self.trades[trade_index].exit_date = exit_date
            self.save_trades()
    
    def set_current_price(self, symbol: str, price: float) -> None:
        """Set current market price for a symbol."""
        self.current_prices[symbol] = price
    
    def get_trades_by_symbol(self, symbol: str) -> List[Trade]:
        """Get all trades for a specific symbol."""
        return [t for t in self.trades if t.symbol == symbol]
    
    def get_open_positions(self) -> List[Trade]:
        """Get all open (unclosed) positions."""
        return [t for t in self.trades if t.is_open]
    
    def get_closed_positions(self) -> List[Trade]:
        """Get all closed positions."""
        return [t for t in self.trades if not t.is_open]
    
    def load_trades(self) -> None:
        """Load trades from JSON file."""
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                self.trades = [
                    Trade(
                        symbol=t['symbol'],
                        quantity=t['quantity'],
                        entry_price=t['entry_price'],
                        entry_date=datetime.fromisoformat(t['entry_date']),
                        exit_price=t.get('exit_price'),
                        exit_date=datetime.fromisoformat(t['exit_date']) if t.get('exit_date') else None
                    )
                    for t in data
                ]
        except FileNotFoundError:
            self.trades = []
    
    def save_trades(self) -> None:
        """Save trades to JSON file."""
        data = [
            {
                'symbol': t.symbol,
                'quantity': t.quantity,
                'entry_price': t.entry_price,
                'entry_date': t.entry_date.isoformat(),
                'exit_price': t.exit_price,
                'exit_date': t.exit_date.isoformat() if t.exit_date else None
            }
            for t in self.trades
        ]
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)
