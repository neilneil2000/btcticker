#!/usr/bin/python3
import os
import time
import socket
import logging
import argparse

from display import display
from config import params

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


def main():
    # Check command line for logging level
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default='info', help='Set the log level (default: info)')
    args = parser.parse_args()

    log_level = getattr(logging, args.log.upper(), logging.WARN)
    logging.basicConfig(level = log_level)
    logger = logging.getLogger("btcticker")
    # Set timezone based on ip address
    try:
        os.system("sudo /home/pi/.local/bin/tzupdate")
    except:
        logger.info("Timezone Not Set")

    
    config = params()

    update_frequency = config.get_update_frequency()
    last_fetch_time = time.time() - update_frequency #Force first update

    screen = display()

    while not internet():
        logger.info("Waiting for internet")
        time.sleep(1)

    try:
        if config.get_cycle():
            while True:
                if (time.time() - last_fetch_time > update_frequency):
                    screen.next_slide()
                    last_fetch_time = time.time()
                time.sleep(0.1)
        else:
            while True:
                time.sleep(0.1)

    except IOError as e:
        logger.error(e)
        logger.debug(e.__traceback__.tb_lineno)
        screen.bean_a_problem(str(e) + " Line: " + str(e.__traceback__.tb_lineno))
    
    # except Exception as e:
    #     logger.error(e)
    #     logger.debug("Line: " + str(e.__traceback__.tb_lineno))
    #     screen.bean_a_problem(str(e) + " Line: " + str(e.__traceback__.tb_lineno))
    
    except KeyboardInterrupt:
        logger.info("ctrl + c:")
        exit()


if __name__ == '__main__':
    main()
