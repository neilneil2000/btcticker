import RPi.GPIO as GPIO
import time
from display import Display
import logging
from config import Params

class Buttons:
    """
    Top level class controlling the function of buttons/GPIO
    """
    
    def __init__(self):
        self.logger = logging.getLogger("btcticker.buttons")
        self.bounce_time = 500
        self.buttons = [17,22,23]
        self.config = Params()
        self.callback_running = False
        self.screen = Display()
        GPIO.setmode(GPIO.BCM)
        for button in self.buttons:
            GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        for button in self.buttons:
            GPIO.add_event_detect(button, GPIO.FALLING, callback=self.button_press, bouncetime=self.bounce_time)


    def __del__(self):
        GPIO.cleanup()  

    def button_press(self,channel):
        while(self.callback_running):
            time.sleep(0.1)
        self.callback_running = True
        if channel == 17:
            self.logger.info('Cycle currencies')
            self.screen.next_slide
        elif channel == 22:
            self.logger.info('Rotate - 90')
            self.screen.set_orientation((self.screen.get_orientation() + 90) % 360)
        elif channel == 23:
            self.logger.info('Invert Display')
            self.screen.toggle_invert()
        self.callback_running = False   