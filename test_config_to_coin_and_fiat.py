from btcticker import config_to_coin_and_fiat
from mock import patch

config = {'ticker': {'currency': 'cabbage,babbage', 'fiatcurrency': 'gbp,usd'}}

@patch('btcticker.config',config)
def test_config_to_coin_and_fiat():
    coin, fiat = config_to_coin_and_fiat()
    assert  coin == 'cabbage' and fiat == 'gbp'