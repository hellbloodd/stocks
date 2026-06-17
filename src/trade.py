from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Trade:
    """Represents a single trade transaction."""
    symbol: str
    quantity: float
    entry_price: float
    entry_date: datetime
    exit_price: Optional[float] = None
    exit_date: Optional[datetime] = None
    
    @property
    def is_open(self) -> bool:
        """Check if the position is still open."""
        return self.exit_price is None
    
    @property
    def current_value(self, current_price: float) -> float:
        """Calculate current position value."""
        price = self.exit_price if self.exit_price else current_price
        return self.quantity * price
    
    @property
    def cost_basis(self) -> float:
        """Calculate total cost of position."""
        return self.quantity * self.entry_price
    
    @property
    def profit_loss(self, current_price: Optional[float] = None) -> float:
        """Calculate profit/loss for this trade."""
        exit = self.exit_price if self.exit_price else current_price
        if exit is None:
            return 0
        return (exit - self.entry_price) * self.quantity
    
    @property
    def profit_loss_percent(self, current_price: Optional[float] = None) -> float:
        """Calculate profit/loss percentage."""
        if self.entry_price == 0:
            return 0
        pl = self.profit_loss(current_price)
        return (pl / self.cost_basis) * 100
