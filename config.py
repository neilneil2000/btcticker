import yaml
import os
import logging

class Params:
    '''Config Class'''
    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yaml')
    

    def __init__(self,filename=config_file):
        self.logger = logging.getLogger("btcticker.config")
        self.config = {}
        self.read_from_file(filename)
        self.parse_config_file()
        self.crypto_index = 0
        self.fiat_index = 0


    def parse_config_file(self):
        self.cryptos = self.string_to_list(self.config['ticker']['currency'])
        self.fiats = self.string_to_list(self.config['ticker']['fiatcurrency'])
        if self.config['display']['cycle'] == "True":
            self.cycle = True
        else:
            self.cycle = False
        self.cycle = self.config['display']['cycle']
        self.days = int(self.config['ticker']['sparklinedays'])
        self.exchange =  self.config['ticker']['exchange']
        self.orientation =  self.config['display']['orientation']
        self.colour = self.config['display']['colour']
        self.inverted = self.config['display']['inverted']
        self.update_frequency = max(5.0,float(self.config['ticker']['updatefrequency']))


    def read_from_file(self, filename=config_file):
        with open(filename, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        self.logger.debug(self.config)


    def write_to_file(self, filename=config_file):
        with open(filename, 'w') as f:
            yaml.dump(self.config, f)


    def next_item(self,list,index):
        next_index = index + 1
        if next_index >= list.len():
            next_index = 0
        return next_index


    def next_crypto(self):
        self.crypto_index = self.next_item(self.cryptos, self.crypto_index)


    def next_fiat(self):
        self.fiat_index = self.next_item(self.fiats, self.fiat_index)


    def string_to_list(self,string):
        list = string.split(",")
        list = [x.strip(' ') for x in list]
        return list

