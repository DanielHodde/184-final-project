import os
import sys
import tempfile

import numpy as np
from PIL import Image
from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget
from skimage.transform import resize

from qt.app import TerrainApp
from qt.tracks import circle_track
from qt.tree import PTImgPath, PTStatic
from terrain.generation.erosion import add_erosion
from terrain.generation.fractal import generate_fractal_noise
from terrain.generation.noise import (
    domain_warp,
    generate_billow_noise,
    generate_perlin_noise,
    generate_ridge_noise,
    generate_simplex_noise,
)
from terrain.style_transfer.neural_style import apply_neural_style
from terrain.visualization.pyvista_vis import (
    generate_tree_density,
    plot_terrain,
    visualize_terrain_with_trees,
)


def downsample_to_size(arr, target_shape):
    return resize(arr, target_shape, mode="reflect", anti_aliasing=True)


def get_image_files(directory):
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    return [
        f
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
        and os.path.splitext(f)[1].lower() in image_extensions
    ]


class StyleWorker(QObject):
    finished = pyqtSignal()
    result_ready = pyqtSignal(object)
    progress = pyqtSignal(int)

    def __init__(
        self,
        img_path,
        style_path,
        height_scale,
        num_steps,
        style_weight,
        content_weight,
        tv_weight,
    ):
        super().__init__()
        self.img_path = img_path
        self.style_path = style_path
        self.height_scale = height_scale
        self.num_steps = num_steps
        self.style_weight = style_weight
        self.content_weight = content_weight
        self.tv_weight = tv_weight

    def run(self):
        styled = apply_neural_style(
            self.img_path,
            self.style_path,
            num_steps=self.num_steps,
            style_weight=self.style_weight,
            content_weight=self.content_weight,
            tv_weight=self.tv_weight,
            progress_callback=self.progress.emit,
        )
        terrain_arr = np.mean(styled, axis=2) / 255.0
        terrain_arr = 2 * terrain_arr - 1
        self.result_ready.emit(terrain_arr)
        self.finished.emit()


def get_update_plotter(app):
    plotter = app.core.display.get_plotter()
    console = app.console
    ipanel = app.ipanel
    lpanel = app.lpanel

    # Function to update the plotter when the user pushes the update button
    def update_plotter():
        plotter.clear()

        # Register noise functions
        noise_opt = lpanel.register_option("Noise")
        noise_functions = {
            "Perlin": generate_perlin_noise,
            "Simplex": generate_simplex_noise,
            "Ridge": generate_ridge_noise,
            "Billow": generate_billow_noise,
        }

        for noise in noise_functions:
            noisef = noise_functions[noise]
            noise_opt.register_function(noise, noisef)
            ipanel.register_function(noise, noisef)

        # Noise params
        shape = lpanel.register_value("Shape", (100, 100)).value()
        scale = lpanel.register_value("Scale", 10).value()
        offset = lpanel.register_value("Offset", (0.0, 0.0)).value()
        zoom = lpanel.register_value("Zoom", 1.0).value()

        ipanel.register_function("Fractal Noise", generate_fractal_noise)

        lpanel.register_value("Domain Warp", PTStatic(""))
        d_warp = lpanel.register_function(
            "Domain Warp Function", domain_warp, show=["strength", "falloff", "warps"]
        )
        ipanel.register_function("Domain Warp", domain_warp)

        generate_noise = noise_opt.get_active_option()

        # Fractal noise params
        is_fractal_enabled = lpanel.register_value("Fractal", False)
        generate_fractal = lpanel.register_function(
            "Fractal Noise",
            generate_fractal_noise,
            show=["octaves", "persistence", "lacunarity"],
        )

        # Erosion
        is_erosion_enabled = lpanel.register_value("Erosion", False)
        apply_erosion = lpanel.register_function("Erosion Function", add_erosion)

        # Post-process
        height_scale = lpanel.register_value("Height Scale", 10)
        is_tree_enabled = lpanel.register_value("Trees Enabled", False)

        # Style transfer params
        is_style_transfer_enabled = console.register_value("Style Transfer", False)

        content_dir = "noises"
        content_opt = console.register_option("Content Path")
        content_opt.register_value("Custom", PTStatic("Custom"), show=False)
        for path in [f"{content_dir}/{file}" for file in get_image_files(content_dir)]:
            content_opt.register_value(path, PTImgPath(path))

        style_dir = "real-world"
        style_opt = console.register_option("Style Path")
        for path in [f"{style_dir}/{file}" for file in get_image_files(style_dir)]:
            style_opt.register_value(path, PTImgPath(path))

        content_path_val = content_opt.get_active_option()
        style_path_val = style_opt.get_active_option()

        iterations_val = console.register_value("Iterations", 2000)
        style_weight_val = console.register_value("Style Weight", 1e-5)
        content_weight_val = console.register_value("Noise Weight", 2.5e-11)
        tv_weight_val = console.register_value("Total Variation Weight", 1e-10)

        noise = None
        if is_fractal_enabled.value():

            def warp_and_noise(shape=shape, scale=scale, offset=offset, zoom=zoom):
                x, y = d_warp(shape, scale, offset, zoom)
                return generate_noise(x, y)

            noise = generate_fractal(warp_and_noise, shape, scale, offset, zoom)
        else:
            x, y = d_warp(shape, scale, offset, zoom)
            noise = generate_noise(x, y)

        size = noise.shape

        tmpfile = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        norm = (noise + 1) / 2
        img = Image.fromarray(np.uint8(norm * 255))
        img.save(tmpfile.name)

        if is_style_transfer_enabled.value():
            if content_path_val.value() == "Custom":
                content_path = tmpfile.name
            else:
                content_path = content_path_val.value()
            # insert preview & progress placeholders in graph area
            graph_widget = app.graph
            plotter.hide()
            # prepare widgets
            content_lbl = QLabel()
            content_title = QLabel("Content")
            style_lbl = QLabel()
            style_title = QLabel("Style")
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress_title = QLabel("Progress")
            # load thumbnails
            pix = QPixmap(content_path).scaled(200, 200, Qt.KeepAspectRatio)
            content_lbl.setPixmap(pix)
            pix2 = QPixmap(style_path_val.value()).scaled(200, 200, Qt.KeepAspectRatio)
            style_lbl.setPixmap(pix2)
            # container layout:
            placeholder = QWidget()
            ph_vlay = QVBoxLayout()
            # top row: two images side by side
            top_row = QHBoxLayout()
            # content column
            content_v = QVBoxLayout()
            content_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            content_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            content_v.addWidget(content_lbl)
            content_v.addWidget(content_title)
            content_v.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            # style column
            style_v = QVBoxLayout()
            style_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            style_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            style_v.addWidget(style_lbl)
            style_v.addWidget(style_title)
            style_v.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            top_row.addLayout(content_v)
            top_row.addLayout(style_v)
            top_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            ph_vlay.addLayout(top_row)
            # progress row
            prog_v = QVBoxLayout()
            progress.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            progress_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            prog_v.addWidget(progress)
            prog_v.addWidget(progress_title)
            prog_v.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            ph_vlay.addLayout(prog_v)
            ph_vlay.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            placeholder.setLayout(ph_vlay)
            graph_widget.layout.addWidget(placeholder)
            graph_widget._placeholders = [placeholder]

            worker = StyleWorker(
                content_path,
                style_path_val.value(),
                height_scale.value(),
                iterations_val.value(),
                style_weight_val.value(),
                content_weight_val.value(),
                tv_weight_val.value(),
            )
            worker.progress.connect(progress.setValue, Qt.QueuedConnection)

            # on style result: remove placeholders, restore plotter and render
            def handle_style_result(terrain_map):
                # remove placeholder container
                ph = graph_widget._placeholders[0]
                graph_widget.layout.removeWidget(ph)
                ph.deleteLater()
                plotter.show()

                terrain_map = downsample_to_size(terrain_map, size)
                noise_mdn = np.median(noise)
                terrain_map += noise_mdn - np.median(terrain_map)

                if is_erosion_enabled.value():
                    terrain_map = apply_erosion(terrain_map)

                terrain_map *= height_scale.value()
                plot_terrain(plotter, terrain_map, show=False)
                if is_tree_enabled.value():
                    tree_density = generate_tree_density(terrain_map, len(terrain_map))

                    visualize_terrain_with_trees(
                        plotter,
                        terrain_map,
                        tree_density,
                    )

            worker.result_ready.connect(handle_style_result, Qt.QueuedConnection)
            thread = QThread()
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.finished.connect(thread.quit)
            console._worker = worker
            console._thread = thread
            thread.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.start()
        else:
            terrain = noise
            if is_erosion_enabled.value():
                terrain = apply_erosion(terrain)

            terrain = terrain * height_scale.value()
            plot_terrain(plotter, terrain, show=False)

            if is_tree_enabled.value():
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
