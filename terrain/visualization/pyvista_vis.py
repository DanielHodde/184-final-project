"""
Visualization utilities using PyVista.
"""
import numpy as np
import pyvista as pv

def plot_terrain(terrain_array, show=True):
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
    plotter = pv.Plotter()
    min_h, max_h = np.min(zz), np.max(zz)
    thresholds = [min_h, min_h + 0.2*(max_h-min_h), min_h + 0.5*(max_h-min_h), min_h + 0.8*(max_h-min_h), max_h]
    color_map = [
        "#4682B4",  # Water (Steel Blue)
        "#228B22",  # Grass (Forest Green)
        "#CD853F",  # Mountain (Peru)
        "#FFFAFA",  # Snow (Snow White)
    ]
    terrain_type = np.zeros_like(zz, dtype=np.uint8)
    terrain_type[zz < thresholds[1]] = 0
    terrain_type[(zz >= thresholds[1]) & (zz < thresholds[2])] = 1
    terrain_type[(zz >= thresholds[2]) & (zz < thresholds[3])] = 2
    terrain_type[zz >= thresholds[3]] = 3
    plotter.add_mesh(
        grid,
        scalars=terrain_type.ravel(order='F'),
        show_edges=False,
        cmap=color_map,
    )
    if show:
        plotter.show()
    return plotter, grid

def add_trees_to_plotter(plotter, terrain_array, tree_density_map, tree_threshold=0.7, 
                         max_tree_height=80, tree_height=5, tree_radius=1, tree_color="forestgreen", seed=42):
    """
    Add trees using instanced geometry (much more efficient)
    """
    rng = np.random.default_rng(seed)
    
    # Sparse sampling - critical for performance and visualization quality
    sparse_factor = 5  # Use every 5th point in each dimension
    sampled_mask = np.zeros_like(tree_density_map, dtype=bool)
    sampled_mask[::sparse_factor, ::sparse_factor] = True
    
    # Create mask for where trees should be placed
    mask = (tree_density_map > tree_threshold) & (terrain_array < max_tree_height) & sampled_mask
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
        tree_glyph = pv.Cone(height=1.0, radius=tree_radius/tree_height, resolution=8, direction=(0, 0, 1))
        
        # Use the glyph filter for efficient instancing
        trees = point_cloud.glyph(geom=tree_glyph, orient=False, scale="height", factor=1)
        plotter.add_mesh(trees, color=tree_color)


def plot_terrain_with_trees(terrain_array, tree_density_map, tree_threshold=0.7, 
                           max_tree_height=80, tree_height=5, tree_radius=1, 
                           tree_color="forestgreen", seed=42):
    """
    Visualize a 2D numpy array as a 3D surface using PyVista and add trees 
    as cones based on a density map.
    """
    plotter, _ = plot_terrain(terrain_array, show=False)
    add_trees_to_plotter(plotter, terrain_array, tree_density_map, 
                         tree_threshold, max_tree_height, tree_height, 
                         tree_radius, tree_color, seed)
    plotter.show()
