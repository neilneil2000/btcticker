import pytest
from image import Slide

testdata = [
    (0.1, "0.100"),
    (0.10, "0.100"),
    (0.100, "0.100"),
    (0.01, "0.010"),
    (0.001, "0.001"),
    (1, "1.00"),
    (1.2, "1.20"),
    (1.23, "1.23"),
    (1.231, "1.23"),
    (1000, "1K"),
    (4999, "4.999K"),
    (5000, "5K"),
]


@pytest.mark.parametrize("raw,formatted", testdata)
def test_human_format(raw, formatted):
    test_image = Slide()
    assert test_image.human_format(raw) == formatted
