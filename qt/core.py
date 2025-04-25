from terrain.generation.fractal_perlin import generate_fractal_perlin_noise
from terrain.generation.perlin import generate_perlin_noise
from terrain.visualization.pyvista_vis import (
    generate_tree_density,
    plot_terrain,
    visualize_terrain_with_trees,
)

from .camera import Camera

noise_functions = {
    "perlin": generate_perlin_noise,
    "fractal-perlin": generate_fractal_perlin_noise,
}


class TCore:
    def __init__(self, console, display):
        self.console = console
        self.display = display
        self.console.parameterChanged.connect(self.handle_update)
        self.tree = self.console.tree

        self.camera = Camera()

        self.camera.connect(self.console.slider, self.console.buttons.buttons)
        self.camera.set_plotter(self.display.get_plotter())

        self.handle_update()

    def track_path(self, path):
        self.camera.track_path(path)

    def parse_parameter_tree(self):
        return {
            "noise": {
                "value": self.tree.child("noise").currentText(),
                "children": {
                    "height scale": self.tree.child("noise")
                    .child("height scale")
                    .value()
                },
            },
            "trees": self.tree.child("trees").isChecked(),
            "style-transfer": self.tree.child("style-transfer").isChecked(),
        }

    def handle_update(self):
        args = self.parse_parameter_tree()
        self.update_plotter(self.display.get_plotter(), args)

    def update_plotter(self, plotter, args):
        plotter.clear()

        noise_type = args["noise"]["value"]
        height_scale = args["noise"]["children"]["height scale"]
        is_tree_enabled = args["trees"]
        is_style_transfer_enabled = args["style-transfer"]

        generate_noise = noise_functions[noise_type]

        terrain = generate_noise() * height_scale
        plot_terrain(plotter, terrain, show=False)

        if is_tree_enabled:
            tree_density = generate_tree_density(terrain, len(terrain))

            visualize_terrain_with_trees(
                plotter,
                terrain,
                tree_density,
            )

        plotter.render()
