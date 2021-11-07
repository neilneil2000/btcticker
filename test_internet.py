import pytest
from btcticker import internet

testdata = [('www.google.com', True),
            ('doesnotexist.neil', False)
]

@pytest.mark.parametrize('web_address, outcome', testdata)
def test_internet(web_address, outcome):
    assert internet(web_address) == outcome

def test_internet_blank_input():
    assert internet() == True