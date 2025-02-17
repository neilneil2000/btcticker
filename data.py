from typing import List
from dataclasses import field, dataclass
from PIL import Image

from sparkline import SparkLine


@dataclass
class CoinData:
    """Class to hold data about given coin/fiat pair"""

    _price_stack: List[float] = field(default_factory=list)
    current_price = None
    all_time_high: float = None
    volume: float = None
    coin: str = None
    fiat: str = None
    data_period_days: int = None
    token_image_white_background: Image.Image = None
    token_image_black_background: Image.Image = None
    spark: Image.Image = None

    @property
    def price_stack(self) -> List[float]:
        """Returns full price stack, including current price"""
        stack = self._price_stack.copy()
        stack.append(self.current_price)
        return stack

    @price_stack.setter
    def price_stack(self, prices: List[float]) -> None:
        """Set value of price_stack"""
        self._price_stack = prices

    @property
    def price_change_percentage(self) -> float:
        """Calculate Price Change Percentage"""
        price_change = self.current_price - self._price_stack[0]
        percentage_change = price_change * 100 / self._price_stack[0]
        return percentage_change

    @property
    def all_time_high_flag(self) -> bool:
        """Return True is current price at or equal to all time high"""
        if self.current_price >= self.all_time_high:
            return True
        return False
