"""
Script to visualize pure Perlin noise as a grayscale image (not as terrain) for debugging/analysis.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from terrain.generation.perlin import generate_perlin_noise
from terrain.visualization.noise_image import plot_noise_image


# This script visualizes Perlin noise as a 2D image (not 3D terrain)
def main():
    noise = generate_perlin_noise()
    plot_noise_image(noise, cmap="gray", title="Perlin Noise (Grayscale)")


if __name__ == "__main__":
    main()
