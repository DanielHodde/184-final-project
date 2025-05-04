from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QSizePolicy, QSpacerItem
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
        self.lpanel = PTPanel()

        self.core = TCore(self.console, self.graph)

        self.window = self.main_window.window
        self.main_window.vsplit_l.addWidget(self.lpanel)
        self.main_window.vsplit_m.addWidget(self.graph)
        self.main_window.vsplit_m.addWidget(self.ipanel)
        self.main_window.vsplit_r.addWidget(self.console)

        self.main_window.show()

    def get_view(self):
        return self.core.camera


class CompactVBox(QtWidgets.QVBoxLayout):
    def __init__(self):
        super().__init__()
        self.addStretch()

    def addWidget(self, widget):
        self.takeAt(self.count() - 1)
        super().addWidget(widget)
        self.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window = QtWidgets.QFrame()
        self.setWindowTitle("Procedural Terrain Generation")
        self.setCentralWidget(self.window)

        self.vsplit_l = CompactVBox()
        self.vsplit_m = CompactVBox()
        self.vsplit_r = CompactVBox()
        splits = [self.vsplit_l, self.vsplit_m, self.vsplit_r]

        self.layout = QtWidgets.QHBoxLayout()
        for split in splits:
            self.layout.addLayout(split)

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

    def register_value(self, name, val, show=True):
        ret_val = self.pt.register_value(name, val, show=show)
        return ret_val

    def register_function(self, name, func, show=True):
        ret_func = self.pt.register_function(name, func, show=show)
        return ret_func


class Console(PTPanel):

    def __init__(self):
        super().__init__()

        self.slider = PathTracker()
        self.buttons = Buttons()

        spacer = QSpacerItem(300, 900, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addSpacerItem(spacer)
        self.layout.addWidget(self.buttons)

        self.sliderbox = QtWidgets.QHBoxLayout()
        self.sliderbox.addWidget(self.slider)
        loop_choices = QtWidgets.QComboBox()
        for strategy in self.slider.loop_strategy:
            loop_choices.addItem(strategy)

        signal = loop_choices.currentTextChanged
        signal.connect(self.slider.set_loop_strategy)

        self.sliderbox.addWidget(loop_choices)

        self.layout.addLayout(self.sliderbox)


class InfoPanel(PTPanel):

    def __init__(self):
        super().__init__()

        self.opts = self.pt.register_option("Function Info")

    def addWidget(self, widget):
        self.layout.addWidget(widget)

    def register_function(self, name, func, show=True):
        self.opts.register_value(name, PTStatic(func.__doc__), show=show)


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
