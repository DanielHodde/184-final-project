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
        self.console = Console()

        self.core = TCore(self.console, self.graph)

        self.window = self.main_window.window
        self.main_window.hsplit.addWidget(self.graph)
        self.main_window.hsplit.addWidget(self.console)
        self.main_window.vsplit.addWidget(self.console.info)

        self.main_window.show()

    def get_view(self):
        return self.core.camera


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window = QtWidgets.QFrame()
        self.setWindowTitle("Procedural Terrain Generation")
        self.setCentralWidget(self.window)

        self.hsplit = QtWidgets.QSplitter()
        self.vsplit = QtWidgets.QVBoxLayout()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.hsplit)
        self.layout.addLayout(self.vsplit)

        self.window.setLayout(self.layout)


class Console(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.slider = PathTracker()
        self.buttons = Buttons()
        self.pt = PTGroup(ParameterTree())

        self.info = InfoPanel()

        self.layout.addWidget(self.pt.tree)
        self.layout.addWidget(self.buttons)
        self.layout.addWidget(self.slider)

    def register_option(self, name):
        opt = self.pt.register_option(name)
        return opt

    def register_value(self, name, val, opt=None):
        ret_val = None
        if opt:
            ret_val = opt.register_value(name, val)
        else:
            ret_val = self.pt.register_value(name, val)
        return ret_val

    def register_function(self, name, func, defaults, opt=None):
        ret_func = None
        if opt:
            ret_func = opt.register_function(name, func, defaults)
        else:
            ret_func = self.pt.register_function(name, func, defaults)

        self.info.register_function(name, ret_func)
        return ret_func


class InfoPanel(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.pt = PTGroup(ParameterTree())
        self.opts = self.pt.register_option("Function Info")
        self.layout.addWidget(self.pt.tree)

    def addWidget(self, widget):
        self.layout.addWidget(widget)

    def register_function(self, name, func):
        self.opts.register_value(name, PTStatic(func.func.__doc__))


class TerrainGraph(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.frame = QtWidgets.QFrame()
        self.layout = QtWidgets.QHBoxLayout()
        self.setFixedSize(700, 500)
        self.setLayout(self.layout)
        self.widget = None

        self.plotter = QtInteractor()
        self.layout.addWidget(self.plotter.interactor)

    def get_plotter(self):
        return self.plotter
