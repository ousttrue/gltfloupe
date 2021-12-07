from typing import Any, Optional
import logging
import glfw
from OpenGL import GL


logger = logging.getLogger(__name__)


class GlfwWindow:
    def __init__(self, window_name: str, width=1280, height=720) -> None:
        if not glfw.init():
            logger.error("Could not initialize OpenGL context")
            exit(1)

        # OS X supports only forward-compatible core profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)

        # Create a windowed mode window and its OpenGL context
        self.window = glfw.create_window(
            int(width), int(height), window_name, None, None
        )
        if not self.window:
            logger.error("Could not initialize Window")
            exit(1)

        glfw.make_context_current(self.window)

        glfw.set_window_close_callback(self.window, self.on_close)

        self.is_running = True

    # def __del__(self):
    #     glfw.terminate()

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
