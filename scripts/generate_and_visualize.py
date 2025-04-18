"""
Script to generate and visualize terrain using Perlin noise and PyVista.
"""

# Ensure the project root is on sys.path so 'terrain' is importable
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from terrain.generation.perlin import generate_perlin_noise
from terrain.generation.fractal_perlin import generate_fractal_perlin_noise
from terrain.visualization.pyvista_vis import plot_terrain


def main():
    # Generate terrain
    terrain = generate_perlin_noise(scale=8)
    terrain *= 15
    # Visualize terrain
    plot_terrain(terrain)


def generate_and_visualize_large_terrain():
    """
    Generate and visualize a larger terrain (2048x2048) using Perlin noise and PyVista.
    """
    # Generate larger terrain
    terrain = generate_perlin_noise(shape=(2048, 2048), scale=10)
    terrain *= 100  # Scale heights for better visualization
    plot_terrain(terrain)

def generate_and_visualize_fractal_terrain():
    """
    Generate and visualize a fractal Perlin noise terrain using multiple octaves.
    """
    terrain = generate_fractal_perlin_noise(shape=(2048, 2048), scale=50, octaves=6,
                                            persistence=0.5, lacunarity=2.0, zoom=15.0)
    terrain *= 500  # Scale heights for better visualization
    plot_terrain(terrain)

if __name__ == "__main__":
    main()
    # Uncomment the line below to generate and visualize a large terrain
    # generate_and_visualize_large_terrain()
    # Uncomment the line below to generate and visualize a fractal terrain
    generate_and_visualize_fractal_terrain()
