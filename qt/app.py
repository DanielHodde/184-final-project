from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow

from .core import TCore
from .widgets import Console, TerrainGraph


class TerrainApp(QApplication):
    def __init__(self):
        super().__init__([])

        self.main_window = MainWindow()
        self.graph = TerrainGraph()
        self.console = Console()

        self.main_window.attach(self.graph)
        self.main_window.attach(self.console)

        self.core = TCore(self.console, self.graph)

        self.main_window.show()

    def get_view(self):
        return self.core.camera


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window = QtWidgets.QSplitter()
        self.window.setFixedSize(1200, 900)
        self.setWindowTitle("Procedural Terrain Generation")
        self.setCentralWidget(self.window)

    def attach(self, widget):
        self.window.addWidget(widget)
