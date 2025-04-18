"""
Visualization utilities using PyVista.
"""

def plot_terrain(terrain_array):
    """
    Visualize a 2D numpy array as a 3D surface using PyVista.
    Args:
        terrain_array (np.ndarray): 2D array representing terrain heights.
    """
    import pyvista as pv
    import numpy as np

    if not isinstance(terrain_array, np.ndarray) or terrain_array.ndim != 2:
        raise ValueError("Input must be a 2D numpy array.")

    h, w = terrain_array.shape
    x = np.arange(w, dtype=np.float32)
    y = np.arange(h, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    zz = terrain_array.astype(np.float32)
    grid = pv.StructuredGrid(xx, yy, zz)
    plotter = pv.Plotter()
    # Custom color mapping based on height
    # Define color categories: water, grass, mountain, snow
    min_h, max_h = np.min(zz), np.max(zz)
    thresholds = [min_h, min_h + 0.2*(max_h-min_h), min_h + 0.5*(max_h-min_h), min_h + 0.8*(max_h-min_h), max_h]
    colors = np.array([
        [70, 130, 180],   # Water (Steel Blue)
        [34, 139, 34],    # Grass (Forest Green)
        [205, 133, 63],   # Mountain (Peru)
        [255, 250, 250],  # Snow (Snow White)
    ], dtype=np.uint8)
    # Assign terrain types based on thresholds
    terrain_type = np.zeros_like(zz, dtype=np.uint8)
    terrain_type[zz < thresholds[1]] = 0
    terrain_type[(zz >= thresholds[1]) & (zz < thresholds[2])] = 1
    terrain_type[(zz >= thresholds[2]) & (zz < thresholds[3])] = 2
    terrain_type[zz >= thresholds[3]] = 3
    # Map terrain types to color hex codes for PyVista
    color_map = [
        "#4682B4",  # Water (Steel Blue)
        "#228B22",  # Grass (Forest Green)
        "#CD853F",  # Mountain (Peru)
        "#FFFAFA",  # Snow (Snow White)
    ]
    # Flatten terrain_type in Fortran order to match PyVista's point order
    plotter.add_mesh(
        grid,
        scalars=terrain_type.ravel(order='F'),
        show_edges=False,
        cmap=color_map,
        clim=[0, 3],
        nan_color="black",
    )
    plotter.add_axes()
    plotter.show()

