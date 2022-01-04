import os
from typing import List
from statistics import mean
from matplotlib import pyplot
from PIL import Image


class Spark:
    """
    Class representing the Small Graph (aka Sparkline)
    """

    def __init__(self, pic_dir: str) -> None:
        self.pic_dir = pic_dir

    def make_spark(self, price_stack: List[float]) -> None:
        """Draw and save the sparkline that represents historical data"""

        if not price_stack:
            return
        mean_price = mean(price_stack)
        adjusted_price = [
            price - mean_price for price in price_stack
        ]  # Make x-axis = mean
        fig, axis = pyplot.subplots(1, 1, figsize=(14, 6))
        pyplot.plot(adjusted_price, color="k", linewidth=6)
        pyplot.plot(len(adjusted_price) - 1, adjusted_price[-1], color="r", marker="o")
        # Remove the Y axis
        for _, v in axis.spines.items():
            v.set_visible(False)
        axis.set_xticks([])
        axis.set_yticks([])
        axis.axhline(c="k", linewidth=4, linestyle=(0, (5, 2, 1, 2)))
        # Save the resulting bmp file to the images directory
        pyplot.savefig(os.path.join(self.pic_dir, "spark.png"), dpi=17)
        img_sparkline = Image.open(os.path.join(self.pic_dir, "spark.png"))
        file_out = os.path.join(self.pic_dir, "spark.bmp")
        img_sparkline.save(file_out)
        pyplot.close(fig)
        pyplot.cla()  # Close plot to prevent memory error
        axis.cla()  # Close axis to prevent memory error
        img_sparkline.close()
