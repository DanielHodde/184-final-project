from .camera import Camera


class TCore:
    def __init__(self, console, display):
        self.console = console
        self.display = display

        self.console.buttons.buttons[2].clicked.connect(self.handle_update)

        self.camera = Camera()

        self.camera.connect(self.console.slider, self.console.buttons.buttons)
        self.camera.set_plotter(self.display.get_plotter())

    def track_path(self, path):
        self.camera.track_path(path)

    def handle_update(self):
        self.update_plotter()

    def on_update(self, fun):
        self.update_plotter = fun
