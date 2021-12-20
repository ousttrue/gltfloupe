from typing import Optional
import pathlib
import ctypes
import logging
#
from glglue.gl3.cydeercontroller import CydeerController
#
import cydeer as imgui
from cydeer.utils.dockspace import dockspace, DockView
#
from gltfio.parser import GltfData
from .. import gltf_loader

logger = logging.getLogger(__name__)


class GUI(CydeerController):
    def __init__(self, ini:  Optional[str]) -> None:
        super().__init__()

        # imgui
        imgui.CreateContext()
        self.io: imgui.ImGuiIO = imgui.GetIO()
        self.io.ConfigFlags |= imgui.ImGuiConfigFlags_.DockingEnable
        if isinstance(ini, str):
            imgui.LoadIniSettingsFromMemory(ini.encode('utf-8'))
        self.io.IniFilename = None  # type: ignore

        # views
        from .jsontree import JsonTree
        self.tree = JsonTree()

        from .loghandler import ImGuiLogHandler
        self.log_handler = ImGuiLogHandler()
        self.log_handler.setFormatter(logging.Formatter(
            '%(levelname)s:%(name)s:%(message)s'))
        logging.getLogger().handlers = [self.log_handler]

        from .prop import Prop
        self.prop = Prop()

        from .animation import Playback
        self.playback = Playback()

        from glglue.gl3.cameraview import CameraView
        self.view = CameraView()

        self.views = [
            DockView('json', (ctypes.c_bool * 1)(True), self.tree.draw),
            DockView('log', (ctypes.c_bool * 1)(True), self.log_handler.draw),
            DockView('prop', (ctypes.c_bool * 1)(True), self.prop.draw),
            DockView('playback', (ctypes.c_bool * 1)
                     (True), self.playback.draw),
            DockView('view', (ctypes.c_bool * 1)(True), self.view.draw),
            #
            DockView('metrics', (ctypes.c_bool * 1)
                     (True), imgui.ShowMetricsWindow),
            DockView('demo', (ctypes.c_bool * 1)(True), imgui.ShowDemoWindow),
        ]

        # gl
        self.data: Optional[GltfData] = None
        self.loader: Optional[gltf_loader.GltfLoader] = None

    def load_font(self):
        # font load
        from cydeer.utils import fontloader
        fontloader.load(pathlib.Path(
            'C:/Windows/Fonts/MSGothic.ttc'), 20.0, self.io.Fonts.GetGlyphRangesJapanese())
        import fontawesome47
        font_range = (ctypes.c_ushort * 3)(*fontawesome47.RANGE, 0)
        fontloader.load(fontawesome47.get_path(), 20.0,
                        font_range, merge=True, monospace=True)
        self.io.Fonts.Build()

    def save_ini(self) -> bytes:
        return imgui.SaveIniSettingsToMemory()

    def toolbar(self):
        import fontawesome47.icons_str as ICONS_FA

        if imgui.Button(ICONS_FA.ARROW_LEFT):
            self.tree.back()

        imgui.SameLine()
        if imgui.Button(ICONS_FA.ARROW_RIGHT):
            self.tree.forward()

    def menu(self):
        if imgui.BeginMenu(b"File", True):

            if imgui.MenuItem(b"Quit", b'Cmd+Q', False, True):
                exit(1)
            imgui.EndMenu()

    def draw_imgui(self):
        # update scene
        if self.loader:
            pos = self.playback.pos[0]
            self.loader.set_time(pos)

        dockspace(*self.views, toolbar=self.toolbar, menu=self.menu)

        if self.prop.selected:
            self.tree.push(self.prop.selected)

        self.prop.set(self.data, self.tree.get_selected(), self.loader)

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
            self.view.rendertarget.scene.drawables = [scene]  # type: ignore

            # fit camera
            from glglue.ctypesmath import AABB
            aabb = AABB.new_empty()
            aabb = scene.expand_aabb(aabb)
            self.view.rendertarget.camera.fit(*aabb)

            # animation
            if self.loader.animations:
                self.playback.time = self.loader.animations[0].last_time

        except Exception as e:
            logger.exception(e)
