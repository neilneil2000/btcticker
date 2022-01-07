import logging
import requests


class GeckoConnection:
    """Class to Connect to CoinGecko and get information"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) \\ AppleWebKit/537.36 (KHTML, like Gecko) \\ Chrome/39.0.2171.95 Safari/537.36"
    }

    logger = logging.getLogger("btcticker.gecko")
    response: requests.Response = None

    @classmethod
    def fetch_json(cls, url: str) -> bool:
        """Get JSON formatted data from Coingecko - e.g. a dataset"""
        return cls.fetch(url=url, stream=False)

    @classmethod
    def fetch_stream(cls, url: str) -> bool:
        """Get stream information from CoinGecko - e.g. an image"""
        return cls.fetch(url=url, stream=True)

    @classmethod
    def fetch(cls, url: str, stream: bool = False) -> int:
        """
        Get Info From CoinGecko
        Returns True on success, false on failure
        """
        cls.logger.debug("Fetching: %s", url)
        cls.response = requests.get(url=url, headers=cls.HEADERS, stream=stream)
        cls.logger.debug(
            "Got info from CoinGecko. Status Code %i",
            cls.response.status_code,
        )
        return cls.response.ok
