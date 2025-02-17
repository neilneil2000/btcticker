import logging
import pygame
from gpiozero import Button, GPIOZeroError, GPIOZeroWarning
from subprocess import check_call


class Buttons:
    """
    Top level class controlling the function of buttons/GPIO
    """

    def __init__(self, bounce_time: float = 0.1):
        self.logger: logging.Logger = None
        self.bounce_time = bounce_time
        self.buttons = []

    def initialise(self):
        """Initialise Buttons"""
        self.logger = logging.getLogger("btcticker.buttons")

    def configure_button(self, button_id: int, callback) -> None:
        """Configure a specific button"""
        try:
            new_button = Button(button_id, bounce_time=self.bounce_time)
        except GPIOZeroError as e:
            self.logger.error("Error Setting Pin %s: %s", str(button_id), str(e))
        else:
            new_button.when_pressed = callback
            self.buttons.append(new_button)

    def configure_shutdown_button(self, button_id) -> None:
        """Configure a button to shutdown the pi"""
        try:
            shutdown_button = Button(button_id, hold_time=2)
        except GPIOZeroError as e:
            self.logger.error("Error Setting Pin %s: %s", str(button_id), str(e))
        else:
            shutdown_button.when_held = self.shutdown
            self.buttons.append(shutdown_button)

    def shutdown(self) -> None:
        """Shutdown Pi"""
        print("Shutdown Button Held Down...powering off")
        pygame.quit()  # This turns the screen off to display the shutdown
        check_call(["sudo", "poweroff"])
