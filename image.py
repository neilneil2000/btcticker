from PIL import ImageFont
from PIL import ImageDraw
from PIL import Image
from PIL import ImageOps
import os
import textwrap
import currency
import logging
import requests
import decimal
import time

from sparkline import Spark

class Slide:
    """
    Class representing a slide for the ticker, showing the logo, graph, price etc
     - next_slide()  Build new slide with new data for next currency in list
    """
    HEADERS = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) \
                 Chrome/39.0.2171.95 Safari/537.36'}
    dir_name = os.path.dirname(__file__)

    def __init__(self):
        self.logger = logging.getLogger("btcticker.display.image")
        self.pic_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')
        self.font_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts/googlefonts')
        
        self.font_date = ImageFont.truetype(os.path.join(self.font_dir, 'PixelSplitter-Bold.ttf'), 11)
        self.my_spark = Spark(self.pic_dir)

        self.image = None
        self.draw = None
        self.colour = True  # TODO: Read it in from the config file
        self.inverted = False
        self.volume = False
        self.data = None
        self.price_now_string = ""
        self.days = 0

        self.logger.debug("Slide class initialised, returning...")
        
    def generate_slide(self, data, days, inverted, orientation, colour):
        self.data = data
        self.days = days
        self.inverted = inverted
        self.orientation = orientation
        self.colour = colour
        self.my_spark.make_spark(self.data.price_stack)
        self.build_image()
        return self.image
        

    def build_image(self):
        """
        Takes the price data, the desired coin/fiat combo along with the config info for formatting
        if config is re-written following adjustment we could avoid passing the last two arguments as
        they will just be the first two items of their string in config
        """        
        # THIS DOES NOT WORK PROPERLY FOR MY SCREEN SIZE
        if self.orientation == 0 or self.orientation == 180:
            self.white_background(self.colour)
            self.apply_spark(10,100)
            self.apply_token(0,0)
            self.apply_price(65)
            self.apply_price_change(110,95)
            self.apply_date(50,10)
            if self.volume:
                self.apply_volume(100,240) 
            if self.data.all_time_high_flag:
                self.apply_all_time_high(174,61)

        if self.orientation == 90 or self.orientation == 270:
            self.logger.debug("Orientation is 90 or 270")
            self.white_background(self.colour)
            self.apply_spark(88,40)
            self.apply_token(0,0)
            self.apply_price(65)
            self.apply_price_change(107,142)
            self.apply_date(80,10)
            if self.volume:
                self.apply_volume(100,210)           
            if self.data.all_time_high_flag:
                self.apply_all_time_high(174,61)
                
        if self.orientation == 270 or self.orientation == 180:
                self.image = self.image.rotate(180, expand=True)
 
        if self.inverted:
            self.image = ImageOps.invert(self.image)

    def white_background(self, colour):
        if colour:
            self.image = Image.new('RGB', (320, 240), (255, 255, 255))
        else:
            self.image = Image.new('L', (320, 240), 255)
        self.draw = ImageDraw.Draw(self.image)


    def calc_price_change(self):
        price_change_raw = round((self.data.price_now - self.data.price_stack[0]) / self.data.price_now * 100, 2)
        if price_change_raw >= 10:
            self.price_change = str("%+d" % price_change_raw) + "%"
        else:
            self.price_change = str("%+.2f" % price_change_raw) + "%"

    def apply_volume(self,x,y):
        self.draw.text((100, 210), "24h vol : " + self.human_format(self.volume), font=self.font_date, fill=0)


    def apply_all_time_high(self,x,y):
        all_time_high_bitmap = Image.open(os.path.join(self.pic_dir, 'ATH.bmp'))
        self.image.paste(all_time_high_bitmap, (x, y))


    def apply_price_change(self,x,y):
        self.calc_price_change()
        self.draw.text((107, 142), str(self.days) + " day : " + self.price_change, font=self.font_date, fill=0)  # Write price change to screen
    
    
    def apply_price(self,y):
        font_size = 60
        symbol_string = currency.symbol(self.data.fiat.upper())
        if self.data.fiat == "jpy" or self.data.fiat == "cny":
            symbol_string = "¥"
        d = decimal.Decimal(str(self.data.price_now)).as_tuple().exponent
        if self.data.price_now > 1000:
            price_now_string = str(format(int(self.data.price_now), ","))
        elif self.data.price_now < 1000 and d == -1:
            price_now_string = "{:.2f}".format(self.data.price_now)
        else:
            price_now_string = "{:.3g}".format(self.data.price_now)
        self.price_now_string = price_now_string
        self.write_wrapped_lines(self.image, symbol_string + self.price_now_string, font_size, y, 8, 10, "Roboto-Medium")


    def apply_date(self,x,y):
        self.draw.text((x,y), str(time.strftime("%-I:%M %p, s%d %b %Y")), font=self.font_date, fill=0)

    def apply_spark(self,x,y):
        spark_bitmap = Image.open(os.path.join(self.pic_dir, 'spark.bmp'))
        self.image.paste(spark_bitmap, (x, y))

    def apply_token(self,x,y):
        self.logger.debug("self.inverted= " + str(self.inverted))
        if self.inverted:
            currency_thumbnail = 'currency/' + self.data.coin + 'INV.bmp'
        else:
            currency_thumbnail = 'currency/' + self.data.coin + '.bmp'
        
        self.logger.debug(currency_thumbnail)
        
        token_filename = os.path.join(self.pic_dir, currency_thumbnail)

        if os.path.isfile(token_filename):
            token_image = Image.open(token_filename).convert("RGBA")
        else:
            token_image = self.fetch_token_image(token_filename)
        self.image.paste(token_image, (x, y))

    def fetch_token_image(self, token_filename):
        self.logger.debug("Getting token Image from Coingecko")
        token_image_url = "https://api.coingecko.com/api/v3/coins/" + self.data.coin + \
                        "?tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"

        if self.get_gecko(token_image_url):
            self.logger.debug("Got token info OK")
        else:
            self.logger.info("Failed to get token info...unhandled exception")
        
        if self.get_gecko(self.raw_json['image']['large'],stream=True):
            self.logger.debug("Got token image")
        else:
            self.logger.info("Failed to get token image...unhandled exception")

        self.token_image = Image.open(self.raw_stream).convert("RGBA")

        resize = 100, 100
        self.token_image.thumbnail(resize, Image.ANTIALIAS)
        # If inverted is true, invert the token symbol before placing if on the white BG so that it is uninverted at the end - this will make things more
        # legible on a black display
        if self.inverted:
            # PIL doesnt like to invert binary images, so convert to RGB, invert and then convert back to RGBA
            token_image = ImageOps.invert(self.token_image.convert('RGB'))
            token_image = token_image.convert('RGBA')
        new_image = Image.new("RGBA", (120, 120), "WHITE")  # Create a white rgba background with a 10 pixel border
        new_image.paste(token_image, (10, 10), token_image)
        token_image = new_image
        token_image.thumbnail((100, 100), Image.ANTIALIAS)
        token_image.save(token_filename)
        return token_image

    def get_gecko(self,url,stream=False):
        """
        Get Info From CoinGecko
        Returns True on success, false on failure
        """
        connect_ok = False
        self.logger.debug("Fetching: " + url)
        try:
            gecko_response = requests.get(url, headers=Slide.HEADERS, stream=stream)
            self.logger.info("Data Requested. Status Code:" + str(gecko_response.status_code))
            if gecko_response.status_code == requests.codes.ok:
                connect_ok = True
                self.logger.debug("Got info from CoinGecko")
                if not stream:
                    self.logger.debug(gecko_response.json())
                    self.raw_json = gecko_response.json()
                else:
                    self.raw_stream = gecko_response.raw
        except requests.exceptions.RequestException as e:
            self.logger.error("Issue with CoinGecko")
            connect_ok = False
            self.raw_json = {}
        return connect_ok

    def human_format(self,num):
        """
        Convert value to max 3 decimal places with Million, Billion, Trillion etc 
        """
        num = float('{:.3f}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


    def place_text(self, img, text, x_offset=0, y_offset=0, fontsize=50, fontstring="Forum-Regular", fill=0):
        """
        Put some centered text at a location on the image (Default centre of screen)
        """
        draw = ImageDraw.Draw(img)
        try:
            filename = os.path.join(self.dir_name, './fonts/googlefonts/' + fontstring + '.ttf')
            font = ImageFont.truetype(filename, fontsize)
        except OSError:
            font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', fontsize)
        img_width, img_height = img.size
        text_width, _ = font.getsize(text)
        text_height = fontsize
        draw_x = (img_width - text_width) // 2 + x_offset
        draw_y = (img_height - text_height) // 2 + y_offset
        draw.text((draw_x, draw_y), text, font=font, fill=fill)


    def bean_a_problem(self, message):
        """
        Display Error Screen
        """
        #   A visual cue that the wheels have fallen off
        the_bean = Image.open(os.path.join(self.pic_dir, 'thebean.bmp'))
        image = Image.new('L', (320, 240), 255)  # 255: clear the image with white
        draw = ImageDraw.Draw(image)
        image.paste(the_bean, (60, 45))
        draw.text((95, 15), str(time.strftime("%-H:%M %p, %-d %b %Y")), font=self.font_date, fill=0)
        self.write_wrapped_lines(image, "Issue: " + message)
        return image


    def write_wrapped_lines(self, img, text, fontsize=20, y_text=20, height=15, width=25, fontstring="Roboto-Light"):
        """
        Write text centred on screen to a fixed width, starting y_text down from centre
        """
        lines = textwrap.wrap(text, width)
        num_lines = 0
        for line in lines:
            self.place_text(img, line, 0, y_text, fontsize, fontstring)
            y_text += height
            num_lines += 1
        return img