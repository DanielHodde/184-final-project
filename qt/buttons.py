from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

import qt.Resources.resources


class PlayButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setIcon(QIcon(":/icons/play.png"))
        self.clicked.connect(self.toggle)
        self.play = 1
        self.setFixedWidth(50)

    def reset(self):
        self.setIcon(QIcon(":/icons/play.png"))

    def track(self, slider):
        self.tracked_slider = slider
        slider.anim.finished.connect(self.toggle)

    def toggle(self):
        if self.play:
            if self.tracked_slider.can_animate():
                self.setIcon(QIcon(":/icons/pause.png"))
                self.tracked_slider.animate()
                self.play = 0

        else:
            self.setIcon(QIcon(":/icons/play.png"))
            self.tracked_slider.anim.stop()
            self.play = 1


class SwitchButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setIcon(QIcon(":/icons/switch.png"))
        self.setFixedWidth(50)


class Buttons(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.buttons = [PlayButton(), SwitchButton()]

        for b in self.buttons:
            self.layout.addWidget(b)
