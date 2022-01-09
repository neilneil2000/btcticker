import logging
import time

from gecko import GeckoConnection
from typing import List

from data import CoinData


class DataManager:
    """Class to manage data source"""

    SLEEP_TIME = 10
    RETRIES = 5

    def __init__(
        self, data_period_days: int, coins: List[str], fiats: List[str]
    ) -> None:
        self.logger: logging.Logger = logging.getLogger("btcticker.data")
        self.data_period_days: int = data_period_days
        self.coins: List[str] = coins
        self.fiats: List[str] = fiats
        self._coin_pointer: int = 0
        self._fiat_pointer: int = 0

        self.data: CoinData = CoinData()
        self.gecko: GeckoConnection = GeckoConnection()

    @property
    def coin(self) -> str:
        """Returns the current coin"""
        return self.coins[self._coin_pointer]

    @property
    def fiat(self) -> str:
        """Returns the current fiat"""
        return self.fiats[self._fiat_pointer]

    @property
    def data_period_seconds(self):
        """Returns the number of seconds in the data period"""
        return 60 * 60 * 24 * self.data_period_days

    def next_crypto(self) -> None:
        """Increment Crypto Pointer"""
        if self._coin_pointer < len(self.coins) - 1:
            self._coin_pointer += 1
        else:
            self._coin_pointer = 0

    def next_fiat(self) -> None:
        """Increment Fiat Pointer"""
        if self._fiat_pointer < len(self.fiats) - 1:
            self._fiat_pointer += 1
        else:
            self._fiat_pointer = 0

    def process_historical_data(self) -> None:
        """Process data response from InfoProvider"""
        _, prices = zip(*self.gecko.response.json()["prices"])
        self.data.price_stack = list(prices)

    def process_live_data(self) -> None:
        """Store Live Price Data in CoinData Object"""
        live_data = self.gecko.response.json()[0]

        self.data.current_price = float(live_data["current_price"])
        self.data.volume = float(live_data["total_volume"])
        self.data.all_time_high = live_data["ath"]

    def clear_data(self) -> None:
        """Clear coin data - leave reference to coin, fiat pair"""
        self.data.current_price = None
        self.data.price_stack = []
        self.data.all_time_high = None
        self.data.volume = None

    def refresh(self) -> CoinData:
        """
        Refresh Data From Coin Gecko
        """
        # self.clear_data()
        self.data.coin = self.coin
        self.data.fiat = self.fiat
        self.data.data_period_days = self.data_period_days
        self.logger.debug("Getting Data")
        end_time = int(time.time())
        start_time = end_time - self.data_period_seconds

        if not self.fetch_historical_data(start_time, end_time):
            return
        self.process_historical_data()

        if not self.fetch_live_price():
            return
        self.process_live_data()

        return self.data

    @property
    def all_time_high_flag(self):
        """Confirm whether we are currently at or above all time high"""
        if self.data.current_price >= self.data.all_time_high:
            return True
        return False

    def fetch_live_price(self):
        """Get current spot price"""
        url = (
            "https://api.coingecko.com/api/v3/coins/markets?vs_currency="
            + self.fiat
            + "&ids="
            + self.coin
        )
        return self.gecko.fetch_json(url)

    def fetch_historical_data(self, start_time: int, end_time: int) -> bool:
        """Get historical data between times specified"""
        url = (
            "https://api.coingecko.com/api/v3/coins/"
            + self.coin
            + "/market_chart/range?vs_currency="
            + self.fiat
            + "&from="
            + str(start_time)
            + "&to="
            + str(end_time)
        )
        return self.gecko.fetch_json(url)
