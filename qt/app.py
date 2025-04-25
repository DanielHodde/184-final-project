import numpy as np
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow
from pyvistaqt import QtInteractor

from .buttons import Buttons
from .camera import Camera, PathTracker


class TerrainApp(QApplication):
    def __init__(self):
        super().__init__([])

        self.main_window = MainWindow()
        self.console = Console()
        self.graph = TerrainGraph()

        self.main_window.attach(self.console)
        self.main_window.attach(self.graph)

        self.core = Core(self.console, self.graph)

        self.main_window.show()

    def get_plotter(self):
        return self.graph.get_plotter()

    def get_view(self):
        return self.core.camera


class Core:
    def __init__(self, console, display):
        self.console = console
        self.display = display
        self.camera = Camera()
        self.tracker = PathTracker()

        self.camera.connect(self.console.slider, self.console.buttons.buttons)
        self.camera.set_plotter(self.display.get_plotter())

    def track_path(self, path):
        self.camera.track_path(path)


class Console(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedSize(300, 900)

        self.slider = PathTracker()
        self.buttons = Buttons()

        self.layout.addWidget(self.buttons)
        self.layout.addWidget(self.slider)


class TerrainGraph(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.frame = QtWidgets.QFrame()
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)
        self.widget = None

        self.plotter = QtInteractor()
        self.layout.addWidget(self.plotter.interactor)

    def get_plotter(self):
        return self.plotter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window = QtWidgets.QSplitter()
        self.window.setFixedSize(1200, 900)
        self.setWindowTitle("Procedural Terrain Generation")
        self.setCentralWidget(self.window)

    def attach(self, widget):
        self.window.addWidget(widget)
