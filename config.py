import yaml
import os
import logging

class params:
    '''Config Class'''
    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yaml')
    

    def __init__(self,filename=config_file):
        self.config = {}
        self.read_from_file(filename)
        self.cryptos = self.string_to_list(self.config['ticker']['currency'])
        self.crypto_index = 0
        self.fiats = self.string_to_list(self.config['ticker']['fiatcurrency'])
        self.fiat_index = 0
        

    def read_from_file(self, filename=config_file):
        with open(filename, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        logging.debug(self.config)
        self.check_update_frequency()
 
    def write_to_file(self, filename=config_file):
        with open(filename, 'w') as f:
            yaml.dump(self.config, f)

    def get_cycle(self):
        if self.config['display']['cycle']:
            return True
        return False

    def get_cryptos(self):
        return self.cryptos

    def get_fiats(self):
        return self.fiats

    def get_days(self):
        return int(self.config['ticker']['sparklinedays'])

    def get_exchange(self):
        return self.config['ticker']['exchange']

    def next_item(self,list,index):
        next_index = index + 1
        if next_index >= list.len():
            next_index = 0
        return next_index

    def next_crypto(self):
        self.crypto_index = self.next_item(self.cryptos, self.crypto_index)
    
    def next_fiat(self):
        self.fiat_index = self.next_item(self.fiats, self.fiat_index)
    
    def get_update_frequency(self):
        self.check_update_frequency()
        return self.config['ticker']['updatefrequency']

    def check_update_frequency(self):
        # Quick Sanity check on update frequency
        if float(self.config['ticker']['updatefrequency']) < 5:
            self.config['ticker']['updatefrequency'] = 5.0

    def get_coin_and_fiat(self):        
        cryptos = self.string_to_list(self.config['ticker']['currency'])
        fiats = self.string_to_list(self.config['ticker']['fiatcurrency'])
        return cryptos[0], fiats[0]

    def string_to_list(self,string):
        list = string.split(",")
        list = [x.strip(' ') for x in list]
        return list

