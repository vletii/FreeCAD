import os
import FreeCAD as App

from PySide.QtCore import QT_TRANSLATE_NOOP

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtWidgets
    from PySide.QtSvg import QSvgRenderer
    from PySide.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QFileDialog, QFileDialog, QMessageBox
    from PySide2.QtGui import QImage, QPainter
    from PySide2.QtCore import Qt
    from PySide.QtSvg import QGraphicsSvgItem
    
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    graphviz = None
    GRAPHVIZ_AVAILABLE = False

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
            "ToolTip": QT_TRANSLATE_NOOP(
                "Assembly_CreateDependencyMap",
                "Create a Dependency Map",
            ),
        }

    def IsActive(self):
        return UtilsAssembly.isAssemblyCommandActive()

    def Activated(self):
        assembly = UtilsAssembly.activeAssembly()
        if not assembly:
            return
        if not GRAPHVIZ_AVAILABLE:
            QMessageBox.warning(
                Gui.getMainWindow(),
                "Feature Not Available.",
                "Cannot render map: graphviz library is not installed."
            )
            return

        Gui.addModule("UtilsAssembly")

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
        self.form.btnExport.clicked.connect(self.exportMap)

    def renderMap(self):            
        self.g = graphviz.Graph()
        self.g.attr()

        self.addNodesToGraph(self.g)
        self.addEdgesToGraph(self.g, self.assembly)

        self.visualizeMap()
        
    def exportMap(self):
        filters = "PNG (*.png);;JPEG (*.jpg *.jpeg);;Bitmap (*.bmp);;Scalable Vector Graphics (*.svg);;PDF (*.pdf)"
        path, selected_filter = QFileDialog.getSaveFileName(None, "Export Dependency Map", "", filters)

        if not path:
            return

        if "PNG" in selected_filter:
            fmt = "png"
        elif "JPEG" in selected_filter:
            fmt = "jpeg"
        elif "Bitmap" in selected_filter:
            fmt = "bmp"
        elif "Scalable" in selected_filter:
            fmt = "svg"
        elif "PDF" in selected_filter:
            fmt = "pdf"

        if not path.lower().endswith(f".{fmt}"):
            path += f".{fmt}"

        if fmt == "svg":
            try:
                with open(path, "wb") as f:
                    f.write(self.svg_data)
                success = True
            except Exception as e:
                success = False

        elif fmt == 'pdf':
            try:
                pdf_data = self.g.pipe(format='pdf')
                with open(path, 'wb') as f:
                    f.write(pdf_data)
                success = True
            except Exception as e:
                success = False
        else: 
            self.renderer = QSvgRenderer(self.svg_data)
            bounds = self.renderer.viewBoxF()
            size = bounds.size().toSize()

            if size.width() == 0 or size.height() == 0:
                success = False

            image = QImage(size, QImage.Format_ARGB32)
            image.fill(Qt.transparent)

            painter = QPainter(image)
            self.renderer.render(painter)
            painter.end()

            success = image.save(path, fmt)

        self.showExportState(success, path)

    def showExportState(self, success, path):
        if success:
            QMessageBox.information(
                    Gui.getMainWindow() if 'Gui' in globals() else None,
                    "Export Successful",
                    f"Dependency map exported successfully to:\n{path}"
            )
        else: 
            QMessageBox.warning(
                    Gui.getMainWindow() if 'Gui' in globals() else None,
                    "Export Error",
                    f"Failed to save image to {path}"
            )

    def addNodesToGraph(self, g):
        assembly = UtilsAssembly.activeAssembly()
        subassembly = UtilsAssembly.getSubAssemblies(assembly)
        for sub in subassembly:
            self.addsSubGraphNodes(g, sub)
        with g.subgraph(name = 'cluster_0 ') as s:
            for part in UtilsAssembly.getParts(assembly):
                s.node(part.Name, style="filled", fillcolor="lightgrey")
        

    def addsSubGraphNodes(self, g, assembly):
        #subgraph
        with g.subgraph(name = 'cluster_' + assembly.Name) as s:
            s.attr(style="filled", color= "lightpink", label=assembly.Name)
            subassembly = UtilsAssembly.getSubAssemblies(assembly)
            for sub in subassembly:
                self.addsSubGraphNodes(g, sub)
            for obj in UtilsAssembly.getParts(assembly):
                s.node(obj.Label, label=obj.Label,  style="filled", fillcolor="lightblue")

    def addEdgesToGraph(self, g, assembly):
        joints = assembly.Joints
        for joint in joints:
            #g.node(joint.Label, label=joint.Label, style="filled", fillcolor = "green",shape='Mdiamond')
            part1 = UtilsAssembly.getMovingPart(assembly, joint.Reference1)
            part2 = UtilsAssembly.getMovingPart(assembly, joint.Reference2)
            if part1 and part2:
                # g.edge(part1.Label, joint.Label)
                # g.edge(joint.Label, part2.Label)
                
                if self.form.CheckBox_ShowJoints.isChecked(): # if show joints
                    g.edge(part1.Label, part2.Label, style="dashed", color="blue", label=joint.Label, labelfloat="true")
                #     g.node(joint.Label, label=joint.Label, style="filled", fillcolor = "green",shape='Mdiamond')
                #     g.edge(part1.Label, joint.Label)
                #     g.edge(joint.Label, part2.Label)
                # else:
                else:
                    g.edge(part1.Label, part2.Label)

    def visualizeMap(self):
        self.svg_data = self.g.pipe(format="svg")

        mdi_area = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)

        if not mdi_area: 
            return

        if self.dependency_map:
            self.dependency_map.updateSvg(self.svg_data)
            self.dependency_map.raise_()
            self.dependency_map.activateWindow()
        else:
            self.dependency_map = GraphvizSvgView(self.svg_data, self.dependency_map)
            sub_window = mdi_area.addSubWindow(self.dependency_map)
            sub_window.show()

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