import requests
import logging
import time

from config import params

class data:

    HEADERS = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) \
                     Chrome/39.0.2171.95 Safari/537.36'}

    SLEEP_TIME = 10
    RETRIES = 5

    def __init__(self):        
        self.logger = logging.getLogger("btcticker.display.data")
        self.config = params()

        self.price_stack = []
        self.price_now = None
        
        self.coin = ""
        self.fiat = ""
        self.all_time_high_flag = False

        self.raw_json = {}


    def fetch_pair(self,coin,fiat):
        self.coin = coin
        self.fiat = fiat
        self.refresh()
    

    def refresh(self):
        """
        Get Data From Coin Gecko
        """
        sleep_time = data.SLEEP_TIME

        self.logger.info("Getting Data")
        end_time = int(time.time())
        start_time = end_time - 60 * 60 * 24 * self.config.get_days()

        self.price_stack = []

        for x in range(0, data.RETRIES):
            success = self.get_historical_data(start_time, end_time)
            if success:
                self.logger.debug(self.raw_json)
                self.logger.debug(type(self.raw_json))
                for time_value in self.raw_json['prices']:
                    self.price_stack.append(float(time_value[1]))
                time.sleep(0.1)
            
                # Get the price
                success = self.get_live_price()
                if success:
                    self.logger.debug(self.raw_json)
                    live_coin = self.raw_json[0]
                    self.price_now = float(live_coin['current_price'])
                
                    self.volume = float(live_coin['total_volume'])
                    self.price_stack.append(self.price_now)
                    
                    self.all_time_high = live_coin['ath']
                    self.check_all_time_high()
                    self.logger.debug("Price Now:\t\t" + str(self.price_now))
                    self.logger.debug("All Time High:\t" + str(self.all_time_high))
                    self.logger.debug("Volume:\t\t" + str(self.volume))
                    break
                else:
                    self.logger.warning("Trying again in " + sleep_time + " seconds")
                    time.sleep(sleep_time)  # wait before trying to fetch the data again
                    sleep_time = min(sleep_time*2, 3600) #exponential backoff


    def check_all_time_high(self):
        if self.price_now > self.all_time_high:
            self.all_time_high_flag = True
        else:
            self.all_time_high_flag = False


    def get_price_stack(self):
        return self.price_stack


    def get_live_price(self):
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=" + self.fiat + "&ids=" + self.coin
        return self.get_gecko(url)
        

    def get_historical_data(self,start_time, end_time):
        url = "https://api.coingecko.com/api/v3/coins/" + self.coin + \
                    "/market_chart/range?vs_currency=" + self.fiat + "&from=" + str(start_time) + \
                    "&to=" + str(end_time)
        return self.get_gecko(url)
    

    def get_gecko(self,url):
        """
        Get Info From CoinGecko
        Returns True on success, false on failure
        """
        connect_ok = False
        self.logger.debug("Fetching: " + url)
        try:
            gecko_response = requests.get(url, headers=data.HEADERS)
            if gecko_response.status_code == 200:
                connect_ok = True
                self.logger.debug("Got info from CoinGecko")
                self.raw_json = gecko_response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error("Issue with CoinGecko")
            connect_ok = False
            self.raw_json = {}
        return connect_ok