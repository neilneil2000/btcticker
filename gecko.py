import requests
import logging


class GeckoConnection:

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) \
                 Chrome/39.0.2171.95 Safari/537.36"
    }

    def __init__(self):
        self.logger = logging.getLogger("btcticker.gecko")
        self.raw_json = {}
        self.raw_stream = {}

    def fetch_data(self, url: str, stream: bool = False) -> bool:
        """
        Get Info From CoinGecko
        Returns True on success, false on failure
        """
        connect_ok = False
        self.logger.debug("Fetching: %s", url)
        try:
            gecko_response = requests.get(url, headers=self.HEADERS, stream=stream)
            self.logger.debug(
                "Data Requested. Status Code: %s", str(gecko_response.status_code)
            )
            if gecko_response["status_code"] == requests.codes["ok"]:
                connect_ok = True
                self.logger.debug("Got info from CoinGecko")
                if not stream:
                    self.logger.debug(gecko_response.json())
                    self.raw_json = gecko_response.json()
                else:
                    self.raw_stream = gecko_response.raw
        except requests.exceptions.RequestException as e:
            self.logger.error("Issue with CoinGecko")
            connect_ok = False
            self.raw_json = {}
        return connect_ok
