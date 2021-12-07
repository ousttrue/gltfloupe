from typing import Optional, Any, Callable, Dict
import pathlib
import logging
import os
from dataclasses import dataclass

import glfw
import imgui
import imgui.integrations.glfw
from gltfio.parser import GltfData
from OpenGL import GL


logger = logging.getLogger(__name__)
INI_FILE = str(pathlib.Path(
    os.environ['USERPROFILE']) / 'gltfloupe.ini').encode('utf-8')


@dataclass
class View:
    name: str
    drawer: Callable[[], Any]
    use_begin: bool = True
    visible: bool = True

    def draw(self):
        if not self.visible:
            return
        if self.use_begin:
            is_expand, self.visible = imgui.begin(self.name, True)
            if is_expand:
                self.drawer()
            imgui.end()
        else:
            self.visible = self.drawer()


class GUI:
    def __init__(self) -> None:
        imgui.create_context()
        self.io = imgui.get_io()
        self.io.ini_file_name = INI_FILE
        # io.Fonts->AddFontFromFileTTF("resource\\ipag.ttf", 14.0f, nullptr, io.Fonts->GetGlyphRangesJapanese());
        self.io.fonts.add_font_from_file_ttf(
            "C:/Windows/Fonts/MSGothic.ttc", 20
        )
        self.io.config_flags |= imgui.CONFIG_DOCKING_ENABLE

        # views
        from .jsontree import JsonTree
        self.tree = JsonTree()

        from .loghandler import ImGuiLogHandler
        self.log_handler = ImGuiLogHandler()
        self.log_handler.setFormatter(logging.Formatter(
            '%(levelname)s:%(name)s:%(message)s'))
        logging.getLogger().handlers = [self.log_handler]

        def show_metrics():
            return imgui.show_metrics_window(True)

        from .prop import Prop
        self.prop = Prop()

        self.views = [
            View('json', self.tree.draw),
            View('log', self.log_handler.draw),
            View('metrics', show_metrics, False),
            View('prop', self.prop.draw),
        ]

        # gl
        import glglue.gl3.samplecontroller
        self.controller = glglue.gl3.samplecontroller.SampleController()
        self.gltf: Optional[GltfData] = None

    def initialize(self, window: glfw._GLFWwindow):
        self.impl = imgui.integrations.glfw.GlfwRenderer(window)
        self.show_json_tree = True

    def __del__(self):
        del self.controller
        self.impl.shutdown()

    def _update(self):
        from .dockspace import dockspace
        dockspace('docking_space')

        #
        # imgui menu
        #
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):

                clicked_quit, selected_quit = imgui.menu_item(
                    "Quit", 'Cmd+Q', False, True
                )

                if clicked_quit:
                    exit(1)

                imgui.end_menu()

            if imgui.begin_menu("View", True):
                for v in self.views:
                    clicked, v.visible = imgui.menu_item(
                        v.name, '', v.visible, True
                    )
                imgui.end_menu()

            imgui.end_main_menu_bar()

        #
        # imgui widgets
        #
        for v in self.views:
            v.draw()

        if self.gltf:
            self.prop.set(self.gltf.gltf, self.tree.selected)
        else:
            self.prop.set({}, ())

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
        self.gltf = None
        self.tree.root = None

        try:
            import gltfio
            self.gltf = gltfio.parse_path(file)
            self.file = file
            self.tree.root = self.gltf.gltf

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
