import ast
import inspect
import uuid

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit


class PTGroup:
    """
    Defines a group of either values or functions in a parameter tree.
    Each object maintains its state which updates upon a signal from the tree.
    """

    def __init__(self, tree):
        self.tree = tree
        self.cache = {}

    def register_value(self, name, val, show=True):
        identifier = f"{name}_{self.tree.id}"
        if identifier in self.cache:
            return self.cache[identifier]

        entry = dict(name=name, default=val)

        signal = self.tree.push(entry, show=show)
        ret_val = PTValue(val)
        if signal:
            signal.connect(ret_val.set_value)

        self.cache[identifier] = ret_val
        return ret_val

    def register_function(self, name, func, show=True):
        identifier = f"{name}_{self.tree.id}"
        if identifier in self.cache:
            return self.cache[identifier]

        ret_func = PTCallable(func)
        defaults = ret_func.defaults

        show_defaults = None

        if isinstance(show, list):
            show_defaults = {key: False for key in defaults}
            for kwarg in show:
                show_defaults[kwarg] = True
        else:
            show_defaults = {key: show for key in defaults}

        for key in defaults:
            show_param = show_defaults[key]
            ct = ParameterTree()
            self.tree.layout.addWidget(ct)
            if not show_param:
                ct.hide()

            entry = dict(name=key, default=defaults[key].value())
            signal = ct.push(entry, show=show_param)
            arg = ret_func.defaults[key]
            if signal:
                signal.connect(arg.set_value)

        self.cache[identifier] = ret_func
        return ret_func

    def register_option(self, name):
        identifier = f"{name}_{self.tree.id}"
        if identifier in self.cache:
            return self.cache[identifier]

        sub_tree = ParameterTree()
        sub_tree.layout.setContentsMargins(0, 0, 0, 0)
        opt = PTOption(sub_tree)

        signal = sub_tree.push(dict(name=name, default=opt))
        signal.connect(opt.set_idx)

        opt.options = sub_tree.layout.itemAt(0).itemAt(1).widget()
        self.tree.layout.addWidget(sub_tree)

        self.cache[identifier] = opt
        return opt


class PTOption(PTGroup):
    """
    An option object used to attach either functions or values, one of which can be active at a time.

    NOTE: Weird things can happen if you pass in unknown values for options.
    Can error on strings sometimes, it is recommended to pass a PTStatic value.
    """

    def __init__(self, tree):
        super().__init__(tree)

        self.widgets = []
        self.options = []
        self.idx = PTValue(0)

    def register_value(self, name, val, show=True):
        identifier = f"{name}_{self.tree.id}"
        if identifier in self.cache:
            return self.cache[identifier]

        gtree = ParameterTree()
        gtree.layout.setContentsMargins(0, 0, 0, 0)
        group = PTGroup(gtree)
        ret_val = group.register_value(name, val, show=show)

        self.widgets.append(gtree)
        self.tree.layout.addWidget(gtree)
        self.options.addItem(name, ret_val)

        if self.idx.value() != len(self.widgets) - 1:
            gtree.hide()

        self.cache[identifier] = ret_val
        return ret_val

    def register_function(self, name, func, show=True):
        identifier = f"{name}_{self.tree.id}"
        if identifier in self.cache:
            return self.cache[identifier]

        gtree = ParameterTree()
        gtree.layout.setContentsMargins(0, 0, 0, 0)
        group = PTGroup(gtree)
        ret_func = group.register_function(name, func, show=show)

        self.widgets.append(gtree)
        self.tree.layout.addWidget(gtree)
        self.options.addItem(name, ret_func)

        if self.idx.value() != len(self.widgets) - 1:
            gtree.hide()

        self.cache[identifier] = ret_func
        return ret_func

    def set_idx(self, idx):
        self.widgets[self.idx.value()].hide()
        self.idx.set_value(idx)
        self.widgets[self.idx.value()].show()

    def get_active_option(self):
        idx = self.idx.value()
        if -1 < idx and idx < len(self.options):
            return self.options.itemData(idx)
        return None


class PTCallable:
    """
    A wrapper around a function who's parameters are updateable PTValues
    """

    def __init__(self, func):
        self.func = func
        self.signature = inspect.signature(func)
        self.defaults = {}
        self.positional_count = 0
        for param in self.signature.parameters.values():
            if param.kind != param.POSITIONAL_ONLY and param.default != param.empty:
                self.defaults[param.name] = PTValue(param.default)
            else:
                self.positional_count += 1

    def __call__(self, *args, **kwargs):
        defaults = {key: self.defaults[key].value() for key in self.defaults}
        nkwargs = {}
        for key in kwargs:
            if key in defaults:
                defaults[key] = kwargs[key]
            else:
                nkwargs[key] = kwargs[key]

        keys = list(defaults.keys())
        for i in range(len(args) - self.positional_count):
            defaults.pop(keys[i])

        defaults = [v for v in defaults.values()]
        return self.func(*args, *defaults, **nkwargs)


class PTValue:
    """
    A wrapper around an updatable value
    """

    def __init__(self, value):
        self.val = value

    def value(self):
        if isinstance(self.val, PTValue):
            return self.val.value()
        return self.val

    def set_value(self, value):
        new_value = str(value)
        try:
            self.val = ast.literal_eval(new_value)
        except Exception:
            self.val = ""


class PTStatic(PTValue):
    """
    Like PTValue but we check for PTStatic to avoid updating the value
    """

    def __init__(self, value):
        super().__init__(value)


class PTImgPath(PTValue):
    def __init__(self, value):
        super().__init__(value)


class ParameterTree(QtWidgets.QWidget):
    """
    Contains widgets used to update the parameter of functions and values.
    Currently has limited support for various types.
    """

    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()

        self.setLayout(self.layout)
        left, top, right, bottom = self.layout.getContentsMargins()
        self.layout.setContentsMargins(left, 1, right, 0)

        self.id = uuid.uuid4()

    def push(self, parameter, show=True):
        default = parameter["default"]
        label = QLabel(parameter["name"])
        node = None
        node_align = Qt.AlignRight
        signal = None

        if isinstance(default, list):
            node = QComboBox()
            limits = parameter["limits"]
            node.addItems(limits)
            node.setCurrentIndex(limits.index(default))
            signal = node.currentTextChanged

        elif isinstance(default, bool):
            node = QCheckBox()
            node.setChecked(parameter.get("default", False))
            node.setText(parameter["name"])
            signal = node.toggled

        elif isinstance(default, PTOption):
            node = QComboBox()
            signal = node.currentIndexChanged

        elif isinstance(default, PTStatic):
            node = QLabel(str(default.value()))

        elif isinstance(default, PTImgPath):
            node = QLabel()
            pix = QPixmap(str(default.value())).scaled(100, 100, Qt.KeepAspectRatio)
            node.setPixmap(pix)
            label = None
            node_align = Qt.AlignCenter

        else:
            node = QLineEdit()
            node.setText(str(parameter.get("default", 0)))
            signal = node.textChanged

        hb = QHBoxLayout()
        if label:
            hb.addWidget(label, alignment=Qt.AlignLeft)
        hb.addWidget(node, alignment=node_align)
        if show:
            self.layout.addLayout(hb)

        return signal
