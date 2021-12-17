import sys
import pathlib
import logging
from . import config

logger = logging.getLogger(__name__)


class App:
    def __init__(self) -> None:

        ini, window_status = config.load()

        from .gui.glfw_window import GlfwWindow
        try:
            self.window = GlfwWindow('glTF loupe', window_status)
        except:
            self.window = GlfwWindow('glTF loupe')

        from .gui.gui import GUI
        self.gui = GUI(ini)
        self.gui.initialize(self.window.window)  # type: ignore

    def __del__(self):
        ini = self.gui.save_ini()
        del self.gui
        status = self.window.get_status()
        del self.window
        config.save(ini.decode('utf-8'), status)

    def run(self):
        while self.window.new_frame():
            self.gui.render()
            self.window.end_frame()


def run():
    logging.basicConfig(level=logging.DEBUG)

    app = App()
    if len(sys.argv) > 1:
        app.gui.open(pathlib.Path(sys.argv[1]))

    app.run()
