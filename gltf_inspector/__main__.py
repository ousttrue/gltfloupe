from logging import getLogger
logger = getLogger(__name__)
import pathlib
from OpenGL.GL import *
from PySide2.QtWidgets import (QApplication, QMainWindow, QAction, QFileDialog,
                               QTreeView, QDockWidget, QTextEdit)
from PySide2 import QtCore
from PySide2.QtGui import *
from . import json_tree
import re
from typing import Union


class Controller:
    """
    [CLASSES] Controllerクラスは、glglueの規約に沿って以下のコールバックを実装する
    """
    def __init__(self):
        pass

    def onResize(self, w, h):
        logger.debug('onResize: %d, %d', w, h)
        glViewport(0, 0, w, h)

    def onLeftDown(self, x, y):
        logger.debug('onLeftDown: %d, %d', x, y)

    def onLeftUp(self, x, y):
        logger.debug('onLeftUp: %d, %d', x, y)

    def onMiddleDown(self, x, y):
        logger.debug('onMiddleDown: %d, %d', x, y)

    def onMiddleUp(self, x, y):
        logger.debug('onMiddleUp: %d, %d', x, y)

    def onRightDown(self, x, y):
        logger.debug('onRightDown: %d, %d', x, y)

    def onRightUp(self, x, y):
        logger.debug('onRightUp: %d, %d', x, y)

    def onMotion(self, x, y):
        logger.debug('onMotion: %d, %d', x, y)

    def onWheel(self, d):
        logger.debug('onWheel: %d', d)

    def onKeyDown(self, keycode):
        logger.debug('onKeyDown: %d', keycode)

    def onUpdate(self, d):
        #logger.debug('onUpdate: delta %d ms', d)
        pass

    def draw(self):
        glClearColor(0.0, 0.0, 1.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glBegin(GL_TRIANGLES)
        glVertex(-1.0, -1.0)
        glVertex(1.0, -1.0)
        glVertex(0.0, 1.0)
        glEnd()

        glFlush()


class Window(QMainWindow):
    def __init__(self, parent=None):
        import glglue.pyside2gl
        super().__init__(parent)

        self.resize(1280, 1024)
        self.create_menu()

        # # setup opengl widget
        # self.controller = Controller()
        # self.glwidget = glglue.pyside2gl.Widget(self, self.controller)
        # self.setCentralWidget(self.glwidget)
        
        # left json tree
        self.dock_left = QDockWidget("json", self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_left)
        self.json_tree = QTreeView(self.dock_left)
        self.dock_left.setWidget(self.json_tree)

        # right selected panel
        self.dock_right = QDockWidget("active", self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_right)
        self.text = QTextEdit(self)
        self.dock_right.setWidget(self.text)

    def create_menu(self):
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu("File")
        # viewMenu = mainMenu.addMenu("View")
        # editMenu = mainMenu.addMenu("Edit")
        # searchMenu = mainMenu.addMenu("Font")
        # helpMenu = mainMenu.addMenu("Help")

        openAction = QAction(QIcon('open.png'), "Open", self)
        openAction.setShortcut("Ctrl+O")
        openAction.triggered.connect(self.open_dialog)
        fileMenu.addAction(openAction)

        # saveAction = QAction(QIcon('save.png'), "Save", self)
        # saveAction.setShortcut("Ctrl+S")
        # fileMenu.addAction(saveAction)

        exitAction = QAction(QIcon('exit.png'), "Exit", self)
        exitAction.setShortcut("Ctrl+X")
        exitAction.triggered.connect(self.exit_app)
        fileMenu.addAction(exitAction)

    def exit_app(self):
        self.close()

    def open_dialog(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setFilter(QtCore.QDir.Files)
        dlg.setNameFilters(['*.gltf;*.glb;*.vrm;*.vci', '*'])
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            if filenames and len(filenames) > 0:
                self.open(pathlib.Path(filenames[0]))

    def open(self, file: pathlib.Path):
        print(file)
        self.setWindowTitle(str(file.name))

        ext = file.suffix.lower()
        gltf_json = None
        import json
        if ext == '.gltf':
            gltf_json_src = file.read_text(encoding='utf-8')
            self.open_json(json.loads(gltf_json_src), file.parent)
        elif ext in ['.glb', '.vrm', '.vci']:
            from . import glb
            gltf_json_src, bin = glb.parse_glb(file.read_bytes())
            self.open_json(json.loads(gltf_json_src), bin)
        else:
            print(f'unknown: {ext}')

    def open_json(self, gltf_json: dict, bin: Union[bytes, pathlib.Path]):
        self.json_model = json_tree.TreeModel(gltf_json)
        self.json_tree.setModel(self.json_model)
        self.json_tree.selectionModel().selectionChanged.connect(
            self.on_selected)

        self.gltf_json = gltf_json
        if isinstance(bin, bytes):
            from .gltf_buffer_accessor import GlbBuffer
            self.bin = GlbBuffer(self.gltf_json, bin)
        else:
            NotImplementedError()

    def on_selected(self, selected, deselected):
        selected = selected.indexes()
        if not selected:
            return
        item = selected[0].internalPointer()
        if not isinstance(item, json_tree.Item):
            return

        json_path = item.json_path()
        m = re.match(r'^/skins/(\d+)$', json_path)
        if m:
            groups = m.groups()
            skin_index = int(groups[0])
            from . import skin_debug
            self.text.setText(
                skin_debug.info(self.bin, self.gltf_json, skin_index))
        else:
            self.text.setText(json_path)


def run():
    import sys
    from logging import basicConfig, DEBUG
    basicConfig(format='%(levelname)s:%(name)s:%(message)s', level=DEBUG)
    app = QApplication(sys.argv)
    window = Window()
    if len(sys.argv) > 1:
        window.open(pathlib.Path(sys.argv[1]))
    window.show()
    sys.exit(app.exec_())


run()
