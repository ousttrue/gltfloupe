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
from .. import gltf_loader

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
            selected = None
            if is_expand:
                selected = self.drawer()
            imgui.end()
            return selected
        else:
            self.visible = self.drawer()


def load_font(size):
    '''
    https://github.com/ocornut/imgui/blob/master/docs/FONTS.md#font-loading-instructions
    '''
    io = imgui.get_io()
    # Load a first font
    fonts: imgui._FontAtlas = io.fonts
    # fonts.add_font_default()
    fonts.add_font_from_file_ttf(
        "C:/Windows/Fonts/MSGothic.ttc", size, None, fonts.get_glyph_ranges_japanese()
    )

    # Add character ranges and merge into the previous font
    # The ranges array is not copied by the AddFont* functions and is used lazily
    # so ensure it is available at the time of building or calling GetTexDataAsRGBA32().
    # Will not be copied by AddFont* so keep in scope.
    config = imgui.core._FontConfig()
    config.merge_mode = True
    config.glyph_min_advance_x = size
    # fonts->AddFontFromFileTTF("DroidSans.ttf", 18.0f, &config, io.Fonts->GetGlyphRangesJapanese()); // Merge into first font

    import ctypes
    icons_ranges = (ctypes.c_ushort * 3)(0xf000, 0xf3ff, 0)
    address = ctypes.addressof(icons_ranges)
    import fontawesome47
    fonts.add_font_from_file_ttf(
        str(fontawesome47.get_path()), size,
        config,
        imgui.core._StaticGlyphRanges.from_address(address))
    # Merge into first font
    fonts.build()


class GUI:
    def __init__(self) -> None:
        imgui.create_context()
        self.io = imgui.get_io()
        self.io.ini_file_name = INI_FILE
        load_font(20)
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

        from .accessor_table import AccessorTable
        self.accessor = AccessorTable()

        self.views = [
            View('json', self.tree.draw),
            View('log', self.log_handler.draw),
            View('metrics', show_metrics, False),
            View('prop', self.prop.draw),
            View('accessor', self.accessor.draw),
        ]

        # gl
        import glglue.gl3.samplecontroller
        self.controller = glglue.gl3.samplecontroller.SampleController()
        self.data: Optional[GltfData] = None
        self.loader: Optional[gltf_loader.GltfLoader] = None

    def initialize(self, window: glfw._GLFWwindow):
        self.impl = imgui.integrations.glfw.GlfwRenderer(window)
        self.show_json_tree = True

    def __del__(self):
        del self.controller
        self.impl.shutdown()

    def _update(self):
        from .dockspace import dockspace
        with dockspace('docking_space'):
            import fontawesome47.icons_str as ICONS_FA

            if imgui.button(ICONS_FA.ARROW_LEFT):
                self.tree.back()

            imgui.same_line()
            if imgui.button(ICONS_FA.ARROW_RIGHT):
                self.tree.forward()

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
            selected = v.draw()
            if selected:
                self.tree.push(selected)

        self.prop.set(self.data, self.tree.get_selected(), self.loader)
        self.accessor.set(self.data, self.tree.get_selected(), self.loader)

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
        self.data = None
        self.tree.root = None

        try:
            import gltfio
            self.data = gltfio.parse_path(file)
            self.file = file
            self.tree.root = self.data.gltf
            self.tree.push(())

            # opengl
            self.loader = gltf_loader.GltfLoader(self.data)
            scene = self.loader.load()
            scene.calc_world()
            self.controller.scene.drawables = [scene]  # type: ignore
            from glglue.ctypesmath import AABB
            aabb = AABB.new_empty()
            aabb = scene.expand_aabb(aabb)
            self.controller.camera.fit(*aabb)

        except Exception as e:
            logger.exception(e)
