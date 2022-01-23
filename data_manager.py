import logging
import time
import os

from typing import List, Tuple
from PIL import Image, ImageColor, ImageDraw

from gecko import GeckoConnection
from data import CoinData
from sparkline import SparkLine


class DataManager:
    """Class to manage data source"""

    SLEEP_TIME = 10
    RETRIES = 5
    PIC_DIR: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")

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

    def set_token_images(self) -> None:
        self.data.token_image_white_background = self.open_token_image("white")
        self.data.token_image_black_background = self.open_token_image("black")

    def open_token_image(self, background: str) -> Image.Image:
        token_filename = "currency/" + self.coin + "_" + background + ".bmp"

        token_filename = os.path.join(self.PIC_DIR, token_filename)
        if not os.path.isfile(token_filename):
            if not self.fetch_token_image(token_filename, background):
                return None
        return Image.open(token_filename).convert("RGBA")

    def fetch_token_image(
        self, token_filename: str, target_bg_colour_name: str
    ) -> bool:
        """Fetch Token Image from Web and change background to match target"""
        url = (
            "https://api.coingecko.com/api/v3/coins/"
            + self.coin
            + "?tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
        )
        connection = GeckoConnection()
        if not connection.fetch_json(url):
            return False

        token_image_url = connection.response.json()["image"]["large"]
        if not connection.fetch_stream(token_image_url):
            return False

        token_image = Image.open(connection.response.raw).convert("RGBA")

        bg_colour = self.get_background_colour(token_image)
        target_bg_colour = ImageColor.getrgb(target_bg_colour_name)
        if self.is_transparent(bg_colour):
            new_image = Image.new("RGBA", token_image.size, target_bg_colour_name)
            new_image.paste(im=token_image, mask=token_image)
        else:
            new_image = Image.new(
                mode="RGBA",
                size=(token_image.width + 2, token_image.height + 2),
                color=bg_colour,
            )
            new_image.paste(im=token_image, box=(1, 1), mask=token_image)
            r, g, b, _ = bg_colour
            if (r, g, b) != target_bg_colour:
                r, g, b = target_bg_colour
                target_bg_colour = (r, g, b, 255)
                ImageDraw.floodfill(
                    image=new_image, xy=(0, 0), value=target_bg_colour, thresh=20
                )
        new_image.thumbnail(size=(80, 80), resample=Image.ANTIALIAS)
        new_image.save(token_filename)
        return True

    @staticmethod
    def is_transparent(pixel: Tuple[int, int, int, int]) -> bool:
        if pixel[-1] == 0:
            return True
        return False

    @staticmethod
    def get_background_colour(image: Image.Image):
        pixels = image.load()
        return pixels[0, 0]

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

    def refresh(self) -> bool:
        """
        Refresh All Data
        """
        # self.clear_data()
        self.data.coin = self.coin
        self.data.fiat = self.fiat
        self.data.data_period_days = self.data_period_days
        self.logger.debug("Getting Data")
        end_time = int(time.time())
        start_time = end_time - self.data_period_seconds

        if not self.fetch_historical_data(start_time, end_time):
            return False
        self.process_historical_data()

        if not self.fetch_live_price():
            return False
        self.process_live_data()
        self.set_token_images()
        self.data.spark = SparkLine.generate_spark(self.data.price_stack)
        return True

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
