import numpy as np


def add_erosion(
    noise,
    erosion_factor=0.8,
):
    scale = 10
    octaves = 4
    persistence = 0.5
    offset = (0.0, 0.0)
    zoom = 1.0
    noise_min = np.min(noise)

    w, h = noise.shape
    # Initialize coordinates
    lin_x = np.linspace(0, scale / zoom, w, endpoint=False) + offset[0]
    lin_y = np.linspace(0, scale / zoom, h, endpoint=False) + offset[1]
    x, y = np.meshgrid(lin_x, lin_y)

    amplitude = 1.0
    max_amplitude = 0.0

    dx, dy = np.zeros_like(noise, dtype=np.float32), np.zeros_like(
        noise, dtype=np.float32
    )

    for _ in range(octaves):
        gx, gy = np.gradient(noise)
        dx += gx
        dy += gy

        gradient_magnitude = np.power(dx, 2) + np.power(dy, 2)
        gradient_magnitude *= erosion_factor
        noise -= amplitude * gradient_magnitude

        max_amplitude += amplitude
        amplitude *= persistence

    noise /= max_amplitude
    noise += noise_min - np.min(noise)

    return noise
