import numpy as np
from PyQt6.QtCore import QPropertyAnimation, Qt
from PyQt6.QtWidgets import QSlider


def get_angle(v0, v1):
    cos_theta = np.dot(v0, v1) / (np.linalg.norm(v0) * np.linalg.norm(v1))

    if cos_theta > 1:
        cos_theta = 1

    elif cos_theta < -1:
        cos_theta = -1

    return np.arccos(cos_theta)


class PathTracker(QSlider):
    def __init__(self):
        super().__init__()

        self.min = 0
        self.max = 300
        self.reset()
        self.setMinimum(self.min)
        self.setMaximum(self.max)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.anim = QPropertyAnimation(self, b"value")
        self.anim.finished.connect(self.on_animation_finished)
        self.loop_strategy = {
            "Loop": self.loop,
            "Reverse": self.reverse,
        }
        self.handle_loop = self.loop

    def set_loop_strategy(self, strategy):
        self.handle_loop = self.loop_strategy[strategy]

    def track_path(self, path):
        self.track = path
        self.track_length = sum(
            [np.linalg.norm(path[i + 1] - path[i]) for i in range(len(path) - 1)]
        )
        self.anim_time = int(4 * self.track_length)

    def disconnect(self):
        self.track = None

    def reset(self):
        self.start = self.min
        self.end = self.max
        self.reversed = False
        self.setSliderPosition(self.min)
        self.track = None

    def reverse(self):
        self.start = self.max - self.start
        self.end = self.max - self.end
        self.reversed = not self.reversed
        self.setSliderPosition(self.sliderPosition())

    def loop(self):
        self.setSliderPosition(self.start)

    def can_animate(self):
        return self.sliderPosition() != self.end

    def animate(self):
        if self.can_animate():
            percentage = self.sliderPosition() / (self.max - self.min)
            time = int(self.anim_time * (1 - percentage))
            if self.reversed:
                time = int(self.anim_time * percentage)
            self.anim.setDuration(time)
            self.anim.setStartValue(self.sliderPosition())
            self.anim.setEndValue(self.end)
            self.anim.start()

    def on_animation_finished(self):
        self.handle_loop()
        self.animate()


class Camera:

    def set_plotter(self, plotter):
        self.plotter = plotter
        self.base_position = self.plotter.camera_position
        self.focal_point = self.base_position[1]

    def connect(self, slider, buttons):
        self.slider = slider
        self.play_button = buttons[0]
        self.reverse_button = buttons[1]

        self.play_button.track(self.slider)

        self.reverse_button.clicked.connect(self.slider.reverse)
        self.reverse_button.clicked.connect(self.reverse_path)
        self.reverse_button.clicked.connect(self.follow_path)

        self.slider.sliderMoved.connect(self.follow_path)
        self.slider.valueChanged.connect(self.follow_path)

    def reset(self):
        self.slider.reset()
        self.plotter.camera_position = self.base_position
        self.play_button.setChecked(False)

    def hide(self):
        self.slider.hide()
        self.play_button.hide()
        self.reverse_button.hide()

    def show(self):
        self.slider.show()
        self.play_button.show()
        self.reverse_button.show()

    def track_path(self, path):
        self.track = path
        path_lengths = np.linalg.norm(self.track[:-1] - self.track[1:], axis=1)
        self.clen = np.cumsum(path_lengths)
        self.slider.track_path(path)

        view_dir = np.array(path) - self.focal_point
        view_dir /= np.linalg.norm(view_dir, axis=1, keepdims=True)

        rot = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 0]])
        xy_dir = np.dot(view_dir, rot.T)

        norms = np.linalg.norm(xy_dir, axis=1)
        xy_dir[norms == 0] = np.array([1, 0, 0])
        xy_dir /= np.linalg.norm(xy_dir, axis=1, keepdims=True)

        view_up = np.cross(view_dir, xy_dir)
        view_up /= np.linalg.norm(view_up, axis=1, keepdims=True)
        self.view_up = -view_up

    def reverse_path(self):
        self.track = self.track[::-1]

    def disconnect(self):
        self.track = None
        self.slider.disconnect()

    def follow_path(self):

        if len(self.track) != 0:
            path_length = self.clen[-1]

            percent = self.slider.sliderPosition() / self.slider.max
            if self.slider.reversed:
                percent = 1 - percent

            dist = percent * path_length

            iter = np.searchsorted(self.clen, dist)

            curr_dist = self.clen[iter - 1] if iter > 0 else 0

            start = self.track[iter]
            end = self.track[iter + 1]
            vec = end - start

            vec_dist = np.linalg.norm(vec)
            p = (dist - curr_dist) / vec_dist

            c_pos = p * vec + start

            viewup = self.view_up[iter] + p * (
                self.view_up[iter + 1] - self.view_up[iter]
            )
            viewup = viewup / np.linalg.norm(viewup)

            new_position = (c_pos[0], c_pos[1], c_pos[2])
            self.plotter.set_position(new_position)
            self.plotter.set_viewup(viewup)
