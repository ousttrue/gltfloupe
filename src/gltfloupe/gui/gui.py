from typing import Optional, Union, Any
import pathlib
import logging

import glfw
import imgui
import imgui.integrations.glfw
from gltfio.parser import GltfData
from OpenGL import GL


logger = logging.getLogger(__name__)


class GUI:
    def __init__(self) -> None:
        imgui.create_context()
        self.io = imgui.get_io()
        # gl
        import glglue.gl3.samplecontroller
        self.controller = glglue.gl3.samplecontroller.SampleController()
        self.gltf: Optional[GltfData] = None
        self.selected = None
        self.io.config_flags |= imgui.CONFIG_DOCKING_ENABLE

    def initialize(self, window: glfw._GLFWwindow):
        self.impl = imgui.integrations.glfw.GlfwRenderer(window)
        self.show_json_tree = True

    def __del__(self):
        del self.controller
        self.impl.shutdown()

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
        from .dockspace import dockspace
        dockspace('docking_space')

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

    def _update_view(self):
        w, h = self.io.display_size
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

    def _new_frame(self):
        self.impl.process_inputs()
        imgui.new_frame()
        self._update()

        # update controller
        if not self.io.want_capture_mouse:
            self._update_view()

        imgui.render()

    def render(self):
        self._new_frame()

        # render
        GL.glClearColor(1., 1., 1., 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        self.controller.draw()

        self.impl.render(imgui.get_draw_data())

    def open(self, file: pathlib.Path):
        logger.info(f'load: {file.name}')

        try:
            import gltfio
            self.gltf = gltfio.parse_path(file)
            self.file = file

            # opengl
            from ..gltf_loader import GltfLoader
            loader = GltfLoader(self.gltf)
            scene = loader.load()
            self.controller.scene.drawables = [scene]  # type: ignore
            from glglue.ctypesmath import AABB
            aabb = AABB.new_empty()
            aabb = scene.expand_aabb(aabb)
            self.controller.camera.fit(*aabb)

        except Exception as e:
            logger.exception(e)
