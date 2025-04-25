from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpacerItem,
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


def get_value(widget):
    if isinstance(widget, QComboBox):
        return widget.currentText()
    elif isinstance(widget, QCheckBox):
        return widget.isChecked()
    elif isinstance(widget, QLineEdit):
        return widget.text()
    elif isinstance(widget, WidgetOrPT):
        return widget.parse_values()
    return None


class WidgetOrPT:
    def __init__(self, widget, tree):
        self.widget = widget
        self.tree = tree

    def parse_values(self):
        return {"value": get_value(self.widget), "children": self.tree.parse_values()}

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
            node = QLineEdit()
            node.setText(str(parameter.get("default", 0)))

            node.returnPressed.connect(self.parameterChanged.emit)

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

    def parse_values(self):
        mappings = {}
        for key in self.map:
            widget = self.child(key)
            mappings[key] = get_value(widget)

        return mappings


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
