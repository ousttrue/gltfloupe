from typing import Any, Optional, NamedTuple
import logging
import glfw
from OpenGL import GL


logger = logging.getLogger(__name__)


class WindowStatus(NamedTuple):
    x: int
    y: int
    width: int
    height: int
    is_maxmized: bool


class GlfwWindow:
    def __init__(self, window_name: str, window_status: Optional[WindowStatus] = None) -> None:
        if not glfw.init():
            logger.error("Could not initialize OpenGL context")
            exit(1)

        # OS X supports only forward-compatible core profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)

        # Create a windowed mode window and its OpenGL context
        width = window_status.width if window_status else 1280
        height = window_status.height if window_status else 720
        self.window: Optional[glfw._GLFWwindow] = glfw.create_window(
            width, height, window_name, None, None
        )
        if not self.window:
            logger.error("Could not initialize Window")
            exit(1)

        if window_status and window_status.is_maxmized:
            glfw.maximize_window(self.window)

        glfw.make_context_current(self.window)

        glfw.set_window_close_callback(self.window, self.on_close)

        self.is_running = True

    def __del__(self):
        # glfw.terminate()
        pass

    def on_close(self, window):
        self.is_running = False

    def new_frame(self) -> bool:
        if not self.is_running:
            return False
        if glfw.window_should_close(self.window):
            return False
        glfw.poll_events()
        return True

    def end_frame(self):
        glfw.swap_buffers(self.window)

    def get_status(self) -> WindowStatus:
        w, h = glfw.get_window_size(self.window)
        x, y = glfw.get_window_pos(self.window)
        is_maximized = True if glfw.get_window_attrib(
            self.window, glfw.MAXIMIZED) else False
        return WindowStatus(x, y, w, h, is_maximized)
