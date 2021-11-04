#!/usr/bin/python3
from PIL import Image, ImageOps
from PIL import ImageFont
from PIL import ImageDraw
import currency
import os
import sys
import logging
import RPi.GPIO as GPIO
# from waveshare_epd import epd2in7
import time
import requests
import urllib
import json
import matplotlib as mpl


import matplotlib.pyplot as plt
import yaml
import socket
import textwrap
import argparse
import decimal

import pygame

mpl.use('Agg')
os.putenv('SDL_FBDEV', '/dev/fb0')  # Set Output to PiTFT - Could be fb1 if desktop installed
os.putenv('SDL_AUDIODRIVER', 'dsp')  # Prevent ALSA errors in PyGame
pygame.init()
lcd = pygame.display.set_mode((320, 240))
pygame.mouse.set_visible(False)

dir_name = os.path.dirname(__file__)
pic_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')
font_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts/googlefonts')
configfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yaml')
font_date = ImageFont.truetype(os.path.join(font_dir, 'PixelSplitter-Bold.ttf'), 11)
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/39.0.2171.95 Safari/537.36'}
callback_running = False
config = {}
static_coins = {}
live_coin = {}
last_coin_fetch = 0

def internet(hostname="google.com"):
    """
    Check whether there is an internet connection by attempting a connection to google.com
    """
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        host = socket.gethostbyname(hostname)
        # connect to the host -- tells us if the host is actually
        # reachable
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except:
        logging.info("Google says No")
    return False


def human_format(num):
    """
    Convert value to max 3 decimal places with Million, Billion, Trillion etc 
    """
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def _place_text(img, text, x_offset=0, y_offset=0, fontsize=50, fontstring="Forum-Regular", fill=0):
    """
    Put some centered text at a location on the image (Default centre of screen)
    """
    draw = ImageDraw.Draw(img)
    try:
        filename = os.path.join(dir_name, './fonts/googlefonts/' + fontstring + '.ttf')
        font = ImageFont.truetype(filename, fontsize)
    except OSError:
        font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', fontsize)
    img_width, img_height = img.size
    text_width, _ = font.getsize(text)
    text_height = fontsize
    draw_x = (img_width - text_width) // 2 + x_offset
    draw_y = (img_height - text_height) // 2 + y_offset
    draw.text((draw_x, draw_y), text, font=font, fill=fill)


def write_wrapped_lines(img, text, fontsize=20, y_text=20, height=15, width=25, fontstring="Roboto-Light"):
    """
    Write text centred on screen to a fixed width, starting y_text down from centre
    """
    lines = textwrap.wrap(text, width)
    num_lines = 0
    for line in lines:
        _place_text(img, line, 0, y_text, fontsize, fontstring)
        y_text += height
        num_lines += 1
    return img


def get_gecko(coin, fiat, start_time=None, end_time=None):
    """
    Get Info From CoinGecko
    Gets Price History if start and end time given
    Gets Instantaneous info if no start/finish
    """
    if start_time and end_time:
        url = "https://api.coingecko.com/api/v3/coins/" + coin + \
                "/market_chart/range?vs_currency=" + fiat + "&from=" + str(start_time) + \
                "&to=" + str(end_time)
    else:
        exchange = config['ticker']['exchange']
        if exchange == "gecko" or exchange == "default":
            url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=" + fiat + "&ids=" + coin
        else:
            url = "https://api.coingecko.com/api/v3/exchanges/" + exchange + \
                "/tickers?coin_ids=" + coin + "&include_exchange_logo=false"
    logging.debug(url)
    try:
        gecko_json = requests.get(url, headers=headers).json()
        connect_ok = True
        logging.debug("Got info from CoinGecko")
    except requests.exceptions.RequestException as e:
        logging.error("Issue with CoinGecko")
        connect_ok = False
        gecko_json = {}
    return gecko_json, connect_ok


def get_data(other):
    """
    The function to grab the data (TO DO: need to test properly)
    """
    sleep_time = 10
    num_retries = 5
    coin, fiat = config_to_coin_and_fiat()
    logging.info("Getting Data")
    end_time = int(time.time())
    start_time = end_time - 60 * 60 * 24 * int(config['ticker']['sparklinedays'])

    time_series_stack = []
    for x in range(0, num_retries):
        time_series, success = get_gecko(coin, fiat, start_time, end_time)
        if success:
            for time_value in time_series['prices']:
                time_series_stack.append(float(time_value[1]))
            time.sleep(0.1)
        
        # Get the price
        if config['ticker']['exchange'] == 'default' or config['ticker']['exchange'] == 'gecko':
            live_coin, success = get_gecko(coin, fiat)
            if success:
                logging.debug(live_coin)
                live_coin = live_coin[0]
                price_now = float(live_coin['current_price'])
                # Quick workaround for error being thrown for obscure coins. TO DO: Examine further
                try:
                    other['market_cap_rank'] = int(live_coin['market_cap_rank'])
                except:
                    config['display']['showrank'] = False
                    other['market_cap_rank'] = 0
                other['volume'] = float(live_coin['total_volume'])
                time_series_stack.append(price_now)
        else:
            live_coin, success = get_gecko(coin, fiat)
            if success:
                the_index = -1
                upper_fiat = fiat.upper()
                for i in range(len(live_coin['tickers'])):
                    target = live_coin['tickers'][i]['target']
                    if target == upper_fiat:
                        the_index = i
                        logging.debug("Found " + upper_fiat + " at index " + str(i))
                #       if UPPERFIAT is not listed as a target the_index==-1 and it is time to go to sleep
                if the_index == -1:
                    logging.error(
                        "The exchange is not listing in " + upper_fiat + ". Misconfigured - shutting down script")
                    sys.exit()
                live_coin = live_coin['tickers'][the_index]
                price_now = float(live_coin['last'])
                other['market_cap_rank'] = 0  # For non-default the Rank does not show in the API, so leave blank
                other['volume'] = float(live_coin['converted_volume']['usd'])
                all_time_high = 1000000.0  # For non-default the ATH does not show in the API
                logging.debug("Got Live Data From CoinGecko")
                time_series_stack.append(price_now)
        if price_now > float(live_coin['ath']):
            other['ATH'] = True
        else:
            other['ATH'] = False
        if success:
            break
        else:
            logging.warning("Trying again in " + sleep_time + " seconds")
            time.sleep(sleep_time)  # wait before trying to fetch the data again
            sleep_time = min(sleep_time*2, 3600) #exponential backoff
    return time_series_stack, other


def bean_a_problem(message):
    """
    Display Error Screen
    """
    #   A visual cue that the wheels have fallen off
    the_bean = Image.open(os.path.join(pic_dir, 'thebean.bmp'))
    image = Image.new('L', (320, 240), 255)  # 255: clear the image with white
    draw = ImageDraw.Draw(image)
    image.paste(the_bean, (60, 45))
    draw.text((95, 15), str(time.strftime("%-H:%M %p, %-d %b %Y")), font=font_date, fill=0)
    write_wrapped_lines(image, "Issue: " + message)
    return image


def make_spark(price_stack):
    # Draw and save the sparkline that represents historical data
    # Subtract the mean from the sparkline to make the mean appear on the plot (it's really the x axis)
    mean = sum(price_stack) / float(len(price_stack))
    x = [xx - mean for xx in price_stack]
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
    plt.plot(x, color='k', linewidth=6)
    plt.plot(len(x) - 1, x[-1], color='r', marker='o')
    # Remove the Y axis
    for k, v in ax.spines.items():
        v.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axhline(c='k', linewidth=4, linestyle=(0, (5, 2, 1, 2)))
    # Save the resulting bmp file to the images directory
    plt.savefig(os.path.join(pic_dir, 'spark.png'), dpi=17)
    img_sparkline = Image.open(os.path.join(pic_dir, 'spark.png'))
    file_out = os.path.join(pic_dir, 'spark.bmp')
    img_sparkline.save(file_out)
    plt.close(fig)
    plt.cla()  # Close plot to prevent memory error
    ax.cla()  # Close axis to prevent memory error
    img_sparkline.close()
    return


def update_display(price_stack, other):
    """
    Takes the price data, the desired coin/fiat combo along with the config info for formatting
    if config is re-written following adjustment we could avoid passing the last two arguments as
    they will just be the first two items of their string in config
    """
 
    original_coin = config['ticker']['currency']
    original_coin_list = original_coin.split(",")
    original_coin_list = [x.strip(' ') for x in original_coin_list]
    coin, fiat = config_to_coin_and_fiat()
    days = int(config['ticker']['sparklinedays'])
    symbol_string = currency.symbol(fiat.upper())
    if fiat == "jpy" or fiat == "cny":
        symbol_string = "¥"
    price_now = price_stack[-1]
    if config['display']['inverted']:
        currency_thumbnail = 'currency/' + coin + 'INV.bmp'
    else:
        currency_thumbnail = 'currency/' + coin + '.bmp'
    token_filename = os.path.join(pic_dir, currency_thumbnail)
    spark_bitmap = Image.open(os.path.join(pic_dir, 'spark.bmp'))

    all_time_high_bitmap = Image.open(os.path.join(pic_dir, 'ATH.bmp'))
    #   Check for token image, if there isn't one, get on off coingecko, resize it and pop it on a white background
    if os.path.isfile(token_filename):
        logging.debug("Getting token Image from Image directory")
        token_image = Image.open(token_filename).convert("RGBA")
    else:
        logging.debug("Getting token Image from Coingecko")
        token_image_url = "https://api.coingecko.com/api/v3/coins/" + coin + \
                          "?tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
        raw_image = requests.get(token_image_url, headers=headers).json()
        token_image = Image.open(requests.get(raw_image['image']['large'], headers=headers, stream=True).raw).convert(
            "RGBA")
        resize = 100, 100
        token_image.thumbnail(resize, Image.ANTIALIAS)
        # If inverted is true, invert the token symbol before placing if on the white BG so that it is uninverted at the end - this will make things more
        # legible on a black display
        if config['display']['inverted']:
            # PIL doesnt like to invert binary images, so convert to RGB, invert and then convert back to RGBA
            token_image = ImageOps.invert(token_image.convert('RGB'))
            token_image = token_image.convert('RGBA')
        new_image = Image.new("RGBA", (120, 120), "WHITE")  # Create a white rgba background with a 10 pixel border
        new_image.paste(token_image, (10, 10), token_image)
        token_image = new_image
        token_image.thumbnail((100, 100), Image.ANTIALIAS)
        token_image.save(token_filename)
    price_change_raw = round((price_stack[-1] - price_stack[0]) / price_stack[-1] * 100, 2)
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
    if config['display']['orientation'] == 0 or config['display']['orientation'] == 180:
        image = Image.new('L', (240, 320), 255)  # 255: clear the image with white
        draw = ImageDraw.Draw(image)
        draw.text((110, 80), str(days) + "day :", font=font_date, fill=0)
        draw.text((110, 95), price_change, font=font_date, fill=0)
        write_wrapped_lines(image, symbol_string + price_now_string, 40, 65, 8, 10, "Roboto-Medium")
        image.paste(token_image, (0, 0))
        image.paste(spark_bitmap, (10, 100))
        draw.text((10, 10), str(time.strftime("%-I:%M %p, s%d %b %Y")), font=font_date, fill=0)
        if config['display']['orientation'] == 180:
            image = image.rotate(180, expand=True)

    if config['display']['orientation'] == 90 or config['display']['orientation'] == 270:
        if config['display']['colour']:
            image = Image.new('RGB', (320, 240), (255, 255, 255))  # (255,255,255): clear the image with white
        else:
            image = Image.new('L', (320, 240), 255)  # 255: clear the image with white
        draw = ImageDraw.Draw(image)
        if 'showvolume' in config['display'] and config['display']['showvolume']:
            draw.text((100, 210), "24h vol : " + human_format(other['volume']), font=font_date, fill=0)
        write_wrapped_lines(image, symbol_string + price_now_string, 50, 55, 8, 10, "Roboto-Medium")  # Write Price to Screen
        image.paste(spark_bitmap, (88, 40))  # Write Image to Screen
        image.paste(token_image, (0, 0))  # Write Token Icon Image to Screen
        draw.text((107, 142), str(days) + " day : " + price_change, font=font_date,
                  fill=0)  # Write price change to screen
        if other['ATH']:
            image.paste(all_time_high_bitmap, (174, 61))
        # Don't show rank for #1 coin, #1 doesn't need to show off
        if 'showrank' in config['display'] and config['display']['showrank'] and other['market_cap_rank'] > 1:
            draw.text((10, 105), "Rank: " + str("%d" % other['market_cap_rank']), font=font_date, fill=0)
        draw.text((95, 15), str(time.strftime("%-I:%M %p, %d %b %Y")), font=font_date, fill=0)
        if config['display']['orientation'] == 270:
            image = image.rotate(180, expand=True)
    #       This is a hack to deal with the mirroring that goes on in older waveshare libraries Uncomment line below if needed
    #       image = ImageOps.mirror(image)
    #   If the display is inverted, invert the image using ImageOps
    if config['display']['inverted']:
        image = ImageOps.invert(image)
    return image


def string_to_list(string):
    list = string.split(",")
    list = [x.strip(' ') for x in list]
    return list


def currency_cycle(curr_string):
    curr_list = string_to_list(curr_string)
    # Rotate the array of currencies from config.... [a b c] becomes [b c a]
    curr_list = curr_list[1:] + curr_list[:1]
    return curr_list


def display_image(img):
    img = img.convert('RGB')
    py_image = pygame.image.fromstring(img.tobytes(), img.size, img.mode).convert()
    lcd.blit(py_image, (0, 0))
    pygame.display.update()
    return


def init_keys():
    key1 = 17
    key2 = 22
    key3 = 23
    logging.debug('Setup GPIO keys')
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(key1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(key2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(key3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    the_keys = [key1, key2, key3]
    return the_keys


def add_key_event(the_keys):
    #   Add key_press events
    logging.debug('Add key events')
    bounce_time = 500
    GPIO.add_event_detect(the_keys[0], GPIO.FALLING, callback=key_press, bouncetime=bounce_time)
    GPIO.add_event_detect(the_keys[1], GPIO.FALLING, callback=key_press, bouncetime=bounce_time)
    GPIO.add_event_detect(the_keys[2], GPIO.FALLING, callback=key_press, bouncetime=bounce_time)
    return


def key_press(channel):
    global callback_running
    global config
    global last_coin_fetch
    while(callback_running):
        time.sleep(0.1)
    callback_running = True
    if channel == 17:
        logging.info('Cycle currencies')
        crypto_list = currency_cycle(config['ticker']['currency'])
        config['ticker']['currency'] = ",".join(crypto_list)
    elif channel == 22:
        logging.info('Rotate - 90')
        config['display']['orientation'] = (config['display']['orientation'] + 90) % 360
    elif channel == 23:
        logging.info('Invert Display')
        config['display']['inverted'] = not config['display']['inverted']
    elif channel == 19:
        logging.info('Cycle fiat')
        fiat_list = currency_cycle(config['ticker']['fiatcurrency'])
        config['ticker']['fiatcurrency'] = ",".join(fiat_list)
    last_coin_fetch = full_update(last_coin_fetch) #TODO: Split Screen Update and Data Update to allow screen changes independent of changing currency
    config_write()
    callback_running = False
    return


def config_write():
    """
    Write the config file following an adjustment made using the buttons
    This is so that the unit returns to its last state after it has been
    powered off
    """
    with open(configfile, 'w') as f:
       data = yaml.dump(config, f)


def config_read():
    """
    Read Config File into global variable
    """
    global config
    global static_coins
    with open(configfile, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    logging.info(config)
    config['display']['orientation'] = int(config['display']['orientation'])
    static_coins = config['ticker']['currency']

    # Quick Sanity check on update frequency
    if float(config['ticker']['updatefrequency']) < 5:
        logging.info("Throttling update frequency to 5 seconds")
        update_frequency = 5.0
    else:
        update_frequency = float(config['ticker']['updatefrequency'])
    
    return update_frequency


def full_update(last_coin_fetch):
    """
    The steps required for a full update of the display
    Earlier versions of the code didn't grab new data for some operations
    but the e-Paper is too slow to bother the coingecko API
    """
    other = {}
    try:
        price_stack, all_time_high = get_data(other)
        make_spark(price_stack)
        image = update_display(price_stack, other)
        display_image(image)
        last_grab = time.time()
        time.sleep(0.2)
    except Exception as e:
        message = "Data pull/print problem"
        image = bean_a_problem(str(e) + " Line: " + str(e.__traceback__.tb_lineno))
        display_image(image)
        time.sleep(20)
        last_grab = last_coin_fetch
    return last_grab


def config_to_coin_and_fiat():
    cryptos = string_to_list(config['ticker']['currency'])
    fiats = string_to_list(config['ticker']['fiatcurrency'])
    return cryptos[0], fiats[0]


def main():
    global config
    global last_coin_fetch
    # Check command line for logging level
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default='info', help='Set the log level (default: info)')
    args = parser.parse_args()

    # Set Logging Level
    log_level = getattr(logging, args.log.upper(), logging.WARN)
    logging.basicConfig(level=log_level)

    # Set timezone based on ip address
    try:
        os.system("sudo /home/pi/.local/bin/tzupdate")
    except:
        logging.info("Timezone Not Set")

    logging.info("Build Frame")

    keys = init_keys()  # Set Up Buttons
    add_key_event(keys)  # Add Key Events
        
    update_frequency = config_read()
    number_of_coins = len(config['ticker']['currency'].split(","))

    last_fetch_time = time.time() - update_frequency #Force first update

    while not internet():
        logging.info("Waiting for internet")
        time.sleep(1)
    
    try:
        if config['display']['cycle']:
            while True:
                if (time.time() - last_fetch_time > update_frequency):
                    last_fetch_time = full_update(last_fetch_time)
                    crypto_list = currency_cycle(config['ticker']['currency'])
                    config['ticker']['currency'] = ",".join(crypto_list)
                    config_write()
                time.sleep(0.1)
        else:
            while True:
                time.sleep(60)
    except IOError as e:
        logging.error(e)
        image = bean_a_problem(str(e) + " Line: " + str(e.__traceback__.tb_lineno))
        display_image(image)
    except Exception as e:
        logging.error(e)
        image = bean_a_problem(str(e) + " Line: " + str(e.__traceback__.tb_lineno))
        display_image(image)
    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        GPIO.cleanup()
        exit()


if __name__ == '__main__':
    main()
