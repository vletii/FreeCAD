import os
import FreeCAD as App

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QFileDialog
    from PySide2.QtCore import Qt, QPointF
    from PySide2.QtGui import QPainter, QPen, QBrush, QImage
    from PySide2.QtSvg import QSvgRenderer, QGraphicsSvgItem

from PIL import Image as PILImage
import UtilsAssembly


class CommandCreateDependencyMap:
    def GetResources(self):
        return {
            "Pixmap": "Assembly_ExportASMT",
            "MenuText": "Create a Dependency Map",
            "ToolTip": "Create a Dependency Map",
        }

    def IsActive(self):
        return UtilsAssembly.isAssemblyCommandActive()

    def Activated(self):
        assembly = UtilsAssembly.activeAssembly()
        if not assembly:
            return
        panel = TaskAssemblyCreateDependencyMap()
        Gui.Control.showDialog(panel)

class TaskAssemblyCreateDependencyMap(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.assembly = UtilsAssembly.activeAssembly()
        if not self.assembly:
            return

        self.form = Gui.PySideUic.loadUi(":/panels/TaskAssemblyCreateDependencyMap.ui")

        self.form.btnGenerate.clicked.connect(self.renderMap)
        self.form.btnExport.clicked.connect(self.exportMap)

        self.window = QtWidgets.QMainWindow()
        self.window.setWindowTitle("Dependency Map")
        self.scene = QGraphicsScene()
        self.view = DependencyMapView(self.scene)
        self.window.setCentralWidget(self.view)
        self.nodes = {}

    def renderMap(self):
        self.scene.clear()
        self.nodes.clear()
        start_y = 0
        self.add_parts(self.assembly, 0, start_y)
        self.visualize()

    def add_parts(self, assembly, x, y, parent_pos=None):
        label = assembly.Name
        pos = QPointF(x, y)
        rect = self.scene.addRect(x, y, 120, 40, QtGui.QPen(Qt.black), QtGui.QBrush(Qt.lightGray))
        text = self.scene.addText(label)
        text.setPos(x + 10, y + 10)
        self.nodes[label] = pos

        if parent_pos:
            self.drawEdge(parent_pos, pos)

        y_offset = y + 120
        for part in UtilsAssembly.getParts(assembly):
            p_label = part.Label
            part_pos = QPointF(x + 160, y_offset)
            rect = self.scene.addRect(part_pos.x(), part_pos.y(), 100, 40, QtGui.QPen(Qt.black), QtGui.QBrush(Qt.cyan))
            text = self.scene.addText(p_label)
            text.setPos(part_pos.x() + 10, part_pos.y() + 10)
            self.nodes[p_label] = part_pos
            self.drawEdge(pos, part_pos)
            y_offset += 120

        for sub in UtilsAssembly.getSubAssemblies(assembly):
            y_offset += 40
            self.add_parts(sub, x + 160, y_offset, pos)

        # Draw edges for joints
        for joint in self.assembly.Joints:
            part1 = UtilsAssembly.getMovingPart(self.assembly, joint.Reference1)
            part2 = UtilsAssembly.getMovingPart(self.assembly, joint.Reference2)
            if part1 and part2 and part1.Label in self.nodes and part2.Label in self.nodes:
                self.drawEdge(self.nodes[part1.Label], self.nodes[part2.Label], color=Qt.red)


    def drawEdge(self, start, end, color=Qt.black):
        line = QtCore.QLineF(start + QPointF(60, 20), end + QPointF(0, 20))
        pen = QtGui.QPen(color, 2)
        self.scene.addLine(line, pen)


    def visualize(self):
        mdi_area = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
        if mdi_area:
            sub_window = mdi_area.addSubWindow(self.view)
            sub_window.show()
        else:
            self.window.show()

    def exportMap(self):
        filters = "PNG (*.png);;JPEG (*.jpg *.jpeg);;Bitmap (*.bmp);;PDF (*.pdf)"
        path, selected_filter = QFileDialog.getSaveFileName(None, "Export Dependency Map", "", filters)

        if not path:
            return

        if "PNG" in selected_filter:
            fmt = "PNG"
        elif "JPEG" in selected_filter:
            fmt = "JPEG"
        elif "Bitmap" in selected_filter:
            fmt = "BMP"
        elif "Scalable" in selected_filter:
            fmt = "SVG"
        elif "PDF" in selected_filter:
            fmt = "pdf"

        if not path.lower().endswith(f".{fmt.lower()}"):
            path += f".{fmt.lower()}"

        rect = self.scene.sceneRect()

        image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.white)
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()

        if fmt == "pdf": # Save as temporary PNG, then convert to PDF using Pillow
            temp_png = path[:-4] + "_temp_export.png"
            image.save(temp_png)
            pil_img = PILImage.open(temp_png)
            pil_img.save(path, "PDF", resolution=100.0)
            os.remove(temp_png)

        else:
            image.save(path)

    def accept(self):
        self.deactivate()
        return True

    def reject(self):
        self.deactivate()
        return True

    def deactivate(self):
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()


class DependencyMapView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        self._zoom = 0

    def wheelEvent(self, event):
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor

        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
            self._zoom += 1
        else:
            zoomFactor = zoomOutFactor
            self._zoom -= 1

        self.scale(zoomFactor, zoomFactor)

    def mouseDoubleClickEvent(self, event):
        self.resetTransform()
        self._zoom = 0
        super().mouseDoubleClickEvent(event)


if App.GuiUp:
    Gui.addCommand("Assembly_CreateDependencyMap", CommandCreateDependencyMap())
