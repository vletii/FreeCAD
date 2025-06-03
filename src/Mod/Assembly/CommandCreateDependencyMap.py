import os
import FreeCAD as App

from PySide.QtCore import QT_TRANSLATE_NOOP

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtWidgets
    from PySide.QtSvg import QSvgRenderer
    from PySide.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QFileDialog, QToolBar, QAction, QFileDialog
    from PySide2.QtGui import QImage, QPainter
    from PySide2.QtCore import Qt
    from PySide.QtSvg import QGraphicsSvgItem
    from PySide2.QtPrintSupport import QPrinter
    import graphviz

import UtilsAssembly
import Assembly_rc


title = "Assembly Command to show Dependency Map"
author = "Ondsel"
url = "https://www.freecad.org/"

class CommandCreateDependencyMap:
    def init(self):
        pass

    def GetResources(self):

        return {
            # TODO change pixmap icon
            "Pixmap": "Assembly_ExportASMT",
            "MenuText": QT_TRANSLATE_NOOP("Assembly_CreateDependencyMap", "Create a Dependency Map"),
            # "Accel": "Z", # shortcut key - define later maybe
            "ToolTip": QT_TRANSLATE_NOOP(
                "Assembly_CreateDependencyMap",
                "Create a Dependency Map",
            ),
        }

    def IsActive(self):
        return UtilsAssembly.isAssemblyCommandActive()

    def Activated(self):
        # print("Python: About to run Std_DependencyMap command")
        # print("Python: Finished running Std_DependencyMap command")
        assembly = UtilsAssembly.activeAssembly()
        if not assembly:
            return
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(assembly)
        Gui.runCommand("Std_DependencyMap")
        panel = TaskAssemblyCreateDependencyMap()
        Gui.Control.showDialog(panel)

class TaskAssemblyCreateDependencyMap(QtCore.QObject):
    def __init__(self):  
        super().__init__()
        self.assembly = UtilsAssembly.activeAssembly()

        if not self.assembly:
            return

        self.dependency_map = None
        self.form = Gui.PySideUic.loadUi(":/panels/TaskAssemblyCreateDependencyMap.ui")

        self.form.btnGenerate.clicked.connect(self.renderMap)
        # self.form.btnExport.clicked.connect(self.exportMap)

    def renderMap(self):
        print("Starting renderMap...")
        doc = self.assembly.Document
        print(f"Got active document: {doc.Name}")
        App.ParamGet("User parameter:BaseApp/Preferences/Assembly").SetString("TargetAssembly", assembly.Name)
        Gui.runCommand("Std_DependencyMap")


    # TODO check exportation
    def exportMap(self):
        filters = "PNG (*.png);;JPEG (*.jpg *.jpeg);;Bitmap (*.bmp);;Scalable Vector Graphics (*.svg);;PDF (*.pdf)"
        path, selected_filter = QFileDialog.getSaveFileName(None, "Export Dependency Map", "", filters)

        if not path:
            return

        if "PNG" in selected_filter:
            fmt = "png"
        elif "JPEG" in selected_filter:
            fmt = "jpg"
        elif "Bitmap" in selected_filter:
            fmt = "bmp"
        elif "Scalable" in selected_filter:
            fmt = "svg"
        elif "PDF" in selected_filter:
            fmt = "pdf"
        else:
            fmt = "png"

        if not path.lower().endswith(f".{fmt}"):
            path += f".{fmt}"

        # Handle SVG export directly
        if fmt == "svg":
            with open(path, "wb") as f:
                f.write(self.svg_data)
            return

        # Use QSvgRenderer to render to image
        renderer = QSvgRenderer(self.svg_data)
        bounds = renderer.viewBoxF()
        size = bounds.size().toSize()

        if size.width() == 0 or size.height() == 0:
            return

        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        renderer.render(painter)
        painter.end()

        if fmt == "pdf":
            image.save(path, "PDF")
        else:
            image.save(path, fmt.upper())

    def accept(self):
        self.deactivate()
        return True

    def reject(self):
        self.deactivate()
        return True

    def deactivate(self):
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()


class GraphvizSvgView(QMainWindow):
    def __init__(self, svg_data, dependency_map, parent=None):
        super().__init__(parent)
        self.dependency_map = dependency_map
        self.setWindowTitle("Dependency Graph")
        self._zoom = 0

        self.scene = QGraphicsScene(self)
        self.renderer = QSvgRenderer(svg_data, self)
        self.svg_item = QGraphicsSvgItem()
        self.svg_item.setSharedRenderer(self.renderer)
        self.scene.addItem(self.svg_item)

        self.view = QGraphicsView(self.scene, self)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        self.setCentralWidget(self.view)

    def wheelEvent(self, event):
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor

        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
            self._zoom += 1
        else:
            zoomFactor = zoomOutFactor
            self._zoom -= 1

        self.view.scale(zoomFactor, zoomFactor)
    
    def updateSvg(self, svg_data):
        self.renderer.load(svg_data)
        self.view.resetTransform()
        self._zoom = 0


if App.GuiUp:
    Gui.addCommand("Assembly_CreateDependencyMap", CommandCreateDependencyMap())