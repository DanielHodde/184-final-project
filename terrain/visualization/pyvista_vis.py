"""
Visualization utilities using PyVista.
"""

import numpy as np
import pyvista as pv
from scipy import ndimage


def plot_terrain(plotter, terrain_array, show=True):
    """
    Visualize a 2D numpy array as a 3D surface using PyVista.
    Returns the plotter and grid for further modification.
    """
    if not isinstance(terrain_array, np.ndarray) or terrain_array.ndim != 2:
        raise ValueError("Input must be a 2D numpy array.")
    h, w = terrain_array.shape
    x = np.arange(w, dtype=np.float32)
    y = np.arange(h, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    zz = terrain_array.astype(np.float32)
    grid = pv.StructuredGrid(xx, yy, zz)
    # min_h, max_h = np.min(zz), np.max(zz)
    # thresholds = [
    #     min_h,
    #     min_h + 0.2 * (max_h - min_h),
    #     min_h + 0.5 * (max_h - min_h),
    #     min_h + 0.8 * (max_h - min_h),
    #     max_h,
    # ]
    # color_map = [
    #     "#4682B4",  # Water (Steel Blue)
    #     "#228B22",  # Grass (Forest Green)
    #     "#CD853F",  # Mountain (Peru)
    #     "#FFFAFA",  # Snow (Snow White)
    # ]
    # terrain_type = np.zeros_like(zz, dtype=np.uint8)
    # terrain_type[zz < thresholds[1]] = 0
    # terrain_type[(zz >= thresholds[1]) & (zz < thresholds[2])] = 1
    # terrain_type[(zz >= thresholds[2]) & (zz < thresholds[3])] = 2
    # terrain_type[zz >= thresholds[3]] = 3
    plotter.add_mesh(
        grid,
        scalars=terrain_array.ravel(order="F"),
        show_edges=False,
        cmap="terrain",
    )
    if show:
        plotter.show()
    return plotter, grid


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
    # size = terrain.shape[0]

    # # Create coordinate grid
    # x = np.arange(size)
    # y = np.arange(size)
    # xx, yy = np.meshgrid(x, y)
    #
    # # Create structured grid for the terrain
    # grid = pv.StructuredGrid(xx, yy, terrain)

    # Define terrain colors based on elevation
    min_h, max_h = float(np.min(terrain)), float(np.max(terrain))
    thresholds = [
        float(min_h),
        float(min_h + 0.2 * (max_h - min_h)),  # Water to grass transition
        float(min_h + 0.6 * (max_h - min_h)),  # Grass to mountain transition
        float(min_h + 0.85 * (max_h - min_h)),  # Mountain to snow transition
        float(max_h),
    ]

    # # Create terrain type classification
    # terrain_type = np.zeros_like(terrain, dtype=np.uint8)
    # terrain_type[terrain < thresholds[1]] = 0  # Water
    # terrain_type[(terrain >= thresholds[1]) & (terrain < thresholds[2])] = 1  # Grass
    # terrain_type[(terrain >= thresholds[2]) & (terrain < thresholds[3])] = 2  # Mountain
    # terrain_type[terrain >= thresholds[3]] = 3  # Snow
    #
    # # Color map for terrain types
    # color_map = [
    #     "#1E90FF",  # Water (Dodger Blue)
    #     "#228B22",  # Grass (Forest Green)
    #     "#8B4513",  # Mountain (Saddle Brown)
    #     "#FFFAFA",  # Snow (Snow White)
    # ]

    # --- Option 1: Color by terrain type (default) ---
    # plotter.add_mesh(
    #     grid,
    #     scalars=terrain_type.ravel(order='F'),
    #     show_edges=False,
    #     cmap=color_map,
    # )

    # --- Option 2: Color by elevation (uncomment to use) ---
    # Add the surface mesh with flipped normals
    # plotter.add_mesh(
    #     grid,
    #     scalars=terrain.ravel(),
    #     show_edges=False,
    #     cmap="terrain",
    # )

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


def add_trees_to_plotter(
    plotter,
    terrain_array,
    tree_density_map,
    tree_threshold=0.7,
    max_tree_height=80,
    tree_height=5,
    tree_radius=1,
    tree_color="forestgreen",
    seed=42,
):
    """
    Add trees using instanced geometry (much more efficient)
    """
    rng = np.random.default_rng(seed)

    # Sparse sampling - critical for performance and visualization quality
    sparse_factor = 5  # Use every 5th point in each dimension
    sampled_mask = np.zeros_like(tree_density_map, dtype=bool)
    sampled_mask[::sparse_factor, ::sparse_factor] = True

    # Create mask for where trees should be placed
    mask = (
        (tree_density_map > tree_threshold)
        & (terrain_array < max_tree_height)
        & sampled_mask
    )
    tree_indices = np.argwhere(mask)

    # Create points for trees
    points = np.zeros((len(tree_indices), 3))
    for i, (y_idx, x_idx) in enumerate(tree_indices):
        dx = rng.uniform(-0.4, 0.4)
        dy = rng.uniform(-0.4, 0.4)
        x = float(x_idx) + dx
        y = float(y_idx) + dy
        z = float(terrain_array[y_idx, x_idx])
        points[i] = [x, y, z]

    # Create varying tree heights for natural appearance
    heights = tree_height * rng.uniform(0.8, 1.2, size=len(points))

    # If we have points, create glyphs (instanced geometry)
    if len(points) > 0:
        point_cloud = pv.PolyData(points)
        # Add height data
        point_cloud["height"] = heights

        # Create a single tree model (cone)
        tree_glyph = pv.Cone(
            height=1.0,
            radius=tree_radius / tree_height,
            resolution=8,
            direction=(0, 0, 1),
        )

        # Use the glyph filter for efficient instancing
        trees = point_cloud.glyph(
            geom=tree_glyph, orient=False, scale="height", factor=1
        )
        plotter.add_mesh(trees, color=tree_color)


def plot_terrain_with_trees(
    terrain_array,
    tree_density_map,
    tree_threshold=0.7,
    max_tree_height=80,
    tree_height=5,
    tree_radius=1,
    tree_color="forestgreen",
    seed=42,
):
    """
    Visualize a 2D numpy array as a 3D surface using PyVista and add trees
    as cones based on a density map.
    """
    plotter, _ = plot_terrain(terrain_array, show=False)
    add_trees_to_plotter(
        plotter,
        terrain_array,
        tree_density_map,
        tree_threshold,
        max_tree_height,
        tree_height,
        tree_radius,
        tree_color,
        seed,
    )
    plotter.show()
