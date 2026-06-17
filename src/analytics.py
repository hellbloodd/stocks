from typing import List, Dict, Tuple
from src.portfolio import Portfolio
from src.trade import Trade

class PortfolioAnalytics:
    """Analyze portfolio performance and profitability."""
    
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
    
    def get_profit_loss_by_symbol(self) -> Dict[str, Dict[str, float]]:
        """Calculate total profit/loss for each symbol."""
        result = {}
        symbols = set(t.symbol for t in self.portfolio.trades)
        
        for symbol in symbols:
            trades = self.portfolio.get_trades_by_symbol(symbol)
            total_pl = sum(
                t.profit_loss(self.portfolio.current_prices.get(symbol, t.exit_price))
                for t in trades
            )
            total_invested = sum(t.cost_basis for t in trades)
            pl_percent = (total_pl / total_invested * 100) if total_invested > 0 else 0
            
            result[symbol] = {
                'profit_loss': total_pl,
                'profit_loss_percent': pl_percent,
                'trade_count': len(trades),
                'total_invested': total_invested
            }
        
        return result
    
    def get_sorted_by_performance(self, ascending: bool = False) -> List[Tuple[str, Dict]]:
        """Get symbols sorted by profit/loss (best to worst or vice versa)."""
        pl_data = self.get_profit_loss_by_symbol()
        sorted_data = sorted(
            pl_data.items(),
            key=lambda x: x[1]['profit_loss'],
            reverse=not ascending
        )
        return sorted_data
    
    def get_portfolio_summary(self) -> Dict:
        """Get overall portfolio summary."""
        pl_data = self.get_profit_loss_by_symbol()
        
        total_pl = sum(v['profit_loss'] for v in pl_data.values())
        total_invested = sum(v['total_invested'] for v in pl_data.values())
        overall_pl_percent = (total_pl / total_invested * 100) if total_invested > 0 else 0
        
        return {
            'total_profit_loss': total_pl,
            'total_profit_loss_percent': overall_pl_percent,
            'total_invested': total_invested,
            'symbol_count': len(pl_data),
            'trade_count': len(self.portfolio.trades)
        }
