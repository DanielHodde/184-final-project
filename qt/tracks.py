import numpy as np


def circle_track(origin, radius):
    # Parameters
    height = origin[2]
    num_points = 1000  # Number of points for the circle

    # Parametric equations for a circle
    theta = np.linspace(0, 2 * np.pi, num_points)
    x = radius * np.cos(theta) + origin[0]
    y = radius * np.sin(theta) + origin[1]
    z = np.full_like(x, height)  # Constant height at 10

    # Combine x, y, z into a 3D array (each point as (x, y, z))
    circle_points = np.vstack((x, y, z)).T
    return circle_points
