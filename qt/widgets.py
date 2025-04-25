from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSpacerItem,
    QSpinBox,
)
from pyvistaqt import QtInteractor

from .buttons import Buttons
from .camera import PathTracker

PARAMS = [
    dict(
        name="noise",
        type="list",
        limits=["perlin", "fractal-perlin"],
        default="perlin",
        children=[
            dict(name="height scale", type="float", default=10, min=0, max=200),
        ],
    ),
    dict(
        name="style-transfer",
        type="bool",
        default=False,
    ),
    dict(name="trees", type="bool", default=False),
]


class WidgetOrPT:
    def __init__(self, widget, tree):
        self.widget = widget
        self.tree = tree

    def __getattr__(self, attr):
        if hasattr(self.tree, attr):
            return getattr(self.tree, attr)

        if hasattr(self.widget, attr):
            return getattr(self.widget, attr)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{attr}'"
        )


class ParameterTree(QtWidgets.QWidget):
    parameterChanged = pyqtSignal()

    def __init__(self, params):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(0)
        self.stretch = 5

        self.setLayout(self.layout)

        self.map = {}

        for arg in params:
            self.push(arg)

    def child(self, name):
        return self.map[name]

    def push(self, parameter):
        ptype = parameter["type"]
        label = QLabel(parameter["name"])
        node = None

        if ptype == "list":
            node = QComboBox()
            limits = parameter["limits"]
            node.addItems(limits)
            node.setCurrentIndex(limits.index(parameter.get("default", limits[0])))
            node.currentIndexChanged.connect(self.parameterChanged.emit)

        elif ptype == "bool":
            node = QCheckBox()
            node.setChecked(parameter.get("default", False))
            node.setText(parameter["name"])
            node.toggled.connect(self.parameterChanged.emit)

        elif ptype == "float":
            node = QSpinBox()
            node.setValue(parameter.get("default", 0))
            node.setMinimum(parameter.get("min", 0))
            node.setMaximum(parameter.get("max", 100))
            node.valueChanged.connect(self.parameterChanged.emit)

        hb = QHBoxLayout()
        hb.addWidget(label)
        hb.addWidget(node)

        self.layout.addLayout(hb, self.stretch)
        self.map[parameter["name"]] = node

        if "children" in parameter:
            pt = ParameterTree(parameter["children"])
            self.layout.addWidget(pt)
            self.map[parameter["name"]] = WidgetOrPT(node, pt)
            pt.parameterChanged.connect(self.parameterChanged.emit)


class Console(QtWidgets.QWidget):
    parameterChanged = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.layout = QtWidgets.QVBoxLayout()

        self.setLayout(self.layout)
        self.setFixedSize(300, 900)

        self.slider = PathTracker()
        self.buttons = Buttons()
        self.tree = ParameterTree(PARAMS)
        self.tree.layout.addSpacerItem(QSpacerItem(300, 900))
        self.tree.parameterChanged.connect(self.parameterChanged.emit)

        self.layout.addWidget(self.tree)
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
