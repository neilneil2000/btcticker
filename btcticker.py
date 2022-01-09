#!/usr/bin/python3
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
        self.callback_request = None

    def callback_executor(self):
        """Function to Execute Requested Callbacks"""
        button_id = self.callback_request
        if button_id == 17:
            self.screen.inverted = not self.screen.inverted
            self.refresh(False)
        elif button_id == 22:
            self.refresh()
        elif button_id == 23:
            pass

    def callback_manager(self, button: Button) -> None:
        """Handle Callbacks from Button Press"""
        self.callback_request = button.pin.number

    def refresh(self, next: bool = True) -> None:
        """Get new data and update screen"""
        self.last_fetch_time = time.time()
        if next:
            self.data_manager.next_crypto()
        data = self.data_manager.refresh()
        self.screen.display(data)

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

        self.my_buttons = Buttons()
        self.my_buttons.initialise()
        self.my_buttons.configure_button(17, self.callback_manager)
        self.my_buttons.configure_button(22, self.callback_manager)
        self.my_buttons.configure_shutdown_button(23)
        # my_buttons.configure_button(23, next_crypto)

    def run(self):
        """Run the ticker"""
        self.refresh(False)
        while True:
            time.sleep(0.1)
            if self.callback_request is not None:
                self.callback_executor()
                self.callback_request = None
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
        quit()


if __name__ == "__main__":
    main()
