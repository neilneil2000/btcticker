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
button_pressed = 0


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


def get_gecko(url):
    try:
        gecko_json = requests.get(url, headers=headers).json()
        connect_fail = False
    except requests.exceptions.RequestException as e:
        logging.error("Issue with CoinGecko")
        connect_fail = True
        gecko_json = {}
    return gecko_json, connect_fail


def get_data(config, other):
    """
    The function to grab the data (TO DO: need to test properly)
    """

    sleep_time = 10
    num_retries = 5
    which_coin, fiat = config_to_coin_and_fiat(config)
    logging.info("Getting Data")
    days_ago = int(config['ticker']['sparklinedays'])
    end_time = int(time.time())
    start_time = end_time - 60 * 60 * 24 * days_ago
    start_time_seconds = start_time
    end_time_seconds = end_time
    gecko_url_historical = "https://api.coingecko.com/api/v3/coins/" + which_coin + \
                           "/market_chart/range?vs_currency=" + fiat + "&from=" + str(start_time_seconds) + \
                           "&to=" + str(end_time_seconds)
    logging.debug(gecko_url_historical)
    time_series_stack = []
    for x in range(0, num_retries):
        raw_time_series, connect_fail = get_gecko(gecko_url_historical)
        if connect_fail:
            pass
        else:
            logging.debug("Got price for the last " + str(days_ago) + " days from CoinGecko")
            time_series_array = raw_time_series['prices']
            length = len(time_series_array)
            i = 0
            while i < length:
                time_series_stack.append(float(time_series_array[i][1]))
                i += 1
            # A little pause before hitting the api again
            time.sleep(1)
            # Get the price
        if config['ticker']['exchange'] == 'default':
            gecko_url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=" + fiat + "&ids=" + which_coin
            logging.debug(gecko_url)
            raw_live_coin, connect_fail = get_gecko(gecko_url)
            if connect_fail:
                pass
            else:
                logging.debug(raw_live_coin[0])
                live_price = raw_live_coin[0]
                price_now = float(live_price['current_price'])
                all_time_high = float(live_price['ath'])
                # Quick workaround for error being thrown for obscure coins. TO DO: Examine further
                try:
                    other['market_cap_rank'] = int(live_price['market_cap_rank'])
                except:
                    config['display']['showrank'] = False
                    other['market_cap_rank'] = 0
                other['volume'] = float(live_price['total_volume'])
                time_series_stack.append(price_now)
                if price_now > all_time_high:
                    other['ATH'] = True
                else:
                    other['ATH'] = False
        else:
            gecko_url = "https://api.coingecko.com/api/v3/exchanges/" + config['ticker'][
                'exchange'] + "/tickers?coin_ids=" + which_coin + "&include_exchange_logo=false"
            logging.debug(gecko_url)
            raw_live_coin, connect_fail = get_gecko(gecko_url)
            if connect_fail:
                pass
            else:
                the_index = -1
                upper_fiat = fiat.upper()
                for i in range(len(raw_live_coin['tickers'])):
                    target = raw_live_coin['tickers'][i]['target']
                    if target == upper_fiat:
                        the_index = i
                        logging.debug("Found " + upper_fiat + " at index " + str(i))
                #       if UPPERFIAT is not listed as a target the_index==-1 and it is time to go to sleep
                if the_index == -1:
                    logging.error(
                        "The exchange is not listing in " + upper_fiat + ". Misconfigured - shutting down script")
                    sys.exit()
                live_price = raw_live_coin['tickers'][the_index]
                price_now = float(live_price['last'])
                other['market_cap_rank'] = 0  # For non-default the Rank does not show in the API, so leave blank
                other['volume'] = float(live_price['converted_volume']['usd'])
                all_time_high = 1000000.0  # For non-default the ATH does not show in the API
                logging.debug("Got Live Data From CoinGecko")
                time_series_stack.append(price_now)
                if price_now > all_time_high:
                    other['ATH'] = True
                else:
                    other['ATH'] = False
        if connect_fail:
            message = "Trying again in ", sleep_time, " seconds"
            logging.warning(message)
            time.sleep(sleep_time)  # wait before trying to fetch the data again
            sleep_time *= 2  # exponential backoff
            sleep_time = min(sleep_time, 3600)
        else:
            break
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


def update_display(config, price_stack, other):
    """
    Takes the price data, the desired coin/fiat combo along with the config info for formatting
    if config is re-written following adjustment we could avoid passing the last two arguments as
    they will just be the first two items of their string in config
    """
    with open(configfile) as f:
        original_config = yaml.load(f, Loader=yaml.FullLoader)
    original_coin = original_config['ticker']['currency']
    original_coin_list = original_coin.split(",")
    original_coin_list = [x.strip(' ') for x in original_coin_list]
    which_coin, fiat = config_to_coin_and_fiat(config)
    days_ago = int(config['ticker']['sparklinedays'])
    symbol_string = currency.symbol(fiat.upper())
    if fiat == "jpy" or fiat == "cny":
        symbol_string = "¥"
    price_now = price_stack[-1]
    if config['display']['inverted']:
        currency_thumbnail = 'currency/' + which_coin + 'INV.bmp'
    else:
        currency_thumbnail = 'currency/' + which_coin + '.bmp'
    token_filename = os.path.join(pic_dir, currency_thumbnail)
    spark_bitmap = Image.open(os.path.join(pic_dir, 'spark.bmp'))
    logging.info(spark_bitmap.size)
    # TESTING - DRAW BOX AROUND SPARKLINE
    #    draw = ImageDraw.Draw(spark_bitmap)
    #    draw.line((0,0) + spark_bitmap.size, fill=128)
    #    draw.line((0, spark_bitmap.size[1]-1, spark_bitmap.size[0]-1, 0), fill=128)
    #    draw.line((0,0,spark_bitmap.size[0]-1,0), fill=128)
    #    draw.line((0,0,0,spark_bitmap.size[1]-1), fill=128)
    #    draw.line((spark_bitmap.size[0]-1,0,spark_bitmap.size[0]-1,spark_bitmap.size[1]-1), fill=128)
    #    draw.line((0,spark_bitmap.size[1]-1,spark_bitmap.size[0]-1,spark_bitmap.size[1]-1), fill=128)
    # END TEST
    all_time_high_bitmap = Image.open(os.path.join(pic_dir, 'ATH.bmp'))
    #   Check for token image, if there isn't one, get on off coingecko, resize it and pop it on a white background
    if os.path.isfile(token_filename):
        logging.debug("Getting token Image from Image directory")
        token_image = Image.open(token_filename).convert("RGBA")
    else:
        logging.debug("Getting token Image from Coingecko")
        token_image_url = "https://api.coingecko.com/api/v3/coins/" + which_coin + \
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
        draw.text((110, 80), str(days_ago) + "day :", font=font_date, fill=0)
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
        draw.text((107, 142), str(days_ago) + " day : " + price_change, font=font_date,
                  fill=0)  # Write price change to screen
        if other['ATH']:
            image.paste(all_time_high_bitmap, (174, 61))
        # Don't show rank for #1 coin, #1 doesn't need to show off
        if 'showrank' in config['display'] and config['display']['showrank'] and other['market_cap_rank'] > 1:
            draw.text((10, 105), "Rank: " + str("%d" % other['market_cap_rank']), font=font_date, fill=0)
        if config['display']['trendingmode'] and not (str(which_coin) in original_coin_list):
            draw.text((95, 28), which_coin, font=font_date, fill=0)
        #       draw.text((5,110),"In retrospect, it was inevitable",font =font_date,fill = 0)
        draw.text((95, 15), str(time.strftime("%-I:%M %p, %d %b %Y")), font=font_date, fill=0)
        if config['display']['orientation'] == 270:
            image = image.rotate(180, expand=True)
    #       This is a hack to deal with the mirroring that goes on in older waveshare libraries Uncomment line below if needed
    #       image = ImageOps.mirror(image)
    #   If the display is inverted, invert the image using ImageOps
    if config['display']['inverted']:
        image = ImageOps.invert(image)
    return image


def currency_string_to_list(curr_string):
    # Takes the string for currencies in the config.yaml file and turns it into a list
    curr_list = curr_string.split(",")
    curr_list = [x.strip(' ') for x in curr_list]
    return curr_list


def currency_cycle(curr_string):
    curr_list = currency_string_to_list(curr_string)
    # Rotate the array of currencies from config.... [a b c] becomes [b c a]
    curr_list = curr_list[1:] + curr_list[:1]
    return curr_list


def display_image(img):
    img = img.convert('RGB')
    mode = img.mode
    size = img.size
    data = img.tobytes()
    # logging.info(mode)
    # logging.info(size)

    py_image = pygame.image.fromstring(data, size, mode).convert()
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
    bounce_time = 300
    GPIO.add_event_detect(the_keys[0], GPIO.FALLING, callback=key_press, bouncetime=bounce_time)
    GPIO.add_event_detect(the_keys[1], GPIO.FALLING, callback=key_press, bouncetime=bounce_time)
    GPIO.add_event_detect(the_keys[2], GPIO.FALLING, callback=key_press, bouncetime=bounce_time)
    return


def key_press(channel):
    global button_pressed
    with open(configfile) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    last_coin_fetch = time.time()
    if channel == 17 and button_pressed == 0:
        logging.info('Cycle currencies')
        button_pressed = 1
        crypto_list = currency_cycle(config['ticker']['currency'])
        config['ticker']['currency'] = ",".join(crypto_list)
        last_coin_fetch = full_update(config, last_coin_fetch)
        config_write(config)
        return
    elif channel == 22 and button_pressed == 0:
        logging.info('Rotate - 90')
        button_pressed = 1
        config['display']['orientation'] = (config['display']['orientation'] + 90) % 360
        last_coin_fetch = full_update(config, last_coin_fetch)
        config_write(config)
        return
    elif channel == 23 and button_pressed == 0:
        logging.info('Invert Display')
        button_pressed = 1
        config['display']['inverted'] = not config['display']['inverted']
        last_coin_fetch = full_update(config, last_coin_fetch)
        config_write(config)
        return
    elif channel == 19 and button_pressed == 0:
        logging.info('Cycle fiat')
        button_pressed = 1
        fiat_list = currency_cycle(config['ticker']['fiatcurrency'])
        config['ticker']['fiatcurrency'] = ",".join(fiat_list)
        last_coin_fetch = full_update(config, last_coin_fetch)
        config_write(config)
        return
    return


def config_write(config):
    """
        Write the config file following an adjustment made using the buttons
        This is so that the unit returns to its last state after it has been
        powered off
    """
    # with open(configfile, 'w') as f:
    #   data = yaml.dump(config, f)
    #   Reset button pressed state after config is written
    global button_pressed
    button_pressed = 0


def full_update(config, last_coin_fetch):
    """
    The steps required for a full update of the display
    Earlier versions of the code didn't grab new data for some operations
    but the e-Paper is too slow to bother the coingecko API
    """
    other = {}
    try:
        price_stack, all_time_high = get_data(config, other)
        make_spark(price_stack)
        image = update_display(config, price_stack, other)
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


def config_to_coin_and_fiat(config):
    crypto_list = currency_string_to_list(config['ticker']['currency'])
    fiat_list = currency_string_to_list(config['ticker']['fiatcurrency'])
    currency = crypto_list[0]
    fiat = fiat_list[0]
    return currency, fiat


def get_trending(config):
    coin_list = config['ticker']['currency']
    url = "https://api.coingecko.com/api/v3/search/trending"
    #   Cycle must be true if trending mode is on
    config['display']['cycle'] = True
    trending_coins = requests.get(url, headers=headers).json()
    for i in range(0, (len(trending_coins['coins']))):
        print(trending_coins['coins'][i]['item']['id'])
        coin_list += "," + str(trending_coins['coins'][i]['item']['id'])
    config['ticker']['currency'] = coin_list
    return config


def main():
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

    try:
        logging.info("Build Frame")
        #       Get the configuration from config.yaml
        with open(configfile) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        logging.info(config)
        config['display']['orientation'] = int(config['display']['orientation'])
        static_coins = config['ticker']['currency']

        keys = init_keys()  # Set Up Buttons
        add_key_event(keys)  # Add Key Events
        how_many_coins = len(config['ticker']['currency'].split(","))

        data_pulled = False
        last_coin_fetch = time.time()

        #       Quick Sanity check on update frequency
        if float(config['ticker']['updatefrequency']) < 5:
            logging.info("Throttling update frequency to 5 seconds")
            update_frequency = 5.0
        else:
            update_frequency = float(config['ticker']['updatefrequency'])
            logging.debug("Update Frequency is " + str(update_frequency) + " seconds")
        while not internet():
            logging.info("Waiting for internet")
            time.sleep(1)
        while True:
            if config['display']['trendingmode']:
                # The hard-coded 7 is for the number of trending coins to show. Consider revising
                if (time.time() - last_coin_fetch > (7 + how_many_coins) * update_frequency) or not data_pulled:
                    # Reset coin list to static (non trending coins from config file)
                    config['ticker']['currency'] = static_coins
                    config = get_trending(config)
            logging.debug("Current time: " + str(time.time()))
            logging.debug("Last Fetch at: " + str(last_coin_fetch))
            logging.debug("Elapsed time since last fetch: " + str(time.time() - last_coin_fetch))
            logging.debug("Data_Pulled set to: " + str(data_pulled))
            if (time.time() - last_coin_fetch > update_frequency) or not data_pulled:
                if config['display']['cycle'] and data_pulled:
                    crypto_list = currency_cycle(config['ticker']['currency'])
                    config['ticker']['currency'] = ",".join(crypto_list)
                    config_write(config)
                last_coin_fetch = full_update(config, last_coin_fetch)
                data_pulled = True
            #           Reduces CPU load during that while loop
            time.sleep(0.01)
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
        image = bean_a_problem("Keyboard Interrupt")
        display_image(image)
        # epd2in7.epdconfig.module_exit()
        GPIO.cleanup()
        exit()


if __name__ == '__main__':
    main()
