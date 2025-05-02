import numpy as np
import pyvista as pv
from scipy import ndimage
# need to do noise generation using generate_perlin_noise and generate_fractal_perlin_noise
from noise import snoise2
import tensorflow as tf
from tensorflow import keras

# Set random seed for reproducibility
np.random.seed(42)


def generate_terrain(size=128, octaves=6, persistence=0.5, lacunarity=2.0):
    """Generate a fractal terrain using Perlin noise"""

    terrain = np.zeros((size, size))

    # Generate terrain using multiple octaves of noise
    for i in range(size):
        for j in range(size):
            nx = i / size - 0.5
            ny = j / size - 0.5
            terrain[i][j] = snoise2(
                nx, ny, octaves=octaves, persistence=persistence, lacunarity=lacunarity
            )

    # Normalize to 0-1 range
    terrain = (terrain - np.min(terrain)) / (np.max(terrain) - np.min(terrain))

    # Apply exponential function to create more dramatic mountains
    terrain = np.power(terrain, 1.5)

    # Scale to desired height
    terrain *= 25.0

    return terrain

def generate_perlin_terrain(size=128, scale=5.0):
    """Generate a terrain using non-fractal (single octave) Perlin noise for comparison."""
    terrain = np.zeros((size, size))
    for i in range(size):
        for j in range(size):
            nx = i / size - 0.5
            ny = j / size - 0.5
            # Only use one octave, so no persistence/lacunarity
            terrain[i][j] = snoise2(nx * scale, ny * scale, octaves=1)
    # Normalize to 0-1 range
    terrain = (terrain - np.min(terrain)) / (np.max(terrain) - np.min(terrain))
    # Optionally apply same power scaling for visual parity
    terrain = np.power(terrain, 1.5)
    terrain *= 25.0
    return terrain

def add_trees_with_variation(
        plotter,
        terrain,
        tree_indices,
        base_height=3,
        base_radius=0.7,
        color="forestgreen",
        seed=42,
    ):

    rng = np.random.default_rng(seed)
    for idx in tree_indices:
        y, x = idx
        # Slight random variation
        height = base_height * rng.uniform(0.85, 1.15)
        radius = base_radius * rng.uniform(0.85, 1.15)
        dx = rng.uniform(-0.3, 0.3)
        dy = rng.uniform(-0.3, 0.3)
        z = terrain[y, x]
        cone = pv.Cone(
            center=(x + dx, y + dy, z + height / 2),
            direction=(0, 0, 1),
            height=height,
            radius=radius,
            resolution=24,
        )
        plotter.add_mesh(cone, color=color)


def generate_tree_density(terrain, size=128):
    """Generate a tree density map based on terrain attributes"""
    # Trees grow better at mid elevations (not too high, not too low)
    min_height, max_height = np.min(terrain), np.max(terrain)
    mid_height = (min_height + max_height) / 2

    # Create initial density map based on height
    density = np.zeros_like(terrain)

    # More trees at mid elevations, fewer at very low or high elevations
    for i in range(size):
        for j in range(size):
            height = terrain[i, j]
            # Forest band between 20-60% of max height
            if height > min_height + 0.2 * (
                max_height - min_height
            ) and height < min_height + 0.6 * (max_height - min_height):
                density[i, j] = 1.0 - abs(height - mid_height * 0.8) / (
                    max_height * 0.4
                )
            else:
                density[i, j] = 0.1  # Use 0.1 for sparse trees elsewhere
    # Add some noise to make forest edges look natural
    noise = np.random.rand(size, size) * 0.3
    density = np.clip(density + noise, 0, 1)
    # Smooth the density map
    density = ndimage.gaussian_filter(density, sigma=2.0)
    return density


def visualize_terrain_with_trees(plotter, terrain, tree_density, tree_threshold=0.7):
    """Create a PyVista visualization of terrain with trees"""
    size = terrain.shape[0]

    # Create coordinate grid
    x = np.arange(size)
    y = np.arange(size)
    xx, yy = np.meshgrid(x, y)

    # Create structured grid for the terrain
    grid = pv.StructuredGrid(xx, yy, terrain)

    # Define terrain colors based on elevation
    min_h, max_h = float(np.min(terrain)), float(np.max(terrain))
    thresholds = [
        float(min_h),
        float(min_h + 0.2 * (max_h - min_h)),  # Water to grass transition
        float(min_h + 0.6 * (max_h - min_h)),  # Grass to mountain transition
        float(min_h + 0.85 * (max_h - min_h)),  # Mountain to snow transition
        float(max_h),
    ]

    # Create terrain type classification
    terrain_type = np.zeros_like(terrain, dtype=np.uint8)
    terrain_type[terrain < thresholds[1]] = 0  # Water
    terrain_type[(terrain >= thresholds[1]) & (terrain < thresholds[2])] = 1  # Grass
    terrain_type[(terrain >= thresholds[2]) & (terrain < thresholds[3])] = 2  # Mountain
    terrain_type[terrain >= thresholds[3]] = 3  # Snow

    # Color map for terrain types
    color_map = [
        "#1E90FF",  # Water (Dodger Blue)
        "#228B22",  # Grass (Forest Green)
        "#8B4513",  # Mountain (Saddle Brown)
        "#FFFAFA",  # Snow (Snow White)
    ]

    # --- Option 1: Color by terrain type (default) ---
    # plotter.add_mesh(
    #     grid,
    #     scalars=terrain_type.ravel(order='F'),
    #     show_edges=False,
    #     cmap=color_map,
    # )

    # --- Option 2: Color by elevation (uncomment to use) ---
    plotter.add_mesh(
        grid,
        scalars=terrain.ravel(order="F"),
        show_edges=False,
        cmap="terrain",
    )

    # Add trees as instanced geometry with sparse sampling
    sparse_factor = 4  # Only place trees on every 4th point (adjust as needed)
    sampled_mask = np.zeros_like(tree_density, dtype=bool)
    sampled_mask[::sparse_factor, ::sparse_factor] = True

    # Improved random tree distribution based on density probability
    max_tree_height = thresholds[2]  # No trees above mountain transition
    rng = np.random.default_rng(42)
    tree_points = []
    tree_heights = []
    tree_radii = []
    for y in range(terrain.shape[0]):
        for x in range(terrain.shape[1]):
            # Prevent trees in water
            if terrain[y, x] < thresholds[1]:
                continue
            if terrain[y, x] < max_tree_height:
                # Use density as probability for tree placement
                # Reduce overall number of trees by lowering probability
                if rng.uniform(0, 1) < tree_density[y, x] * tree_threshold * 0.3:
                    dx = float(rng.uniform(-0.5, 0.5))
                    dy = float(rng.uniform(-0.5, 0.5))
                    px = float(x) + dx
                    py = float(y) + dy
                    pz = float(terrain[y, x])
                    tree_points.append([px, py, pz])
                    # Even taller and much thinner trees
                    tree_heights.append(rng.uniform(1.5, 3.5))
                    tree_radii.append(rng.uniform(0.18, 0.5))
    tree_points = np.array(tree_points)
    tree_heights = np.array(tree_heights)
    tree_radii = np.array(tree_radii)

    # If we have tree points, create geometry
    if len(tree_points) > 0:
        tree_meshes = []
        for pt, height, radius in zip(tree_points, tree_heights, tree_radii):
            cone = pv.Cone(
                center=(pt[0], pt[1], pt[2] + height / 2),
                direction=(0, 0, 1),
                height=height,
                radius=radius,
                resolution=16,
            )
            tree_meshes.append(cone)
        all_trees = tree_meshes[0].copy()
        for mesh in tree_meshes[1:]:
            all_trees = all_trees.merge(mesh)
        plotter.add_mesh(all_trees, color="#228B22")  # Forest Green

    # Set up camera and rendering options
    plotter.view_isometric()
    plotter.set_background("#87CEEB")  # Sky Blue

    # Show the result
    plotter.show()


if __name__ == "__main__":
    # Generate the terrain
    size = 128
    # terrain = generate_terrain(size=size)
    # terrain = generate_perlin_terrain(size=size, scale=3.0)
    terrain = keras.preprocessing.image.load_img("neural/experiment.png", color_mode='grayscale', target_size=(128, 128))
    terrain = keras.preprocessing.image.img_to_array(terrain)
    # Remove the channel dimension for 2D terrain array
    terrain = terrain.squeeze()

    # Generate tree density map
    tree_density = generate_tree_density(terrain, size=size)
    plotter = pv.Plotter()
    # Visualize the terrain with trees
    visualize_terrain_with_trees(plotter, terrain, tree_density, tree_threshold=0.6)
