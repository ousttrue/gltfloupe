import sys
import pathlib
import logging


logger = logging.getLogger(__name__)


class App:
    def __init__(self) -> None:
        from .gui.glfw_window import GlfwWindow
        self.window = GlfwWindow('glTF loupe')

        from .gui.gui import GUI
        self.gui = GUI()
        self.gui.initialize(self.window.window)
        if len(sys.argv) > 1:
            self.gui.open(pathlib.Path(sys.argv[1]))

    def __del__(self):
        del self.gui
        del self.window

    def run(self):
        while self.window.new_frame():
            self.gui.render()
            self.window.end_frame()


def run():
    logging.basicConfig(level=logging.DEBUG)

    app = App()
    app.run()
