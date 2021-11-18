import os
import matplotlib.pyplot as plt
from PIL import Image

class spark:
    """
    Class representing the Small Graph (aka Sparkline)
    """

    def __init__(self, pic_dir):
        self.pic_dir = pic_dir
        pass
    
    def make_spark(self, price_stack):
        # Draw and save the sparkline that represents historical data
        # Subtract the mean from the sparkline to make the mean appear on the plot (it's really the x axis)
        mean = sum(price_stack) / float(len(price_stack))
        x = [xx - mean for xx in price_stack]
        fig, ax = plt.subplots(1, 1, figsize=(14, 6))
        plt.plot(x, color='k', linewidth=6)
        plt.plot(len(x) - 1, x[-1], color='r', marker='o')
        # Remove the Y axis
        for k, v in ax.spines.items():
            v.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axhline(c='k', linewidth=4, linestyle=(0, (5, 2, 1, 2)))
        # Save the resulting bmp file to the images directory
        plt.savefig(os.path.join(self.pic_dir, 'spark.png'), dpi=17)
        img_sparkline = Image.open(os.path.join(self.pic_dir, 'spark.png'))
        file_out = os.path.join(self.pic_dir, 'spark.bmp')
        img_sparkline.save(file_out)
        plt.close(fig)
        plt.cla()  # Close plot to prevent memory error
        ax.cla()  # Close axis to prevent memory error
        img_sparkline.close()