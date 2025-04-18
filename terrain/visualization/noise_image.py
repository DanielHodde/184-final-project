"""
Visualization of 2D noise arrays as images using matplotlib.
"""

import numpy as np
import matplotlib.pyplot as plt

def plot_noise_image(noise_array, cmap='gray', title='Noise Image'):
    """
    Visualize a 2D noise array as an image using matplotlib.
    Args:
        noise_array (np.ndarray): 2D array of noise values.
        cmap (str): Matplotlib colormap.
        title (str): Plot title.
    """
    if not isinstance(noise_array, np.ndarray) or noise_array.ndim != 2:
        raise ValueError("Input must be a 2D numpy array.")
    plt.figure(figsize=(6,6))
    plt.imshow(noise_array, cmap=cmap, interpolation='nearest')
    plt.title(title)
    plt.axis('off')
    plt.show()
