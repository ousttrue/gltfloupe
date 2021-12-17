from typing import Optional, Any, Callable
import pathlib
import ctypes
import logging
from dataclasses import dataclass

import glfw
import cydeer as imgui
from gltfio.parser import GltfData
from OpenGL import GL
from .. import gltf_loader

logger = logging.getLogger(__name__)


@dataclass
class View:
    name: str
    drawer: Callable[[], Any]
    visible: ctypes.Array
    use_begin: bool = True

    def draw(self):
        if not self.visible[0]:
            return

        imgui.SetNextWindowSize((550, 680), cond=imgui.ImGuiCond_.FirstUseEver)
        if self.use_begin:
            selected = None
            if imgui.Begin(self.name, self.visible):
                selected = self.drawer()
            imgui.End()
            return selected
        else:
            self.drawer(self.visible)  # type: ignore


def load_font(size):
    '''
    https://github.com/ocornut/imgui/blob/master/docs/FONTS.md#font-loading-instructions
    '''
    io = imgui.GetIO()
    # Load a first font
    fonts = io.Fonts
    # fonts.add_font_default()
    fonts.AddFontFromFileTTF(
        "C:/Windows/Fonts/MSGothic.ttc", size, None, fonts.GetGlyphRangesJapanese()
    )

    # Add character ranges and merge into the previous font
    # The ranges array is not copied by the AddFont* functions and is used lazily
    # so ensure it is available at the time of building or calling GetTexDataAsRGBA32().
    # Will not be copied by AddFont* so keep in scope.
    config = imgui.ImFontConfig()
    config.MergeMode = True
    config.FontDataOwnedByAtlas = True
    config.RasterizerMultiply = 1.0
    config.OversampleH = 3
    config.OversampleV = 1
    config.GlyphMaxAdvanceX = 99999
    config.GlyphMinAdvanceX = size
    # fonts->AddFontFromFileTTF("DroidSans.ttf", 18.0f, &config, io.Fonts->GetGlyphRangesJapanese()); // Merge into first font

    import ctypes
    icons_ranges = (ctypes.c_ushort * 3)(0xf000, 0xf3ff, 0)
    import fontawesome47
    fonts.AddFontFromFileTTF(
        str(fontawesome47.get_path()), size,
        config,
        icons_ranges)
    # Merge into first font
    fonts.Build()


class GUI:
    def __init__(self, ini:  Optional[str]) -> None:
        imgui.CreateContext()
        self.io: imgui.ImGuiIO = imgui.GetIO()
        self.io.ConfigFlags |= imgui.ImGuiConfigFlags_.DockingEnable
        if isinstance(ini, str):
            imgui.LoadIniSettingsFromMemory(ini.encode('utf-8'))
        self.io.IniFilename = None  # type: ignore
        load_font(20)

        # views
        from .jsontree import JsonTree
        self.tree = JsonTree()

        from .loghandler import ImGuiLogHandler
        self.log_handler = ImGuiLogHandler()
        self.log_handler.setFormatter(logging.Formatter(
            '%(levelname)s:%(name)s:%(message)s'))
        logging.getLogger().handlers = [self.log_handler]

        def show_metrics(p_open):
            return imgui.ShowMetricsWindow(p_open)

        def show_demo(p_open):
            return imgui.ShowDemoWindow(p_open)

        from .prop import Prop
        self.prop = Prop()

        from .animation import Playback
        self.playback = Playback()

        self.views = [
            View('json', self.tree.draw, (ctypes.c_bool * 1)(True)),
            View('log', self.log_handler.draw, (ctypes.c_bool * 1)(True)),
            View('prop', self.prop.draw, (ctypes.c_bool * 1)(True)),
            View('playback', self.playback.draw, (ctypes.c_bool * 1)(True)),
            #
            View('metrics', show_metrics, (ctypes.c_bool * 1)  # type: ignore
                 (True), False),
            View('demo', show_demo, (ctypes.c_bool * 1)  # type: ignore
                 (True), False),
        ]

        # gl
        import glglue.gl3.samplecontroller
        self.controller = glglue.gl3.samplecontroller.SampleController()
        self.data: Optional[GltfData] = None
        self.loader: Optional[gltf_loader.GltfLoader] = None

    def initialize(self, window: glfw._GLFWwindow):
        from .pyimgui_backend.glfw import GlfwRenderer
        self.impl_glfw = GlfwRenderer(window)
        from .pyimgui_backend.opengl import Renderer
        self.impl_gl = Renderer()
        self.show_json_tree = True

    def save_ini(self) -> bytes:
        return imgui.SaveIniSettingsToMemory()

    def __del__(self):
        del self.controller
        # save ini
        del self.impl_gl

    def _update(self):
        from .dockspace import dockspace
        with dockspace('docking_space'):
            import fontawesome47.icons_str as ICONS_FA

            if imgui.Button(ICONS_FA.ARROW_LEFT):
                self.tree.back()

            imgui.SameLine()
            if imgui.Button(ICONS_FA.ARROW_RIGHT):
                self.tree.forward()

        #
        # imgui menu
        #
        if imgui.BeginMainMenuBar():
            if imgui.BeginMenu(b"File", True):

                if imgui.MenuItem(b"Quit", b'Cmd+Q', False, True):
                    exit(1)
                imgui.EndMenu()

            if imgui.BeginMenu(b"View", True):
                for v in self.views:
                    imgui.MenuItem_2(v.name, b'', v.visible)
                imgui.EndMenu()

            imgui.EndMainMenuBar()

        #
        # imgui widgets
        #
        for v in self.views:
            selected = v.draw()
            if selected:
                self.tree.push(selected)

        self.prop.set(self.data, self.tree.get_selected(), self.loader)

    def _update_view(self):
        w, h = self.io.DisplaySize
        self.controller.onResize(w, h)
        x, y = self.io.MousePos
        if self.io.MouseDown[0]:
            self.controller.onLeftDown(x, y)
        else:
            self.controller.onLeftUp(x, y)
        if self.io.MouseDown[1]:
            self.controller.onRightDown(x, y)
        else:
            self.controller.onRightUp(x, y)
        if self.io.MouseDown[2]:
            self.controller.onMiddleDown(x, y)
        else:
            self.controller.onMiddleUp(x, y)
        if self.io.MouseWheel:
            self.controller.onWheel(int(-self.io.MouseWheel))
        self.controller.onMotion(x, y)

    def _new_frame(self):
        self.impl_glfw.process_inputs()
        imgui.NewFrame()
        self._update()

        # update controller
        if not self.io.WantCaptureMouse:
            self._update_view()

        imgui.Render()

    def render(self):
        self._new_frame()

        # render
        GL.glClearColor(1., 1., 1., 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        self.controller.draw()

        self.impl_gl.render(imgui.GetDrawData())

    def open(self, file: pathlib.Path):
        logger.info(f'load: {file.name}')
        self.file = None
        self.data = None
        self.tree.root = None

        try:
            import gltfio
            self.data = gltfio.parse_path(file)
            self.file = file
            self.tree.root = self.data.gltf
            self.tree.push(())

            # load opengl scene
            self.loader = gltf_loader.GltfLoader(self.data)
            scene = self.loader.load()
            scene.calc_world()
            self.controller.scene.drawables = [scene]  # type: ignore

            # fit camera
            from glglue.ctypesmath import AABB
            aabb = AABB.new_empty()
            aabb = scene.expand_aabb(aabb)
            self.controller.camera.fit(*aabb)

            # animation
            if self.loader.animations:
                self.playback.time = self.loader.animations[0].last_time

        except Exception as e:
            logger.exception(e)
