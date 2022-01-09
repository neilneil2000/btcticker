import os
import textwrap
import time
import logging

from typing import Tuple
import currency
from PIL import ImageFont, Image, ImageDraw, ImageOps

from sparkline import SparkLine
from gecko import GeckoConnection
from data import CoinData


class Slide:
    """
    Class representing a slide for the ticker, showing the logo, graph, price etc
    """

    dir_name = os.path.dirname(__file__)

    pic_dir: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
    font_dir: str = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "fonts/googlefonts"
    )

    font_date: str = ImageFont.truetype(
        os.path.join(font_dir, "PixelSplitter-Bold.ttf"), 11
    )

    PRICE_FONT_SIZE = 60

    logger: logging.Logger = logging.getLogger("btcticker.display.image")

    def __init__(
        self,
        size: Tuple[int, int],
        orientation: int,
        inverted: bool = False,
        colour: bool = True,
    ) -> None:
        self.size = size
        self.orientation = orientation
        self.is_inverted = inverted
        self.is_colour = colour

        self.image: Image.Image = None
        self.volume: float = False
        self.data = None

    def generate_slide(self, data: CoinData) -> Image:
        self.data = data
        self.build_image()
        return self.image

    def build_image(self) -> None:
        """
        Takes the price data, the desired coin/fiat combo along with the config info for formatting
        if config is re-written following adjustment we could avoid passing the last two arguments as
        they will just be the first two items of their string in config
        """
        # THIS DOES NOT WORK PROPERLY FOR MY SCREEN SIZE
        if self.orientation in (0, 180):
            self.white_background()
            self.apply_spark((10, 100))
            self.apply_price(65)
            self.apply_price_change((110, 95))
            self.apply_date((50, 10))
            if self.volume:
                self.apply_volume((100, 240))
            if self.data.all_time_high_flag:
                self.apply_all_time_high((174, 61))

        if self.orientation in (90, 270):
            self.white_background()
            self.apply_spark((88, 40))
            self.apply_price(65)
            self.apply_price_change((107, 142))
            self.apply_date((100, 10))
            if self.volume:
                self.apply_volume((100, 210))
            if self.data.all_time_high_flag:
                self.apply_all_time_high((174, 61))

        if self.is_inverted:
            self.image = ImageOps.invert(self.image)
        self.apply_token((0, 0))

        if self.orientation in (180, 270):
            self.image = self.image.rotate(180, expand=True)

    def white_background(self) -> None:
        """Creates new White Background"""
        if self.is_colour:
            self.image = Image.new(mode="RGB", size=self.size, color=(255, 255, 255))
        else:
            self.image = Image.new(mode="L", size=self.size, color=255)

    def generate_percentage_string(self) -> str:
        """Calculate Price Change Percentages"""
        percent_number = self.data.price_change_percentage
        if percent_number >= 10:
            percent_string = str("%+d" % percent_number) + "%"
        else:
            percent_string = str("%+.2f" % percent_number) + "%"
        return percent_string

    def apply_volume(self, position: Tuple[int, int]) -> None:
        """
        Apply trading volume to Slide
        position : where on slide to place top left pixel of image
        """
        ImageDraw.Draw(self.image).text(
            xy=position,
            text=" ".join(["24h", "vol", ":", self.human_format(self.volume)]),
            font=self.font_date,
            fill=0,
        )

    def apply_all_time_high(self, position: Tuple[int, int]) -> None:
        """
        Apply 'All Time High' Image to Slide
        position : where on slide to place top left pixel of image
        """
        all_time_high_image = Image.open(os.path.join(self.pic_dir, "ATH.bmp"))
        self.image.paste(im=all_time_high_image, box=position)

    def apply_price_change(self, position: Tuple[int, int]) -> None:
        """
        Apply Percentage Price Change to Slide
        position : where on slide to place top left pixel of image
        """
        text = " ".join(
            [
                str(self.data.data_period_days),
                "day",
                ":",
                self.generate_percentage_string(),
            ],
        )
        ImageDraw.Draw(self.image).text(
            xy=position,
            text=text,
            font=self.font_date,
            fill=0,
        )

    def apply_price(self, y_position: int) -> None:
        """
        Apply Price to Slide
        y_position = number of pixels from left on Slide
        """
        fiat = self.data.fiat.upper()
        symbol = "¥" if fiat in ("JPY", "CNY") else currency.symbol(fiat)

        price = self.format_price(self.data.current_price)
        self.write_wrapped_lines(
            text=symbol + price,
            fontsize=self.PRICE_FONT_SIZE,
            y_offset=y_position,
            line_height=8,
            max_width=10,
            font="Roboto-Medium",
        )

    def format_price(self, price: float) -> str:
        """Format Price String"""
        if price >= 1000:  # Ignore pence and add comma seperator
            formatted_price = str(format(int(price), ","))
        elif price < 1:  # 3sig fig
            formatted_price = "{:.3g}".format(price)
        else:  # £XX.xx
            formatted_price = "{:.2f}".format(price)

        return formatted_price

    def apply_date(self, position: Tuple[int, int]) -> None:
        """Apply Date to Slide"""
        ImageDraw.Draw(self.image).text(
            xy=position,
            text=str(time.strftime("%-I:%M %p, s%d %b %Y")),
            font=self.font_date,
            fill=0,
        )

    def apply_spark(self, position: Tuple[int, int]) -> None:
        """Apply Sparkline to Slide"""
        SparkLine(self.pic_dir)
        spark_bitmap = Image.open(os.path.join(self.pic_dir, "spark.bmp"))
        self.image.paste(spark_bitmap, position)

    def apply_token(self, position: Tuple[int, int]) -> None:
        """Apply token image to Slide"""

        currency_thumbnail = "currency/" + self.data.coin
        if self.is_inverted:
            currency_thumbnail += "INV"
        currency_thumbnail += ".bmp"

        token_filename = os.path.join(self.pic_dir, currency_thumbnail)

        if not os.path.isfile(token_filename):
            self.fetch_token_image(token_filename)
        token_image = Image.open(token_filename).convert("RGBA")

        self.image.paste(token_image, position)

    def fetch_token_image(self, token_filename) -> bool:
        """Fetch Token Image from Web"""
        url = (
            "https://api.coingecko.com/api/v3/coins/"
            + self.data.coin
            + "?tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
        )
        if not GeckoConnection.fetch_json(url):
            return False
        token_image_url = GeckoConnection.response.json()["image"]["large"]
        if not GeckoConnection.fetch_stream(token_image_url):
            return False

        token_image = Image.open(GeckoConnection.response.raw).convert("RGBA")

        target_size = (100, 100)
        border_size = (10, 10)
        token_image.thumbnail(target_size, Image.ANTIALIAS)
        # If inverted is true, invert the token symbol before placing if on the white BG so that it is uninverted at the end - this will make things more
        # legible on a black display
        if self.is_inverted:
            # PIL doesnt like to invert binary images, so convert to RGB, invert and then convert back to RGBA
            token_image = ImageOps.invert(token_image.convert("RGB"))
            token_image = token_image.convert("RGBA")
        new_image = Image.new(
            "RGBA", (120, 120), "WHITE"
        )  # Create a white rgba background with a 10 pixel border
        new_image.paste(token_image, border_size, token_image)
        token_image = new_image
        token_image.thumbnail(target_size, Image.ANTIALIAS)
        token_image.save(token_filename)
        return True

    def human_format(self, num: float) -> str:
        """
        Create human readable string for number
        Convert value to max 3 decimal places with Million, Billion, Trillion etc
        """
        num = float("{:.3f}".format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return "{}{}".format(
            "{:f}".format(num).rstrip("0").rstrip("."),
            ["", "K", "M", "B", "T"][magnitude],
        )

    def place_text(
        self,
        text: str,
        x_offset: int = 0,
        y_offset: int = 0,
        fontsize: int = 50,
        font_name: str = "Forum-Regular",
    ):
        """
        Put some centered text at a location on the Slide
        Default position - centre of screen
        """
        canvas = ImageDraw.Draw(self.image)
        try:
            filename = os.path.join(
                self.dir_name, "./fonts/googlefonts/" + font_name + ".ttf"
            )
            font = ImageFont.truetype(filename, fontsize)
        except OSError:
            font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", fontsize)
        img_width, img_height = self.size
        text_width, text_height = font.getsize(text)
        draw_x = (img_width - text_width) // 2 + x_offset
        draw_y = (img_height - text_height) // 2 + y_offset
        canvas.text(xy=(draw_x, draw_y), text=text, font=font, fill=0)

    def bean_a_problem(self, message: str) -> Image:
        """
        Create an Error Slide
        """
        #   A visual cue that the wheels have fallen off
        the_bean = Image.open(os.path.join(self.pic_dir, "thebean.bmp"))
        image = Image.new("L", (320, 240), 255)  # 255: clear the image with white
        draw = ImageDraw.Draw(image)
        image.paste(the_bean, (60, 45))
        draw.text(
            xy=(95, 15),
            text=str(time.strftime("%-H:%-M, %-d %b %y")),
            font=self.font_date,
            fill=0,
        )
        self.write_wrapped_lines(image, "Issue: " + message)
        return image

    def write_wrapped_lines(
        self,
        text: str,
        fontsize: int = 20,
        y_offset: int = 20,
        line_height: int = 15,
        max_width: int = 25,
        font: str = "Roboto-Light",
    ) -> None:
        """
        Write text centred on screen to a fixed width, starting y_text down from centre
        """
        for line in textwrap.wrap(text, max_width):
            self.place_text(
                text=line,
                x_offset=0,
                y_offset=y_offset,
                fontsize=fontsize,
                font_name=font,
            )
            y_offset += line_height
