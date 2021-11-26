from . import json_tree
from PySide6 import QtWidgets, QtCore, QtGui
from typing import Optional, Union
import re
import pathlib
from logging import getLogger
logger = getLogger(__name__)


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

        self.resize(1280, 1024)
        self.create_menu()

        # setup opengl widget
        import glglue.gl3.samplecontroller
        self.controller = glglue.gl3.samplecontroller.SampleController()
        import glglue.pyside6
        import glglue.utils
        self.glwidget = glglue.pyside6.Widget(
            self, self.controller, glglue.utils.get_desktop_scaling_factor())
        self.setCentralWidget(self.glwidget)

        # left json tree
        self.dock_left = QtWidgets.QDockWidget("json", self)
        self.addDockWidget(QtGui.Qt.LeftDockWidgetArea, self.dock_left)
        self.json_tree = QtWidgets.QTreeView(self.dock_left)
        self.dock_left.setWidget(self.json_tree)

        # right selected panel
        self.dock_right = QtWidgets.QDockWidget("active", self)
        self.addDockWidget(QtGui.Qt.RightDockWidgetArea, self.dock_right)
        self.text = QtWidgets.QTextEdit(self)
        self.dock_right.setWidget(self.text)

        # logger
        import logging
        self.logger = glglue.pyside6.QPlainTextEditLogger(self)
        logging.getLogger('').addHandler(self.logger.log_handler)
        self.dock_bottom = QtWidgets.QDockWidget("logger", self)
        self.addDockWidget(QtGui.Qt.BottomDockWidgetArea, self.dock_bottom)
        self.dock_bottom.setWidget(self.logger)

    def create_menu(self):
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu("File")
        # viewMenu = mainMenu.addMenu("View")
        # editMenu = mainMenu.addMenu("Edit")
        # searchMenu = mainMenu.addMenu("Font")
        # helpMenu = mainMenu.addMenu("Help")

        openAction = QtGui.QAction(QtGui.QIcon('open.png'), "Open", self)
        openAction.setShortcut("Ctrl+O")
        openAction.triggered.connect(self.open_dialog)  # type: ignore
        fileMenu.addAction(openAction)

        # saveAction = QAction(QIcon('save.png'), "Save", self)
        # saveAction.setShortcut("Ctrl+S")
        # fileMenu.addAction(saveAction)

        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), "Exit", self)
        exitAction.setShortcut("Ctrl+X")
        exitAction.triggered.connect(self.exit_app)  # type: ignore
        fileMenu.addAction(exitAction)

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
        self.setWindowTitle(str(file.name))
        import gltfio
        self.gltf = gltfio.parse_path(file)

        # opengl
        import glglue.gltf_loader
        loader = glglue.gltf_loader.GltfLoader(self.gltf)
        scene = loader.load()
        self.controller.drawables = [scene]
        self.glwidget.repaint()

        # json
        self.open_json(self.gltf.gltf, file, self.gltf.bin)

    def open_json(self, gltf_json: dict, path: pathlib.Path, bin: Optional[bytes]):
        self.gltf_json = gltf_json
        self.json_model = json_tree.TreeModel(gltf_json)
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

        json_path = item.json_path()
        m = re.match(r'^/skins/(\d+)$', json_path)
        if self.gltf and m:
            groups = m.groups()
            skin_index = int(groups[0])
            from . import skin_debug
            self.text.setText(
                skin_debug.info(self.gltf, skin_index))
        else:
            self.text.setText(json_path)


def run():
    import sys
    from logging import basicConfig, DEBUG
    basicConfig(format='%(levelname)s:%(name)s:%(message)s', level=DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    if len(sys.argv) > 1:
        window.open(pathlib.Path(sys.argv[1]))
    window.show()
    sys.exit(app.exec_())
