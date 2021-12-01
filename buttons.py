import RPi.GPIO as GPIO
import time
import display
import logging
from config import Params

class Buttons:
    """
    Top level class controlling the function of buttons/GPIO
    """
    
    def __init__(self,params):
        self.bounce_time = 500
        self.buttons = [17,22,23]
        self.params = params
        self.callback_running = False
        GPIO.setmode(GPIO.BCM)
        for key in self.keys:
            GPIO.setup(key, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        for button in self.buttons:
            GPIO.add_event_detect(button, GPIO.FALLING, callback=self.button_press, bouncetime=self.bounce_time)


    def __del__(self):
        GPIO.cleanup()     


    def button_press(self,channel):
        while(self.callback_running):
            time.sleep(0.1)
        callback_running = True
        if channel == 17:
            logging.info('Cycle currencies')
            self.params.next_crypto()
        elif channel == 22:
            logging.info('Rotate - 90')
            display.set_orientation() = (display.get_orientation() + 90) % 360
        elif channel == 23:
            logging.info('Invert Display')
            display.invert_display()
        elif channel == 19:
            logging.info('Cycle fiat')
            display.Params.next_fiat()
        last_coin_fetch = full_update(last_coin_fetch) #TODO: Split Screen Update and Data Update to allow screen changes independent of changing currency
        Params.write_to_file()
        callback_running = False