import sys
import pathlib
import logging
import OpenGL.GL as gl
import glfw
import imgui
from imgui.integrations.glfw import GlfwRenderer
logger = logging.getLogger(__name__)


def docking_space(name: str):
    flags = (imgui.WINDOW_MENU_BAR
             | imgui.WINDOW_NO_DOCKING
             | imgui.WINDOW_NO_BACKGROUND
             | imgui.WINDOW_NO_TITLE_BAR
             | imgui.WINDOW_NO_COLLAPSE
             | imgui.WINDOW_NO_RESIZE
             | imgui.WINDOW_NO_MOVE
             | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
             | imgui.WINDOW_NO_NAV_FOCUS
             )

    viewport = imgui.get_main_viewport()
    x, y = viewport.pos
    w, h = viewport.size
    imgui.set_next_window_position(x, y)
    imgui.set_next_window_size(w, h)
    # imgui.set_next_window_viewport(viewport.id)
    imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0.0)
    imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 0.0)

    # When using ImGuiDockNodeFlags_PassthruCentralNode, DockSpace() will render our background and handle the pass-thru hole, so we ask Begin() to not render a background.
    # local window_flags = self.window_flags
    # if bit.band(self.dockspace_flags, ) ~= 0 then
    #     window_flags = bit.bor(window_flags, const.ImGuiWindowFlags_.NoBackground)
    # end

    # Important: note that we proceed even if Begin() returns false (aka window is collapsed).
    # This is because we want to keep our DockSpace() active. If a DockSpace() is inactive,
    # all active windows docked into it will lose their parent and become undocked.
    # We cannot preserve the docking relationship between an active window and an inactive docking, otherwise
    # any change of dockspace/settings would lead to windows being stuck in limbo and never being visible.
    imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, (0, 0))
    imgui.begin(name, None, flags)
    imgui.pop_style_var()
    imgui.pop_style_var(2)

    # DockSpace
    dockspace_id = imgui.get_id(name)
    imgui.dockspace(dockspace_id, (0, 0), imgui.DOCKNODE_PASSTHRU_CENTRAL_NODE)

    imgui.end()


class GlfwWindow:
    def __init__(self, window_name="minimal ImGui/GLFW3 example", width=1280, height=720) -> None:
        if not glfw.init():
            logger.error("Could not initialize OpenGL context")
            exit(1)

        # OS X supports only forward-compatible core profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

        # Create a windowed mode window and its OpenGL context
        self.window = glfw.create_window(
            int(width), int(height), window_name, None, None
        )
        if not self.window:
            logger.error("Could not initialize Window")
            exit(1)

        glfw.make_context_current(self.window)

        # imgui
        imgui.create_context()
        self.io = imgui.get_io()
        self.io.config_flags |= imgui.CONFIG_DOCKING_ENABLE
        self.impl = GlfwRenderer(self.window)
        self.show_custom_window = True

        # gl
        import glglue.gl3.samplecontroller
        self.controller = glglue.gl3.samplecontroller.SampleController()

    def __del__(self):
        del self.controller
        self.impl.shutdown()
        glfw.terminate()

    def _update(self):
        docking_space('docking_space')

        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):

                clicked_quit, selected_quit = imgui.menu_item(
                    "Quit", 'Cmd+Q', False, True
                )

                if clicked_quit:
                    exit(1)

                imgui.end_menu()
            imgui.end_main_menu_bar()

        if self.show_custom_window:
            is_expand, self.show_custom_window = imgui.begin(
                "Custom window", True)
            if is_expand:
                imgui.text("Bar")
                imgui.text_ansi("B\033[31marA\033[mnsi ")
                imgui.text_ansi_colored("Eg\033[31mgAn\033[msi ", 0.2, 1., 0.)
                imgui.extra.text_ansi_colored("Eggs", 0.2, 1., 0.)
            imgui.end()

    def new_frame(self) -> bool:
        if glfw.window_should_close(self.window):
            return False
        glfw.poll_events()
        self.impl.process_inputs()
        imgui.new_frame()
        self._update()

        w, h = self.io.display_size

        # update controller
        self.controller.onResize(w, h)
        x, y = self.io.mouse_pos
        if self.io.mouse_down[0]:
            self.controller.onLeftDown(x, y)
        else:
            self.controller.onLeftUp(x, y)
        if self.io.mouse_down[1]:
            self.controller.onRightDown(x, y)
        else:
            self.controller.onRightUp(x, y)
        if self.io.mouse_down[2]:
            self.controller.onMiddleDown(x, y)
        else:
            self.controller.onMiddleUp(x, y)
        if self.io.mouse_wheel:
            self.controller.onWheel(-self.io.mouse_wheel)
        self.controller.onMotion(x, y)

        imgui.render()

        return True

    def render(self):
        # render
        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        self.controller.draw()

        self.impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self.window)

    def open(self, file: pathlib.Path):
        logger.info(f'load: {file.name}')

        import gltfio
        try:
            self.gltf = gltfio.parse_path(file)
            self.file = file

            # opengl
            from .gltf_loader import GltfLoader
            loader = GltfLoader(self.gltf)
            scene = loader.load()
            self.controller.scene.drawables = [scene]
            from glglue.ctypesmath import AABB
            aabb = AABB.new_empty()
            aabb = scene.expand_aabb(aabb)
            self.controller.camera.fit(*aabb)

            # json
            # self.open_json(self.gltf.gltf, file, self.gltf.bin)

        except Exception as e:
            logger.exception(e)


def run():
    logging.basicConfig(
        format='%(levelname)s:%(name)s:%(message)s', level=logging.DEBUG)

    window = GlfwWindow()

    if len(sys.argv) > 1:
        window.open(pathlib.Path(sys.argv[1]))

    while window.new_frame():

        window.render()
