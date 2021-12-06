import sys
import pathlib
import logging
from typing import Optional, Union, Any
import OpenGL.GL as gl
import glfw
import imgui
from imgui.integrations.glfw import GlfwRenderer

from gltfio.parser import GltfData


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
    def __init__(self, window_name="glTFloupe", width=1280, height=720) -> None:
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
        self.show_json_tree = True

        # gl
        import glglue.gl3.samplecontroller
        self.controller = glglue.gl3.samplecontroller.SampleController()
        self.gltf: Optional[GltfData] = None
        self.selected = None

    def __del__(self):
        del self.controller
        self.impl.shutdown()
        glfw.terminate()

    def _jsontree(self):
        if not self.show_json_tree:
            return
        is_expand, self.show_json_tree = imgui.begin("jsontree", True)
        flags = (
            imgui.TABLE_BORDERS_VERTICAL
            | imgui.TABLE_BORDERS_OUTER_HORIZONTAL
            | imgui.TABLE_RESIZABLE
            | imgui.TABLE_ROW_BACKGROUND
            | imgui.TABLE_NO_BORDERS_IN_BODY
        )
        if is_expand:
            if self.gltf:
                if imgui.begin_table("jsontree_table", 2, flags):
                    # header
                    imgui.table_setup_column("key")
                    imgui.table_setup_column("value")
                    imgui.table_headers_row()

                    # body
                    def traverse(key: str, node: Union[list, dict, Any]):
                        flag = 0  # const.ImGuiTreeNodeFlags_.SpanFullWidth
                        match node:
                            case list():
                                value = f'({len(node)})'
                            case dict():
                                value = node.get('name', '')
                            case _:
                                flag |= imgui.TREE_NODE_LEAF
                                flag |= imgui.TREE_NODE_BULLET
                                # flag |= imgui.TREE_NODE_NO_TREE_PUSH_ON_OPEN
                                value = f'{node}'
                        imgui.table_next_row()
                        # col 0
                        imgui.table_next_column()
                        open = imgui.tree_node(key, flag)
                        imgui.set_item_allow_overlap()
                        # col 1
                        imgui.table_next_column()
                        if node == self.selected:
                            pass
                        _, selected = imgui.selectable(
                            value, node == self.selected, imgui.SELECTABLE_SPAN_ALL_COLUMNS)
                        if selected:
                            # update selctable
                            self.selected = node
                        if imgui.is_item_clicked():
                            # update selctable
                            self.selected = node
                        if open:
                            match node:
                                case list():
                                    for i, v in enumerate(node):
                                        traverse(f'{i}', v)
                                case dict():
                                    for k, v in node.items():
                                        traverse(k, v)
                            imgui.tree_pop()

                    imgui.set_next_item_open(True, imgui.ONCE)
                    for k, v in self.gltf.gltf.items():
                        traverse(k, v)

                    imgui.end_table()
        imgui.end()

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

            if imgui.begin_menu("View", True):
                _, self.show_json_tree = imgui.menu_item(
                    "jsontree", '', self.show_json_tree, True
                )

                imgui.end_menu()

            imgui.end_main_menu_bar()

        self._jsontree()

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
