import pytest
from btcticker import human_format

testdata = [(0.1, '0.100'),
            (0.10, '0.100'),
            (0.100, '0.100'),
            (0.01, '0.010'),
            (0.001, '0.001'),
            (1,'1.00'),
            (1.2,'1.20'),
            (1.23,'1.23'),
            (1.231, '1.23'),  
            (1000,'1K'),
            (4999,'4.999K'), 
            (5000,'5K')
]

@pytest.mark.parametrize("input,output",testdata)
def test_human_format(input, output):
    assert human_format(input) == output