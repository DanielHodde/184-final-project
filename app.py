import numpy as np
from pyvistaqt import QtInteractor
from qtpy import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None, show=True):
        super().__init__(parent)

        self.frame = QtWidgets.QFrame()
        vlayout = QtWidgets.QVBoxLayout()

        # Add PyVista interactor
        self.plotter = QtInteractor(self.frame)
        vlayout.addWidget(self.plotter.interactor)
        self.signal_close = QtWidgets.QAction(self)
        self.signal_close.triggered.connect(self.plotter.close)

        self.frame.setLayout(vlayout)
        self.setCentralWidget(self.frame)

        # Basic menu options
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu("File")
        exitButton = QtWidgets.QAction("Exit", self)
        exitButton.setShortcut("Ctrl+Q")
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        # Animation Menu
        animationMenu = mainMenu.addMenu("Animation")
        self.animate_camera_action = QtWidgets.QAction("Animate Camera", self)
        self.animate_camera_action.triggered.connect(self.animate_camera)
        animationMenu.addAction(self.animate_camera_action)

        if show:
            self.show()

    def animate_camera(self):
        camera_position = self.plotter.camera_position
        start_position = camera_position[0]
        focal_point = camera_position[1]
        view_up = camera_position[2]

        step = np.pi / 256.0
        rot = np.array(
            [
                [np.cos(step), -np.sin(step), 0],
                [np.sin(step), np.cos(step), 0],
                [0, 0, 1],
            ]
        )
        cam_dir = np.array(start_position) - np.array(focal_point)
        n_frames = 1028

        for i in range(n_frames):
            cam_dir = np.dot(rot, cam_dir)
            new_position = cam_dir + focal_point
            new_position = (new_position[0], new_position[1], new_position[2])
            self.plotter.camera_position = [new_position, focal_point, view_up]
            self.plotter.render()
            QtWidgets.QApplication.processEvents()
