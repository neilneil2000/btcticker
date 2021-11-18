import requests
import logging
import time

from config import params

class data:

    def __init__(self):        
        self.config = params()

        self.price_stack = []
        self.price_now = None
        
        self.coin = "bitcoin"
        self.fiat = "GBP"
        self.all_time_high_flag = False
        self.headers = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) \
                     Chrome/39.0.2171.95 Safari/537.36'}

    def get_pair(self,coin,fiat):
        self.coin = coin
        self.fiat = fiat
        self.refresh()
    
    def refresh(self):
        """
        Get Data From Coin Gecko
        """

        sleep_time = 10
        retries = 5

        logging.info("Getting Data")
        end_time = int(time.time())
        start_time = end_time - 60 * 60 * 24 * self.config.get_days()

        time_series_stack = []

        for x in range(0, retries):
            success = self.get_historical_data(start_time, end_time)
            if success:
                for time_value in self.raw_json['prices']:
                    time_series_stack.append(float(time_value[1]))
                time.sleep(0.1)
            
                # Get the price
                success = self.get_live_price()
                if success:
                    logging.debug(self.raw_json)
                    live_coin = self.raw_json[0]
                    self.price_now = float(live_coin['current_price'])
                
                    self.volume = float(live_coin['total_volume'])
                    time_series_stack.append(self.price_now)
                    
                    self.all_time_high = live_coin['ath']
                    self.check_all_time_high()
                    self.price_stack = time_series_stack
                    break
                else:
                    logging.warning("Trying again in " + sleep_time + " seconds")
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
        
        logging.debug(url)
        try:
            gecko_json = requests.get(url, headers=self.headers).json()
            connect_ok = True
            logging.debug("Got info from CoinGecko")
            self.raw_json = gecko_json
        except requests.exceptions.RequestException as e:
            logging.error("Issue with CoinGecko")
            connect_ok = False
            gecko_json = {}
        return connect_ok