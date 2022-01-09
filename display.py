import os
import logging
import pygame

from abc import ABC, abstractmethod

import matplotlib as mpl
from PIL import Image

from image import Slide
from data import CoinData


class Display(ABC):
    @abstractmethod
    def initialise(self) -> None:
        """Set up Display ready to display first image"""

    @abstractmethod
    def toggle_inversion(self) -> None:
        """Toggle Image Inversion and refresh screen"""

    @abstractmethod
    def display(self, data: CoinData) -> None:
        """Update Display to reflect data"""

    @abstractmethod
    def refresh(self) -> None:
        """Refresh Display with current settings"""


class AdaFruitDisplay(Display):
    """
    Top Level Class Providing the Following Functions:
     - refresh_slide()  Reload Existing Image - to account for any changes in settings since last load
     - next_slide()     Get information and render next slide
     - toggle_invert()  Toggle Inversion
     - rotate()         Rotate screen 90 degress clockwise
     - show_error()     Show Error Screen
    """

    def __init__(
        self,
        orientation: int = 90,
        inverted: bool = False,
        colour: bool = False,
    ) -> None:

        self.width: int = 320
        self.height: int = 240
        self.orientation: int = orientation
        self.inverted: bool = inverted
        self.colour: bool = colour
        self.logger: logging.Logger = None
        self.lcd: pygame.Surface = None

        self.pic_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "images"
        )
        self.font_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "fonts/googlefonts"
        )

    def initialise(self) -> None:
        """Set Up Environment and start running"""
        self.logger = logging.getLogger("btcticker.display")
        pygame.init()
        self.lcd = pygame.display.set_mode((self.width, self.height))
        pygame.mouse.set_visible(False)

        os.putenv(
            "SDL_FBDEV", "/dev/fb0"
        )  # Set Output to PiTFT - Could be fb1 if desktop installed
        os.putenv("SDL_AUDIODRIVER", "dsp")  # Prevent ALSA errors in PyGame

        mpl.use("Agg")

    def invert(self, button_id=0) -> None:
        print("Inversion Callback Running")
        self.toggle_inversion()
        self.refresh()

    def display(self, data: CoinData) -> None:
        """Display Image representing data"""

        slide = Slide(
            size=(self.width, self.height),
            orientation=self.orientation,
            inverted=self.inverted,
            colour=self.colour,
        )
        image = slide.generate_slide(data)
        self.show_pillow_image(image)

    def __del__(self):
        pygame.quit()

    def toggle_inversion(self) -> None:
        """Toggle Screen colour inversion"""
        self.inverted = not self.inverted
        self.refresh()

    def show_pillow_image(self, img: Image) -> None:
        """Display PIL Image object on screen"""
        img = img.convert("RGB")
        py_image = pygame.image.fromstring(img.tobytes(), img.size, img.mode).convert()
        self.lcd.blit(py_image, (0, 0))
        pygame.display.update()

    def refresh(self) -> None:
        """Refresh Image with current settings"""

    def bean_a_problem(self, message) -> None:
        """Display Error Message on Screen"""
        problem_slide = Slide(
            size=(self.width, self.height),
            orientation=self.orientation,
            inverted=self.inverted,
            colour=self.colour,
        )
        image = problem_slide.bean_a_problem(message)
        self.show_pillow_image(image)
