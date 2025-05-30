"""
Perlin noise terrain generation implementation.
"""

import time

import numpy as np


def domain_warp(
    shape=(100, 100),
    scale=10,
    offset=(0.0, 0.0),
    zoom=1.0,
    warps=0,
    strength=0.6,
    falloff=0.5,
):
    """
    Perform domain warping on a 2D coordinate grid with multiple iterations.

    Args:
        shape (tuple): Output shape (height, width) of the warped grid.
        scale (float): Scale of the base noise used for warping
                       (higher = more detail, smaller features).
        offset (tuple): (x, y) offset to shift the sampled region.
        zoom (float): Zoom factor for the noise; >1 zooms in, <1 zooms out.
        warps (int): Number of times to apply domain warping.
        strength (float): Initial strength of the warping applied to the coordinates.
        falloff (float): Factor by which the warp strength decreases in each iteration.

    Returns:
        tuple: Two 2D arrays (x, y) representing the warped coordinates.
    """
    h, w = shape
    # Initialize coordinates
    lin_x = np.linspace(0, scale / zoom, w, endpoint=False) + offset[0]
    lin_y = np.linspace(0, scale / zoom, h, endpoint=False) + offset[1]
    x, y = np.meshgrid(lin_x, lin_y)

    # Apply domain warping for warps iterations
    for i in range(warps):
        warp_noise_x = generate_fractal_perlin_noise(
            shape=shape, scale=scale, offset=offset, zoom=zoom
        )
        warp_noise_y = generate_fractal_perlin_noise(
            shape=shape, scale=scale, offset=offset, zoom=zoom
        )

        warp_noise_x = (warp_noise_x + 1) / 2 - 0.5
        warp_noise_y = (warp_noise_y + 1) / 2 - 0.5

        x += strength * warp_noise_x
        y += strength * warp_noise_y
        strength *= falloff

    return x, y


def generate_perlin_noise(x, y):
    """
    Generate a 2D Perlin noise array.
    Args:
        x (np.ndarray): Grid of samples for the x-axis
        y (np.ndarray): Grid of samples for the y-axis
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
        vectors = np.array(
            [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [-1, 1], [1, -1], [-1, -1]]
        )
        g = vectors[h % 8]
        return g[..., 0] * x + g[..., 1] * y

    # Integer part (grid coordinates)
    x0 = x.astype(int)
    y0 = y.astype(int)
    x1 = x0 + 1
    y1 = y0 + 1

    # Fractional part
    sx = x - x0
    sy = y - y0

    # Permutation table
    rng = np.random.RandomState(int(time.time()))
    perm = rng.permutation(256)
    perm = np.stack([perm, perm]).flatten()

    def hash_coords(xi, yi):
        return perm[(perm[xi % 256] + yi) % 256]

    # Hash grid corners
    n00 = gradient(hash_coords(x0, y0), sx, sy)
    n10 = gradient(hash_coords(x1, y0), sx - 1, sy)
    n01 = gradient(hash_coords(x0, y1), sx, sy - 1)
    n11 = gradient(hash_coords(x1, y1), sx - 1, sy - 1)

    # Interpolate
    u = fade(sx)
    v = fade(sy)
    nx0 = lerp(n00, n10, u)
    nx1 = lerp(n01, n11, u)
    nxy = lerp(nx0, nx1, v)
    return nxy


def generate_simplex_noise(x, y):
    """
    Generate a 2D Simplex noise array.

    Args:
        x (np.ndarray): Grid of samples for the x-axis
        y (np.ndarray): Grid of samples for the y-axis

    Returns:
        np.ndarray: 2D array of Simplex noise values normalized to the range [-1, 1].
    """

    F2 = 0.5 * (np.sqrt(3.0) - 1.0)
    G2 = (3.0 - np.sqrt(3.0)) / 6.0

    def lerp(a, b, t):
        """Linear interpolation."""
        return a + t * (b - a)

    def gradient(h, x, y):
        """Convert hash value to gradient and compute dot product with (x, y) offset."""
        # 8 possible directions
        vectors = np.array(
            [[1, 1], [-1, 1], [1, -1], [-1, -1], [1, 0], [-1, 0], [0, 1], [0, -1]]
        )
        g = vectors[h % 8]
        return g[..., 0] * x + g[..., 1] * y

    # Skew points to grid
    s = (x + y) * F2
    i = np.floor(x + s).astype(int)
    j = np.floor(y + s).astype(int)

    # Get simplex points
    t = (i + j) * G2
    x0 = x - i + t
    y0 = y - j + t

    # Determine upper/lower simplex
    i1 = (x0 > y0).astype(int)
    j1 = 1 - i1

    x1 = x0 - i1 + G2
    y1 = y0 - j1 + G2
    x2 = x0 - 1.0 + 2.0 * G2
    y2 = y0 - 1.0 + 2.0 * G2

    # Permutation table
    rng = np.random.RandomState(int(time.time()))
    perm = rng.permutation(256)
    perm = np.stack([perm, perm]).flatten()

    ii = np.mod(i, 256)
    jj = np.mod(j, 256)

    gi0 = perm[ii + perm[jj]]
    gi1 = perm[ii + i1 + perm[jj + j1]]
    gi2 = perm[ii + 1 + perm[jj + 1]]

    n0 = gradient(gi0, x0, y0)
    n1 = gradient(gi1, x1, y1)
    n2 = gradient(gi2, x2, y2)

    t0 = 0.5 - x0**2 - y0**2
    t0 = np.maximum(0, t0)
    t0 **= 4
    n0 *= t0

    t1 = 0.5 - x1**2 - y1**2
    t1 = np.maximum(0, t1)
    t1 **= 4
    n1 *= t1

    t2 = 0.5 - x2**2 - y2**2
    t2 = np.maximum(0, t2)
    t2 **= 4
    n2 *= t2

    noise = (n0 + n1 + n2) * 40
    return noise


def generate_ridge_noise(x, y, p=1.0):
    """
    Generate a 2D Ridge noise array.

    Args:
        x (np.ndarray): Grid of samples for the x-axis
        y (np.ndarray): Grid of samples for the y-axis
        p (float): Exponent factor to determine sharpness of ridges.
    Returns:
        np.ndarray: 2D array of Ridge noise values normalized to the range [-1, 1].
    """
    noise = generate_perlin_noise(x, y)
    noise = np.power(1 - np.abs(noise), p)

    return noise - (np.max(noise) - np.min(noise)) / 2


def generate_billow_noise(x, y, p=1.7):
    """
    Generate a 2D Billow noise array.

    Args:
        x (np.ndarray): Grid of samples for the x-axis
        y (np.ndarray): Grid of samples for the y-axis
        p (float): Exponent factor to adjust the softness of peaks.
    Returns:
        np.ndarray: 2D array of Billow noise values normalized to the range [-1, 1].
    """
    # Generate Perlin noise
    noise = generate_perlin_noise(x, y)

    # Apply Billow transformation
    billow_noise = np.abs(noise) ** p

    return billow_noise


def generate_fractal_perlin_noise(
    shape=(100, 100),
    scale=10,
    octaves=4,
    persistence=0.5,
    lacunarity=2.0,
    offset=(0.0, 0.0),
    zoom=1.0,
):
    """
    Generate a 2D fractal (FBM) Perlin noise array by summing multiple octaves.
    Args:
        shape (tuple): Output shape (height, width).
        scale (float): Base scale (frequency) of the first octave.
        octaves (int): Number of noise layers to sum.
        persistence (float): Amplitude multiplier for each octave.
        lacunarity (float): Frequency multiplier for each octave.
        offset (tuple): (x, y) offset to shift the sampled region (applied to all octaves, scaled by frequency).
        zoom (float): Zoom factor; >1 zooms in, <1 zooms out.
    Returns:
        np.ndarray: 2D array of fractal Perlin noise values in range [-1, 1].
    """
    w, h = shape

    noise = np.zeros(shape, dtype=np.float32)
    amplitude = 1.0
    frequency = 1.0
    max_amplitude = 0.0

    for _ in range(octaves):

        # Offset is scaled by frequency to allow zooming/panning
        octave_offset = (offset[0] * frequency, offset[1] * frequency)
        octave_scale = (scale * frequency) / zoom

        # Initialize coordinates
        lin_x = (
            np.linspace(0, octave_scale / zoom, w, endpoint=False) + octave_offset[0]
        )
        lin_y = (
            np.linspace(0, octave_scale / zoom, h, endpoint=False) + octave_offset[1]
        )
        x, y = np.meshgrid(lin_x, lin_y)

        noise += amplitude * generate_perlin_noise(x, y)

        max_amplitude += amplitude
        amplitude *= persistence
        frequency *= lacunarity
    noise /= max_amplitude
    return noise
