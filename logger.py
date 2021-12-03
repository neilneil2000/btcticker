import logging

class log:
    def __init__(self):
        self.set_logging_level()

    def set_logging_level(self,log_level):
        log_level = getattr(logging, log_level, logging.WARN)
        logging.basicConfig(level = log_level)