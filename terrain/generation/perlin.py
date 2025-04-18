"""
Perlin noise terrain generation implementation.
"""

import numpy as np

def generate_perlin_noise(shape=(100, 100), scale=10, offset=(0.0, 0.0), zoom=1.0):
    """
    Generate a 2D Perlin noise array.
    Args:
        shape (tuple): Output shape (height, width).
        scale (float): The number of grid cells per axis (higher = more detail, smaller features).
        offset (tuple): (x, y) offset to shift the sampled region.
        zoom (float): Zoom factor; >1 zooms in, <1 zooms out.
    Returns:
        np.ndarray: 2D array of Perlin noise values in range [-1, 1].
    """
    def lerp(a, b, t):
        return a + t * (b - a)

    def fade(t):
        return 6 * t**5 - 15 * t**4 + 10 * t**3

    def gradient(h, x, y):
        """Convert hash value to gradient and compute dot product with (x, y) offset."""
        # 8 possible directions
        vectors = np.array([[0,1],[0,-1],[1,0],[-1,0],[1,1],[-1,1],[1,-1],[-1,-1]])
        g = vectors[h % 8]
        return g[...,0]*x + g[...,1]*y

    h, w = shape
    # Adjust scale by zoom and apply offset
    lin_x = np.linspace(0, scale / zoom, w, endpoint=False) + offset[0]
    lin_y = np.linspace(0, scale / zoom, h, endpoint=False) + offset[1]
    x, y = np.meshgrid(lin_x, lin_y)

    # Integer part (grid coordinates)
    x0 = x.astype(int)
    y0 = y.astype(int)
    x1 = x0 + 1
    y1 = y0 + 1

    # Fractional part
    sx = x - x0
    sy = y - y0

    # Permutation table
    rng = np.random.RandomState(0)  # Fixed seed for reproducibility
    perm = rng.permutation(256)
    perm = np.stack([perm, perm]).flatten()

    def hash_coords(xi, yi):
        return perm[(perm[xi % 256] + yi) % 256]

    # Hash grid corners
    n00 = gradient(hash_coords(x0, y0), sx, sy)
    n10 = gradient(hash_coords(x1, y0), sx-1, sy)
    n01 = gradient(hash_coords(x0, y1), sx, sy-1)
    n11 = gradient(hash_coords(x1, y1), sx-1, sy-1)

    # Interpolate
    u = fade(sx)
    v = fade(sy)
    nx0 = lerp(n00, n10, u)
    nx1 = lerp(n01, n11, u)
    nxy = lerp(nx0, nx1, v)
    return nxy
