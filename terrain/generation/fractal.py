"""
Fractal Perlin noise terrain generation implementation.
"""

import numpy as np


def generate_fractal_noise(
    noisef,
    shape=(100, 100),
    scale=10,
    offset=(0.0, 0.0),
    zoom=1.0,
    octaves=4,
    persistence=0.5,
    lacunarity=2.0,
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

        cur_noise = noisef(scale=octave_scale, offset=octave_offset)

        noise += amplitude * cur_noise

        max_amplitude += amplitude
        amplitude *= persistence
        frequency *= lacunarity
    noise /= max_amplitude
    return noise
