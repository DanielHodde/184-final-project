from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow
from pyvistaqt import QtInteractor

from .buttons import Buttons
from .camera import PathTracker
from .core import TCore
from .tree import ParameterTree, PTGroup, PTStatic


class TerrainApp(QApplication):
    def __init__(self):
        super().__init__([])

        self.main_window = MainWindow()
        self.graph = TerrainGraph()
        self.ipanel = InfoPanel()
        self.console = Console()

        self.core = TCore(self.console, self.graph)

        self.window = self.main_window.window
        self.main_window.vsplit_m.addWidget(self.graph)
        self.main_window.vsplit_m.addWidget(self.ipanel)
        self.main_window.vsplit_r.addWidget(self.console)

        self.main_window.show()

    def get_view(self):
        return self.core.camera


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window = QtWidgets.QFrame()
        self.setWindowTitle("Procedural Terrain Generation")
        self.setCentralWidget(self.window)

        self.vsplit_m = QtWidgets.QVBoxLayout()
        self.vsplit_r = QtWidgets.QVBoxLayout()

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.vsplit_m)
        self.layout.addLayout(self.vsplit_r)

        self.window.setLayout(self.layout)


class PTPanel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.pt = PTGroup(ParameterTree())
        self.layout.addWidget(self.pt.tree)

    def register_option(self, name):
        opt = self.pt.register_option(name)
        return opt

    def register_value(self, name, val):
        ret_val = self.pt.register_value(name, val)
        return ret_val

    def register_function(self, name, func):
        ret_func = self.pt.register_function(name, func)
        return ret_func


class Console(PTPanel):

    def __init__(self):
        super().__init__()

        self.slider = PathTracker()
        self.buttons = Buttons()

        self.layout.addWidget(self.buttons)
        self.layout.addWidget(self.slider)


class InfoPanel(PTPanel):

    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.opts = self.pt.register_option("Function Info")

    def addWidget(self, widget):
        self.layout.addWidget(widget)

    def register_function(self, name, func):
        self.opts.register_value(name, PTStatic(func.__doc__))


class TerrainGraph(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.frame = QtWidgets.QFrame()
        self.layout = QtWidgets.QHBoxLayout()
        self.setFixedSize(850, 550)
        self.setLayout(self.layout)
        self.widget = None

        self.plotter = QtInteractor()
        self.layout.addWidget(self.plotter.interactor)

    def get_plotter(self):
        return self.plotter
