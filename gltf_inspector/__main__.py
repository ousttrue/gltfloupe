from logging import getLogger
logger = getLogger(__name__)
import pathlib
from OpenGL.GL import *
from PySide2.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QTreeView, QDockWidget
from PySide2 import QtCore
from PySide2.QtGui import *


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

        self.resize(800, 600)

        # setup opengl widget
        self.controller = Controller()
        self.glwidget = glglue.pyside2gl.Widget(self, self.controller)
        self.setCentralWidget(self.glwidget)
        self.create_menu()

        # left json tree
        dock_left = QDockWidget("json", self)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_left)
        self.json_tree = QTreeView(dock_left)
        dock_left.setWidget(self.json_tree)

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
        if ext == '.gltf':
            gltf_json = file.read_text(encoding='utf-8')
        elif ext in ['.glb', '.vrm', '.vci']:
            from . import glb
            gltf_json, bin = glb.parse_glb(file.read_bytes())
        else:
            print(f'unknown: {ext}')


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
