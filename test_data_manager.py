import os
from PIL import Image
import pytest

from data_manager import DataManager


@pytest.fixture
def simple_data_man():
    return DataManager(7, ["bitcoin"], ["GBP"])


@pytest.mark.parametrize("bg_colour", ["black", "white"])
def test_fetch_image(bg_colour, simple_data_man):
    token_filename = "currency/bitcoin_" + bg_colour + ".bmp"
    token_filename = os.path.join(simple_data_man.PIC_DIR, token_filename)
    assert simple_data_man.fetch_token_image(token_filename, bg_colour)


@pytest.mark.parametrize("colour", [(255, 255, 255), (0, 0, 0)])
def test_get_background_colour_true(colour, simple_data_man):
    image = Image.new(mode="RGB", size=(10, 10), color=colour)
    result = simple_data_man.get_background_colour(image)
    assert result == colour


def test_get_background_colour_true_corner_case(simple_data_man):
    image = Image.new(mode="RGB", size=(10, 10), color=(0, 0, 0))
    pixels = image.load()
    for pixel in [(0, 0), (0, -1), (-1, 0), (-1, -1)]:
        x, y = pixel
        pixels[x, y] = (5, 5, 5)
    result = simple_data_man.get_background_colour(image)
    assert result == (5, 5, 5)


@pytest.mark.parametrize(
    "pixels_to_change", [[(0, 0)], [(0, -1)], [(-1, 0)], [(-1, -1)], [(0, 0), (-1, -1)]]
)
def test_get_background_colour_false(pixels_to_change, simple_data_man):

    image = Image.new(mode="RGB", size=(10, 10), color=(0, 0, 0))
    pixels = image.load()
    for pixel in pixels_to_change:
        x, y = pixel
        pixels[x, y] = (5, 5, 5)
    result = simple_data_man.get_background_colour(image)
    assert not result
