import sys

from qtpy import QtWidgets

from app import MainWindow
from cli import noise_functions, parser
from terrain.visualization.pyvista_vis import (
    add_trees_to_plotter,
    generate_tree_density,
    plot_terrain,
    visualize_terrain_with_trees,
)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()

    args = parser.parse_args()

    noise_type = args.noise
    is_tree_enabled = args.tree
    is_style_transfer_enabled = args.style_transfer

    generate_noise = noise_functions[noise_type]

    plotter = window.plotter
    terrain = generate_noise() * 10
    plot_terrain(plotter, terrain, show=False)

    if is_tree_enabled:
        tree_density = generate_tree_density(terrain, len(terrain))

        visualize_terrain_with_trees(
            plotter,
            terrain,
            tree_density,
        )

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
