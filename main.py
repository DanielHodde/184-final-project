import sys

from qt.app import TerrainApp
from qt.tracks import circle_track


def main():
    app = TerrainApp()
    app.get_view().track_path(circle_track([50, 50, 50], 200))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
