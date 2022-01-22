import datetime
import logging
import requests


class GeckoConnection:
    """Class to Connect to CoinGecko and get information"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) \\ AppleWebKit/537.36 (KHTML, like Gecko) \\ Chrome/39.0.2171.95 Safari/537.36"
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.response: requests.Response = None
        self.timeout = (3, 8)

    def fetch_json(self, url: str) -> bool:
        """Get JSON formatted data from Coingecko - e.g. a dataset"""
        return self.fetch(url=url, stream=False)

    def fetch_stream(self, url: str) -> bool:
        """Get stream information from CoinGecko - e.g. an image"""
        return self.fetch(url=url, stream=True)

    def fetch(self, url: str, stream: bool = False) -> int:
        """
        Get Info From CoinGecko
        Returns True on success, false on failure
        """
        self.logger.debug("Fetching: %s", url)
        try:
            self.response = requests.get(
                url=url, headers=self.HEADERS, stream=stream, timeout=self.timeout
            )
        except (requests.ConnectionError, requests.ConnectTimeout) as e:
            print(f"{str(datetime.datetime.now())} CONNECTION ERROR!")
            print(e)
            return False
        self.logger.debug(
            "Got info from CoinGecko. Status Code %i",
            self.response.status_code,
        )
        return self.response.ok
