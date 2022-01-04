#!/usr/bin/python3
import os
import time
import socket
import logging
import argparse

from display import Display
from config import Params


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
        my_socket = socket.create_connection((host, 80), 2)
        my_socket.close()
        return True
    except:
        logging.info("Google says No")
    return False


def main():
    # Check command line for logging level
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log", default="info", help="Set the log level (default: info)"
    )
    args = parser.parse_args()

    log_level = getattr(logging, args.log.upper(), logging.WARN)
    logging.basicConfig(level=log_level)
    logger = logging.getLogger("btcticker")
    # Set timezone based on ip address
    try:
        os.system("sudo /home/pi/.local/bin/tzupdate")
    except:
        logger.info("Timezone Not Set")

    config = Params()

    last_fetch_time = time.time() - config.update_frequency  # Force first update

    screen = Display()

    # my_buttons = Buttons()

    while not internet():
        logger.info("Waiting for internet")
        time.sleep(1)
    logger.debug("Entering Main Loop. Config.cycle= %s", str(config.cycle))
    try:
        if config.cycle:
            while True:
                if time.time() - last_fetch_time > config.update_frequency:
                    logger.debug("Fetching next slide...")
                    screen.next_slide()
                    last_fetch_time = time.time()
                time.sleep(0.1)

            while True:
                time.sleep(0.1)

    except IOError as e:
        logger.error(e)
        logger.debug(e.__traceback__.tb_lineno)
        screen.bean_a_problem(str(e) + " Line: " + str(e.__traceback__.tb_lineno))

    except Exception as e:
        logger.error(e)
        logger.debug("Line: %i", e.__traceback__.tb_lineno)
        screen.bean_a_problem(str(e) + " Line: " + str(e.__traceback__.tb_lineno))

    except KeyboardInterrupt:
        logger.info("ctrl + c:")
        exit()


if __name__ == "__main__":
    main()
