import glfw
import cydeer as imgui


def compute_fb_scale(window_size, frame_buffer_size):
    win_width, win_height = window_size
    fb_width, fb_height = frame_buffer_size

    # future: remove floats after dropping py27 support
    if win_width != 0 and win_width != 0:
        return float(fb_width) / win_width, float(fb_height) / win_height

    return 1., 1.


class GlfwRenderer:
    def __init__(self, window, attach_callbacks=True):
        if not imgui.GetCurrentContext():
            raise RuntimeError(
                "No valid ImGui context. Use imgui.create_context() first and/or "
                "imgui.set_current_context()."
            )
        self.io = imgui.GetIO()
        self.io.DeltaTime = 1.0 / 60.0

        self.window = window

        if attach_callbacks:
            glfw.set_key_callback(self.window, self.keyboard_callback)
            glfw.set_cursor_pos_callback(self.window, self.mouse_callback)
            glfw.set_window_size_callback(self.window, self.resize_callback)
            glfw.set_char_callback(self.window, self.char_callback)
            glfw.set_scroll_callback(self.window, self.scroll_callback)

        self.io.display_size = glfw.get_framebuffer_size(self.window)
        self.io.get_clipboard_text_fn = self._get_clipboard_text
        self.io.set_clipboard_text_fn = self._set_clipboard_text

        self._map_keys()
        self._gui_time = None

    def _get_clipboard_text(self):
        return glfw.get_clipboard_string(self.window)

    def _set_clipboard_text(self, text):
        glfw.set_clipboard_string(self.window, text)

    def _map_keys(self):
        key_map = self.io.KeyMap

        # TODO: enum
        # key_map[imgui.KEY_TAB] = glfw.KEY_TAB
        # key_map[imgui.KEY_LEFT_ARROW] = glfw.KEY_LEFT
        # key_map[imgui.KEY_RIGHT_ARROW] = glfw.KEY_RIGHT
        # key_map[imgui.KEY_UP_ARROW] = glfw.KEY_UP
        # key_map[imgui.KEY_DOWN_ARROW] = glfw.KEY_DOWN
        # key_map[imgui.KEY_PAGE_UP] = glfw.KEY_PAGE_UP
        # key_map[imgui.KEY_PAGE_DOWN] = glfw.KEY_PAGE_DOWN
        # key_map[imgui.KEY_HOME] = glfw.KEY_HOME
        # key_map[imgui.KEY_END] = glfw.KEY_END
        # key_map[imgui.KEY_INSERT] = glfw.KEY_INSERT
        # key_map[imgui.KEY_DELETE] = glfw.KEY_DELETE
        # key_map[imgui.KEY_BACKSPACE] = glfw.KEY_BACKSPACE
        # key_map[imgui.KEY_SPACE] = glfw.KEY_SPACE
        # key_map[imgui.KEY_ENTER] = glfw.KEY_ENTER
        # key_map[imgui.KEY_ESCAPE] = glfw.KEY_ESCAPE
        # key_map[imgui.KEY_PAD_ENTER] = glfw.KEY_KP_ENTER
        # key_map[imgui.KEY_A] = glfw.KEY_A
        # key_map[imgui.KEY_C] = glfw.KEY_C
        # key_map[imgui.KEY_V] = glfw.KEY_V
        # key_map[imgui.KEY_X] = glfw.KEY_X
        # key_map[imgui.KEY_Y] = glfw.KEY_Y
        # key_map[imgui.KEY_Z] = glfw.KEY_Z

    def keyboard_callback(self, window, key, scancode, action, mods):
        # perf: local for faster access
        io = self.io

        if action == glfw.PRESS:
            io.keys_down[key] = True
        elif action == glfw.RELEASE:
            io.keys_down[key] = False

        io.key_ctrl = (
            io.keys_down[glfw.KEY_LEFT_CONTROL] or
            io.keys_down[glfw.KEY_RIGHT_CONTROL]
        )

        io.key_alt = (
            io.keys_down[glfw.KEY_LEFT_ALT] or
            io.keys_down[glfw.KEY_RIGHT_ALT]
        )

        io.key_shift = (
            io.keys_down[glfw.KEY_LEFT_SHIFT] or
            io.keys_down[glfw.KEY_RIGHT_SHIFT]
        )

        io.key_super = (
            io.keys_down[glfw.KEY_LEFT_SUPER] or
            io.keys_down[glfw.KEY_RIGHT_SUPER]
        )

    def char_callback(self, window, char):
        if 0 < char < 0x10000:
            self.io.add_input_character(char)

    def resize_callback(self, window, width, height):
        self.io.display_size = width, height

    def mouse_callback(self, *args, **kwargs):
        pass

    def scroll_callback(self, window, x_offset, y_offset):
        self.io.mouse_wheel_horizontal = x_offset
        self.io.mouse_wheel = y_offset

    def process_inputs(self):
        io = self.io

        w, h = glfw.get_window_size(self.window)
        fb_size = glfw.get_framebuffer_size(self.window)

        io.DisplaySize.x = w
        io.DisplaySize.y = h
        io.DisplayFramebufferScale = compute_fb_scale((w, h), fb_size)
        io.DeltaTime = 1.0/60

        x = -1
        y = -1
        if glfw.get_window_attrib(self.window, glfw.FOCUSED):
            x, y = glfw.get_cursor_pos(self.window)
        io.MousePos.x = x
        io.MousePos.y = y
        io.MouseDown[0] = glfw.get_mouse_button(self.window, 0)
        io.MouseDown[1] = glfw.get_mouse_button(self.window, 1)
        io.MouseDown[2] = glfw.get_mouse_button(self.window, 2)

        current_time = glfw.get_time()

        if self._gui_time:
            self.io.DeltaTime = current_time - self._gui_time
        else:
            self.io.DeltaTime = 1. / 60.
        if(io.DeltaTime <= 0.0):
            io.DeltaTime = 1. / 1000.

        self._gui_time = current_time
