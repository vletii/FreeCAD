# SPDX-License-Identifier: LGPL-2.1-or-later
# /**************************************************************************
#                                                                           *
#    Copyright (c) 2025 Ondsel <development@ondsel.com>                     *
#                                                                           *
#    This file is part of FreeCAD.                                          *
#                                                                           *
#    FreeCAD is free software: you can redistribute it and/or modify it     *
#    under the terms of the GNU Lesser General Public License as            *
#    published by the Free Software Foundation, either version 2.1 of the   *
#    License, or (at your option) any later version.                        *
#                                                                           *
#    FreeCAD is distributed in the hope that it will be useful, but         *
#    WITHOUT ANY WARRANTY; without even the implied warranty of             *
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU       *
#    Lesser General Public License for more details.                        *
#                                                                           *
#    You should have received a copy of the GNU Lesser General Public       *
#    License along with FreeCAD. If not, see                                *
#    <https://www.gnu.org/licenses/>.                                       *
#                                                                           *
# **************************************************************************/

import re
import os
import FreeCAD as App

from PySide.QtCore import QT_TRANSLATE_NOOP

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtWidgets
    from PySide.QtSvg import QSvgRenderer
    from PySide.QtWidgets import (
        QMainWindow, 
        QGraphicsView, 
        QGraphicsScene, 
        QFileDialog, 
        QFileDialog, 
        QMessageBox
    )
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

        self.dependency_map = None
        self.form = Gui.PySideUic.loadUi(":/panels/TaskAssemblyCreateDependencyMap.ui")

        self.form.btnGenerate.clicked.connect(self.renderMap)
        self.form.btnExport.clicked.connect(self.exportMap)

    def renderMap(self):            
        self.assembly = UtilsAssembly.activeAssembly()
        if not self.assembly:
            return
        self.g = graphviz.Graph()
        self.g.attr()

        self.addNodesToGraph(self.g)
        self.addEdgesToGraph(self.g, self.assembly)

        self.visualizeMap()
        
    def exportMap(self):
        filters = "PNG (*.png);;JPEG (*.jpg *.jpeg);;Bitmap " \
"(*.bmp);;Scalable Vector Graphics (*.svg);;PDF (*.pdf)"
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
                s.node(part.Label, style="filled", fillcolor="powderblue")
        

    def addsSubGraphNodes(self, g, assembly):
        if self.form.CheckBox_ShowSubAssemblies.isChecked():
            with g.subgraph(name = 'cluster_' + assembly.Name) as s:
                s.attr(style="filled", color= "lightgoldenrod1", label=assembly.Name)
                subassembly = UtilsAssembly.getSubAssemblies(assembly)
                for sub in subassembly:
                    self.addsSubGraphNodes(g, sub)
                for obj in UtilsAssembly.getParts(assembly):
                    s.node(obj.Label, label=obj.Label,  style="filled", fillcolor="powderblue")
        else:
            g.node(assembly.Label, label=assembly.Label, style="filled", fillcolor="lightgoldenrod1")

    def addEdgesToGraph(self, g, assembly):
        joints = assembly.Joints
        for joint in joints:
            part1 = UtilsAssembly.getMovingPart(assembly, joint.Reference1)
            part2 = UtilsAssembly.getMovingPart(assembly, joint.Reference2)
            if not self.form.CheckBox_ShowSubAssemblies.isChecked() and part1 and part2:
                part1 = UtilsAssembly.getAssemblyfromPart(part1)
                part2 = UtilsAssembly.getAssemblyfromPart(part2)
            if part1 and part2 and part1.Label != part2.Label:
                if self.form.CheckBox_ShowJoints.isChecked():
                    g.edge(part1.Label, part2.Label, label=joint.Label)
                else:
                    g.edge(part1.Label, part2.Label)
        groundedjoints = UtilsAssembly.getGroundedJoints(assembly)
        if groundedjoints:
            g.node("Ground", label="Ground", style="filled", fillcolor="salmon")
        for joint in groundedjoints:
            part = joint.ObjectToGround
            if not self.form.CheckBox_ShowSubAssemblies.isChecked() and part:
                part = UtilsAssembly.getAssemblyfromPart(part)
            if part:
                if self.form.CheckBox_ShowJoints.isChecked():
                    g.edge(part.Label, "Ground", style="dotted", label=joint.Label)
                else:
                    g.edge(part.Label, "Ground", style="dotted")

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
            self.dependency_map = GraphvizSvgView(self.svg_data, None)
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
        self.svg_item.setSharedRenderer(self.renderer)
        self.view.resetTransform()
        self.scene.update() 
        self.svg_item.update()
        self._zoom = 0


if App.GuiUp:
    Gui.addCommand("Assembly_CreateDependencyMap", CommandCreateDependencyMap())