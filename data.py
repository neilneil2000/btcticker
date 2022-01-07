from typing import List
from dataclasses import field, dataclass


@dataclass
class CoinData:
    """Class to hold data about given coin/fiat pair"""

    _price_stack: List[float] = field(default_factory=list)
    current_price = None
    all_time_high: float = None
    volume: float = None

    @property
    def price_stack(self):
        """Returns full price stack, including current price"""
        stack = self._price_stack.copy()
        stack.append(self.current_price)
        return stack

    @price_stack.setter
    def price_stack(self, prices: List[float]):
        """Set value of price_stack"""
        self._price_stack = prices
