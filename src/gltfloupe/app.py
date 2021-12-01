from typing import Optional, Dict
import pathlib
import logging
from PySide6 import QtWidgets, QtCore, QtGui
from . import json_tree
logger = logging.getLogger(__name__)


class Window(QtWidgets.QMainWindow):
    '''
    +----+----+----+
    |json|Open|Prop|
    |tree|GL  |    |
    +----+----+----+
    '''

    def __init__(self, parent=None):
        # import glglue.PySide6gl
        super().__init__(parent)
        self.docks: Dict[str, QtWidgets.QDockWidget] = {}

        self.icon_map = {
            'folder': self.style().standardIcon(QtWidgets.QStyle.SP_DirClosedIcon),
            'node': self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogInfoView),
            'buffer': self.style().standardIcon(QtWidgets.QStyle.SP_DriveHDIcon),
            'material': self.style().standardIcon(QtWidgets.QStyle.SP_DialogYesButton),
            'mesh': self.style().standardIcon(QtWidgets.QStyle.SP_DialogNoButton),
        }

        # setup opengl widget
        import glglue.gl3.samplecontroller
        self.controller = glglue.gl3.samplecontroller.SampleController()
        import glglue.pyside6
        import glglue.utils
        self.glwidget = glglue.pyside6.Widget(
            self, self.controller, glglue.utils.get_desktop_scaling_factor())
        self.setCentralWidget(self.glwidget)

        # left json tree
        self.json_tree = QtWidgets.QTreeView(self)
        dock_left = self._add_dock("json", QtGui.Qt.LeftDockWidgetArea)
        dock_left.setWidget(self.json_tree)

        # right selected panel
        self.text = QtWidgets.QTextEdit(self)
        dock_right = self._add_dock("active", QtGui.Qt.RightDockWidgetArea)
        dock_right.setWidget(self.text)

        # logger
        self.logger = glglue.pyside6.QPlainTextEditLogger(self)
        logging.getLogger('').addHandler(self.logger.log_handler)
        dock_bottom = self._add_dock("logger", QtGui.Qt.BottomDockWidgetArea)
        dock_bottom.setWidget(self.logger)

        # menu
        self.mainMenu = self.menuBar()
        self._file_menu(self.mainMenu.addMenu("File"))
        self._view_menu(self.mainMenu.addMenu("View"))

    def _add_dock(self, name: str, area: QtGui.Qt.Orientation) -> QtWidgets.QDockWidget:
        dock = QtWidgets.QDockWidget(name, self)
        self.addDockWidget(area, dock)
        self.docks[name] = dock
        return dock

    def _file_menu(self, fileMenu: QtWidgets.QMenu):
        openAction = QtGui.QAction(QtGui.QIcon('open.png'), "Open", self)
        openAction.setShortcut("Ctrl+O")
        openAction.triggered.connect(self.open_dialog)  # type: ignore
        fileMenu.addAction(openAction)

        fileMenu.addSeparator()

        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), "Exit", self)
        exitAction.setShortcut("Ctrl+X")
        exitAction.triggered.connect(self.exit_app)  # type: ignore
        fileMenu.addAction(exitAction)

    def _view_menu(self, viewMenu: QtWidgets.QMenu):
        for _, v in self.docks.items():
            viewMenu.addAction(v.toggleViewAction())

    def exit_app(self):
        self.close()

    def open_dialog(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dlg.setFilter(QtCore.QDir.Files)
        dlg.setNameFilters(['*.gltf;*.glb;*.vrm;*.vci', '*'])
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            if filenames and len(filenames) > 0:
                self.open(pathlib.Path(filenames[0]))

    def open(self, file: pathlib.Path):
        logger.info(f'load: {file.name}')

        import gltfio
        try:
            self.gltf = gltfio.parse_path(file)
            self.setWindowTitle(str(file.name))

            # opengl
            from .gltf_loader import GltfLoader
            loader = GltfLoader(self.gltf)
            scene = loader.load()
            self.controller.scene.drawables = [scene]
            from glglue.ctypesmath import AABB
            aabb = AABB.new_empty()
            aabb = scene.expand_aabb(aabb)
            self.controller.camera.fit(*aabb)
            self.glwidget.repaint()

            # json
            self.open_json(self.gltf.gltf, file, self.gltf.bin)

        except Exception as e:
            logger.exception(e)

    def open_json(self, gltf_json: dict, path: pathlib.Path, bin: Optional[bytes]):
        self.gltf_json = gltf_json

        self.json_model = json_tree.TreeModel(gltf_json, self.icon_map)
        self.json_tree.setModel(self.json_model)
        self.json_tree.selectionModel().selectionChanged.connect(  # type: ignore
            self.on_selected)
        self.bin = bin

    def on_selected(self, selected, deselected):
        selected = selected.indexes()
        if not selected:
            return
        item = selected[0].internalPointer()
        if not isinstance(item, json_tree.Item):
            return

        match item.json_path():
            case ('skins', skin_index, *_):
                skin_index = int(skin_index)
                from . import skin_debug
                self.text.setText(
                    skin_debug.info(self.gltf, skin_index))
            case json_path:
                self.text.setText('/'.join(json_path))


def run():
    import sys
    from logging import basicConfig, DEBUG
    basicConfig(format='%(levelname)s:%(name)s:%(message)s', level=DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.resize(1280, 1024)
    if len(sys.argv) > 1:
        window.open(pathlib.Path(sys.argv[1]))
    window.show()
    sys.exit(app.exec_())
