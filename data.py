import logging
import time

from config import Params
from gecko import GeckoConnection

class Data:

    SLEEP_TIME = 10
    RETRIES = 5

    def __init__(self):        
        self.logger = logging.getLogger("btcticker.display.data")
        self.config = Params()

        self.price_stack = []
        self.price_now = None
        
        self.coin = ""
        self.fiat = ""
        self.all_time_high_flag = False

        self.gecko = GeckoConnection()


    def fetch_pair(self,coin,fiat):
        self.coin = coin
        self.fiat = fiat
        return self.refresh()
    

    def refresh(self):
        """
        Get Data From Coin Gecko
        """
        sleep_time = Data.SLEEP_TIME

        self.logger.debug("Getting Data")
        end_time = int(time.time())
        start_time = end_time - 60 * 60 * 24 * self.config.days

        self.price_stack = []

        success = False

        for x in range(0, Data.RETRIES):
            success = self.fetch_historical_data(start_time, end_time)
            if success:
                for time_value in self.gecko.raw_json['prices']:
                    self.price_stack.append(float(time_value[1]))
                time.sleep(0.1)
            
                # Get the price
                success = self.fetch_live_price()
                if success:
                    live_coin = self.gecko.raw_json[0]
                    self.price_now = float(live_coin['current_price'])
                
                    self.volume = float(live_coin['total_volume'])
                    self.price_stack.append(self.price_now)
                    
                    self.all_time_high = live_coin['ath']
                    self.check_all_time_high()
                    break
            else:
                self.logger.warning("Error Getting Data. Trying again in " + str(sleep_time) + " seconds")
                time.sleep(sleep_time)  # wait before trying to fetch the data again
                sleep_time = min(sleep_time*2, 3600) #exponential backoff
        return success


    def check_all_time_high(self):
        if self.price_now > self.all_time_high:
            self.all_time_high_flag = True
        else:
            self.all_time_high_flag = False


    def fetch_live_price(self):
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=" + self.fiat + "&ids=" + self.coin
        return self.gecko.fetch_data(url)
        

    def fetch_historical_data(self,start_time, end_time):
        url = "https://api.coingecko.com/api/v3/coins/" + self.coin + \
                    "/market_chart/range?vs_currency=" + self.fiat + "&from=" + str(start_time) + \
                    "&to=" + str(end_time)
        return self.gecko.fetch_data(url)