import sys
import pathlib
import logging


logger = logging.getLogger(__name__)


def run():
    logging.basicConfig(
        format='%(levelname)s:%(name)s:%(message)s', level=logging.DEBUG)

    from .gui.glfw_window import GlfwWindow
    window = GlfwWindow('glTF loupe')

    from .gui.gui import GUI
    gui = GUI()
    gui.initialize(window.window)
    if len(sys.argv) > 1:
        gui.open(pathlib.Path(sys.argv[1]))

    while window.new_frame():
        gui.render()
        window.end_frame()
