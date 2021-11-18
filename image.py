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

from sparkline import spark

class slide:
    """
    Class representing a slide for the ticker, showing the logo, graph, price etc
     - next_slide()  Build new slide with new data for next currency in list
    """
    dir_name = os.path.dirname(__file__)

    def __init__(self):
        self.pic_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')
        self.font_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts/googlefonts')
        
        self.font_date = ImageFont.truetype(os.path.join(self.font_dir, 'PixelSplitter-Bold.ttf'), 11)

        self.headers = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) \
                     Chrome/39.0.2171.95 Safari/537.36'}

        self.my_spark = spark(self.pic_dir)

    def generate_slide(self, coin, fiat, price_now, price_stack,all_time_high_flag, volume,days,inverted,orientation,colour):
        logging.debug(price_stack)
        self.my_spark.make_spark(price_stack)
        return self.build_image(coin,fiat,price_now,price_stack, all_time_high_flag,volume, days, inverted,orientation,colour)
        


    def build_image(self,coin,fiat,price_now, price_stack,all_time_high_flag,volume,days, inverted,orientation,colour=True):
        """
        Takes the price data, the desired coin/fiat combo along with the config info for formatting
        if config is re-written following adjustment we could avoid passing the last two arguments as
        they will just be the first two items of their string in config
        """
 
        symbol_string = currency.symbol(fiat.upper())
        if fiat == "jpy" or fiat == "cny":
            symbol_string = "¥"

        if inverted:
            currency_thumbnail = 'currency/' + coin + 'INV.bmp'
        else:
            currency_thumbnail = 'currency/' + coin + '.bmp'
        
        token_filename = os.path.join(self.pic_dir, currency_thumbnail)
        spark_bitmap = Image.open(os.path.join(self.pic_dir, 'spark.bmp'))
        all_time_high_bitmap = Image.open(os.path.join(self.pic_dir, 'ATH.bmp'))
        
        #   Check for token image, if there isn't one, get on off coingecko, resize it and pop it on a white background
        if os.path.isfile(token_filename):
            logging.debug("Getting token Image from Image directory")
            token_image = Image.open(token_filename).convert("RGBA")
        else:
            logging.debug("Getting token Image from Coingecko")
            token_image_url = "https://api.coingecko.com/api/v3/coins/" + coin + \
                            "?tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
            raw_image = requests.get(token_image_url, headers=self.headers).json()
            token_image = Image.open(requests.get(raw_image['image']['large'], headers=self.headers, stream=True).raw).convert(
                "RGBA")
            resize = 100, 100
            token_image.thumbnail(resize, Image.ANTIALIAS)
            # If inverted is true, invert the token symbol before placing if on the white BG so that it is uninverted at the end - this will make things more
            # legible on a black display
            if inverted:
                # PIL doesnt like to invert binary images, so convert to RGB, invert and then convert back to RGBA
                token_image = ImageOps.invert(token_image.convert('RGB'))
                token_image = token_image.convert('RGBA')
            new_image = Image.new("RGBA", (120, 120), "WHITE")  # Create a white rgba background with a 10 pixel border
            new_image.paste(token_image, (10, 10), token_image)
            token_image = new_image
            token_image.thumbnail((100, 100), Image.ANTIALIAS)
            token_image.save(token_filename)
        price_change_raw = round((price_now - price_stack[0]) / price_now * 100, 2)
        if price_change_raw >= 10:
            price_change = str("%+d" % price_change_raw) + "%"
        else:
            price_change = str("%+.2f" % price_change_raw) + "%"
        d = decimal.Decimal(str(price_now)).as_tuple().exponent
        if price_now > 1000:
            price_now_string = str(format(int(price_now), ","))
        elif price_now < 1000 and d == -1:
            price_now_string = "{:.2f}".format(price_now)
        else:
            price_now_string = "{:.3g}".format(price_now)
        # THIS DOES NOT WORK PROPERLY FOR MY SCREEN SIZE
        if orientation == 0 or orientation == 180:
            image = Image.new('L', (240, 320), 255)  # 255: clear the image with white
            draw = ImageDraw.Draw(image)
            draw.text((110, 80), str(days) + "day :", font=self.font_date, fill=0)
            draw.text((110, 95), price_change, font=self.font_date, fill=0)
            self.write_wrapped_lines(image, symbol_string + price_now_string, 40, 65, 8, 10, "Roboto-Medium")
            image.paste(token_image, (0, 0))
            image.paste(spark_bitmap, (10, 100))
            draw.text((10, 10), str(time.strftime("%-I:%M %p, s%d %b %Y")), font=font_date, fill=0)
            if orientation == 180:
                image = image.rotate(180, expand=True)

        if orientation == 90 or orientation == 270:
            if colour:
                image = Image.new('RGB', (320, 240), (255, 255, 255))  # (255,255,255): clear the image with white
            else:
                image = Image.new('L', (320, 240), 255)  # 255: clear the image with white
            draw = ImageDraw.Draw(image)
            if volume:
                draw.text((100, 210), "24h vol : " + self.human_format(volume), font=self.font_date, fill=0)
            self.write_wrapped_lines(image, symbol_string + price_now_string, 50, 55, 8, 10, "Roboto-Medium")  # Write Price to Screen
            image.paste(spark_bitmap, (88, 40))  # Write Image to Screen
            image.paste(token_image, (0, 0))  # Write Token Icon Image to Screen
            draw.text((107, 142), str(days) + " day : " + price_change, font=self.font_date,
                    fill=0)  # Write price change to screen
            if all_time_high_flag:
                image.paste(all_time_high_bitmap, (174, 61))
            # Don't show rank for #1 coin, #1 doesn't need to show off
            if orientation == 270:
                image = image.rotate(180, expand=True)
        #       This is a hack to deal with the mirroring that goes on in older waveshare libraries Uncomment line below if needed
        #       image = ImageOps.mirror(image)
        #   If the display is inverted, invert the image using ImageOps
        if inverted:
            image = ImageOps.invert(image)
        return image


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