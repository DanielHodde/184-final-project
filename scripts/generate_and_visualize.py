"""
Script to generate and visualize terrain using Perlin noise and PyVista.
"""

# Ensure the project root is on sys.path so 'terrain' is importable
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from terrain.generation.perlin import generate_perlin_noise
from terrain.generation.fractal_perlin import generate_fractal_perlin_noise
from terrain.visualization.pyvista_vis import plot_terrain, add_trees_to_plotter


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

def generate_and_visualize_terrain_with_trees():
    """
    Example: Generate terrain, tree density map, and visualize with trees.
    """
    # Generate terrain
    terrain = generate_fractal_perlin_noise(shape=(512, 512), scale=20, octaves=5) * 100
    # Generate tree density map (different scale for variety)
    tree_density = generate_fractal_perlin_noise(shape=terrain.shape, scale=15, octaves=3)
    tree_density = (tree_density - tree_density.min()) / (tree_density.max() - tree_density.min())
    # Visualize terrain
    plotter, _ = plot_terrain(terrain, show=False)
    # Add trees
    # Render fewer, smaller trees for testing
    add_trees_to_plotter(
        plotter, terrain, tree_density,
        tree_threshold=0.9,  # Higher threshold = fewer trees
        max_tree_height=80,
        tree_height=3,
        tree_radius=0.7,
        tree_color="forestgreen",
        seed=42,
        # cone_resolution=48 
    )
    plotter.show()

def generate_and_visualize_single_tree_example():
    """
    Example usage: Visualize terrain and add a single tree at the center.
    """
    from terrain.visualization.pyvista_vis import add_single_tree_to_plotter
    # Generate terrain
    terrain = generate_fractal_perlin_noise(shape=(512, 512), scale=20, octaves=5) * 100
    plotter, _ = plot_terrain(terrain, show=False)
    # Add a single tree at the center
    add_single_tree_to_plotter(plotter, terrain, tree_height=5, tree_radius=1, tree_color="red")
    plotter.show()

if __name__ == "__main__":
    main()
    # generate_and_visualize_large_terrain()
    # generate_and_visualize_fractal_terrain()
    generate_and_visualize_terrain_with_trees()
    # generate_and_visualize_single_tree_example()
