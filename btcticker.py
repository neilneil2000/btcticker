#!/usr/bin/python3
import sys
import time
import logging
import argparse

from gpiozero import Button

from display import Display, AdaFruitDisplay
from config import Params
from data_manager import DataManager
from buttons import Buttons


class CryptoTicker:
    def __init__(self):
        # TODO: Allow to pass in types of screen and exchange using Bridge method and abc classes
        self.config: Params = None
        self.data_manager: DataManager = None
        self.screen: Display = None
        self.my_buttons: Buttons = None
        self.logger: logging.Logger = None
        self.last_fetch_time: float = None
        self.callback_button_number = None

    def callback_executor(self):
        """Function to Execute Requested Callbacks"""
        button_action = ""
        for button_action, button_number in self.config.buttons.items():
            if button_number == self.callback_button_number:
                break
        if button_action == "invert":
            self.screen.inverted = not self.screen.inverted
            self.refresh(False)
        elif button_action == "next_crypto":
            self.refresh()

        self.callback_button_number = None

    def callback_manager(self, button: Button) -> None:
        """Handle Callbacks from Button Press"""
        self.callback_button_number = button.pin.number

    def refresh(self, next_crypto: bool = True) -> None:
        """Get new data and update screen"""
        self.last_fetch_time = time.time()
        if next_crypto:
            self.data_manager.next_crypto()
        if self.data_manager.refresh():
            self.screen.display(self.data_manager.data)

    def initialise(self):
        """Initialise Ticker"""
        self.logger = logging.getLogger("btcticker")
        self.config = Params()
        self.data_manager = DataManager(
            data_period_days=self.config.days,
            coins=self.config.cryptos,
            fiats=self.config.fiats,
        )
        self.screen = AdaFruitDisplay(
            orientation=self.config.orientation,
            inverted=self.config.inverted,
            colour=self.config.colour,
        )
        self.screen.initialise()

        if not self.config.buttons:
            return
        self.my_buttons = Buttons()
        self.my_buttons.initialise()
        for action, number in self.config.buttons.items():
            if action == "shutdown":
                self.my_buttons.configure_shutdown_button(number)
            else:
                self.my_buttons.configure_button(number, self.callback_manager)

    def run(self):
        """Run the ticker"""
        self.refresh(next_crypto=False)
        while True:
            time.sleep(0.1)
            if self.callback_button_number is not None:
                self.callback_executor()
            if time.time() - self.last_fetch_time > self.config.update_frequency:
                if self.config.cycle:
                    self.data_manager.next_crypto()
                self.refresh()


def setup_logger() -> None:
    """Set Log Level from Input Args"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log", default="info", help="Set the log level (default: info)"
    )
    args = parser.parse_args()

    log_level = getattr(logging, args.log.upper(), logging.WARN)
    logging.basicConfig(level=log_level)


def main():

    setup_logger()
    app = CryptoTicker()
    app.initialise()
    try:
        app.run()
    except KeyboardInterrupt:
        print("ctrl + c...")
        sys.exit()


if __name__ == "__main__":
    main()
