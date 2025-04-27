import sys

from qt.app import TerrainApp
from qt.tracks import circle_track
from terrain.generation.fractal_perlin import generate_fractal_perlin_noise
from terrain.generation.perlin import generate_perlin_noise
from terrain.visualization.pyvista_vis import (
    generate_tree_density,
    plot_terrain,
    visualize_terrain_with_trees,
)

noise_functions = {
    "Perlin": generate_perlin_noise,
    "Fractal-Perlin": generate_fractal_perlin_noise,
}

noise_defaults = {
    "Perlin": {
        "Shape": (100, 100),
        "Scale": 10,
        "Offset": (0.0, 0.0),
        "Zoom": 1.0,
    },
    "Fractal-Perlin": {
        "Shape": (100, 100),
        "Scale": 10,
        "Octaves": 4,
        "Persistence": 0.5,
        "Lacunarity": 2.0,
        "Offset": (0.0, 0.0),
        "Zoom": 1.0,
    },
}


def get_update_plotter(app):
    plotter = app.core.display.get_plotter()
    console = app.console

    # Function to update the plotter when the user pushes the update button
    def update_plotter():
        plotter.clear()
        # Start registering functions to the tree
        #
        # Although this function is called mutliple times, results are cached
        # so we don't need to worry about duplicates

        # A PTOption type is returned. Use this to append values/functions to
        # the tree such that one of which will be active at a time.
        opt = console.register_option("Noise")

        for noise in noise_functions:
            console.register_function(
                noise, noise_functions[noise], noise_defaults[noise], opt
            )

        generate_noise = opt.get_active_option()

        # A register_value or register_function call to a PTOption/PTGroup/console
        # will return an object that allows state updates
        #
        # To get the value, use PTValue.value
        # For functions, you can call them like normal, but default arguments
        # passed in are automatically registered by the PTCallable class.
        height_scale = console.register_value("Height Scale", 10)
        is_tree_enabled = console.register_value("Trees Enabled", False)
        is_style_transfer_enabled = console.register_value("Style-Transfer", False)

        terrain = generate_noise() * height_scale.value
        plot_terrain(plotter, terrain, show=False)

        # Example of using the registered value
        if is_tree_enabled.value:
            tree_density = generate_tree_density(terrain, len(terrain))

            visualize_terrain_with_trees(
                plotter,
                terrain,
                tree_density,
            )

        plotter.render()

    return update_plotter


def main():

    app = TerrainApp()
    app.get_view().track_path(circle_track([50, 50, 100], 200))

    update_plotter = get_update_plotter(app)

    app.core.on_update(update_plotter)
    app.core.handle_update()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
