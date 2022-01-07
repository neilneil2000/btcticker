import os
import logging
import pygame

import matplotlib as mpl

from config import Params
from image import Slide
from data import CoinData


class Display:
    """
    Top Level Class Providing the Following Functions:
     - refresh_slide()  Reload Existing Image - to account for any changes in settings since last load
     - next_slide()     Get information and render next slide
     - toggle_invert()  Toggle Inversion
     - rotate()         Rotate screen 90 degress clockwise
     - show_error()     Show Error Screen
    """

    def __init__(self, width: int = 320, height: int = 240) -> None:

        self.logger = logging.getLogger("btcticker.display")

        os.putenv(
            "SDL_FBDEV", "/dev/fb0"
        )  # Set Output to PiTFT - Could be fb1 if desktop installed
        os.putenv("SDL_AUDIODRIVER", "dsp")  # Prevent ALSA errors in PyGame

        self.pic_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "images"
        )
        self.font_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "fonts/googlefonts"
        )

        mpl.use("Agg")

        self.width = width
        self.height = height

        pygame.init()
        self.logger.debug(
            "Pygame Initialised. Setting display width: %i Height: %i",
            self.width,
            self.height,
        )
        self.lcd = pygame.display.set_mode((self.width, self.height))
        self.logger.debug("Pygame Display Mode Set")
        pygame.mouse.set_visible(False)

        self.logger.debug("Pygame Started, now opening config file")
        self.config = Params()
        self.slide = Slide()
        self.my_data = DataManager()

        self.cryptos = self.config.cryptos
        self.fiats = self.config.fiats
        self.crypto_index = len(self.cryptos) - 1
        self.fiat_index = len(self.fiats) - 1

        self.logger.debug("Display Class Initialised, returning...")

    def __del__(self):
        pygame.quit()

    def get_orientation(self) -> int:
        return self.config.config["display"]["orientation"]

    def set_orientation(self, angle: int) -> None:
        self.config.config["display"]["orientation"] = angle
        self.slide.refresh()

    def toggle_invert(self) -> None:
        self.config.config["display"]["inverted"] = not self.config.config["display"][
            "inverted"
        ]
        self.slide.refresh()

    def update(self, img) -> None:
        img = img.convert("RGB")
        py_image = pygame.image.fromstring(img.tobytes(), img.size, img.mode).convert()
        self.lcd.blit(py_image, (0, 0))
        pygame.display.update()

    def next_pairing(self) -> bool:
        """
        Change Pointer to point to next crypto
        """
        if self.crypto_index + 1 >= len(self.cryptos):
            self.crypto_index = 0
        else:
            self.crypto_index += 1
        coin = self.cryptos[self.crypto_index]
        fiat = self.fiats[self.fiat_index]
        self.logger.debug("Getting Pairing: " + coin + " " + fiat)
        return self.my_data.fetch_pair(coin, fiat)

    def next_slide(self) -> None:
        if self.next_pairing():
            self.logger.debug("Pairing Ready, now generating slide")
            image = self.slide.generate_slide(
                self.my_data,
                self.config.days,
                inverted=self.config.inverted,
                orientation=self.config.orientation,
                colour=self.config.colour,
            )
        else:
            image = self.slide.bean_a_problem("Error Getting Pairing")
        self.update(image)

    def bean_a_problem(self, message) -> None:
        image = self.slide.bean_a_problem(message)
        self.update(image)
