#!/usr/bin/python3
import os
import time
import logging
import argparse

from display import Display
from config import Params
from data import DataManager


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

    data_manager = DataManager(
        data_period_days=config.days, coins=config.cryptos, fiats=config.fiats
    )
    # screen = Display()
    # my_buttons = Buttons()

    data_manager.refresh()
    #screen.display()
    try:
        while True:
            if time.time() - last_fetch_time > config.update_frequency and config.cycle:
                data_manager.next_crypto()
                data_manager.refresh()
                # screen.next_slide()
                last_fetch_time = time.time()

    except IOError as e:
        logger.error(e)
        logger.debug(e.__traceback__.tb_lineno)
        # screen.bean_a_problem(str(e) + " Line: " + str(e.__traceback__.tb_lineno))

    except Exception as e:
        logger.error(e)
        logger.debug("Line: %i", e.__traceback__.tb_lineno)
        # screen.bean_a_problem(str(e) + " Line: " + str(e.__traceback__.tb_lineno))

    except KeyboardInterrupt:
        logger.info("ctrl + c:")
        exit()


if __name__ == "__main__":
    main()
