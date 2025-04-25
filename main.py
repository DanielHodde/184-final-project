import sys

from cli import noise_functions, parser
from qt.app import TerrainApp
from qt.tracks import circle_track
from terrain.visualization.pyvista_vis import (
    generate_tree_density,
    plot_terrain,
    visualize_terrain_with_trees,
)


def main():
    app = TerrainApp()
    app.get_view().track_path(circle_track([50, 50, 50], 120))

    args = parser.parse_args()

    noise_type = args.noise
    is_tree_enabled = args.tree
    is_style_transfer_enabled = args.style_transfer

    generate_noise = noise_functions[noise_type]

    plotter = app.get_plotter()
    terrain = generate_noise() * 10
    plot_terrain(plotter, terrain, show=False)

    if is_tree_enabled:
        tree_density = generate_tree_density(terrain, len(terrain))

        visualize_terrain_with_trees(
            plotter,
            terrain,
            tree_density,
        )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
