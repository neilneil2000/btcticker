import io
from statistics import mean
from typing import List

from matplotlib import pyplot
from PIL import Image


class SparkLine:
    """
    Class representing the Small Graph (aka Sparkline)
    """

    @staticmethod
    def generate_spark(data: List[float]) -> Image.Image:
        """Draw and save the sparkline that represents historical data"""
        mean_value = mean(data)
        offset_data = [value - mean_value for value in data]  # Make x-axis = mean
        fig, axis = pyplot.subplots(1, 1, figsize=(14, 6))
        pyplot.plot(offset_data, color="k", linewidth=6)
        pyplot.plot(len(offset_data) - 1, offset_data[-1], color="r", marker="o")
        # Remove the Y axis
        for _, v in axis.spines.items():
            v.set_visible(False)
        axis.set_xticks([])
        axis.set_yticks([])
        axis.axhline(c="k", linewidth=4, linestyle=(0, (5, 2, 1, 2)))

        buf = io.BytesIO()
        pyplot.savefig(buf, format="png", dpi=17)
        pyplot.close(fig)
        pyplot.cla()  # Close plot to prevent memory error
        axis.cla()  # Close axis to prevent memory error
        buf.seek(0)
        return Image.open(buf)
