import os
import FreeCAD as App

from PySide.QtCore import QT_TRANSLATE_NOOP

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui, QtWidgets
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
            "Pixmap": "Assembly_ExportASMT",
            "MenuText": QT_TRANSLATE_NOOP("Assembly_CreateDependencyMap", "Create a Dependency Map"),
            # "Accel": "Z", # shortcut key - define later maybe
            "ToolTip": QT_TRANSLATE_NOOP(
                "Assembly_CreateDependencyMap",
                "Create a Dependency Map",
            ),
            # "CmdType": "ForEdit", # not needed i think?
        }

    def IsActive(self):
        return UtilsAssembly.isAssemblyCommandActive()

    def Activated(self):

        assembly = UtilsAssembly.activeAssembly()
        if not assembly:
            return

        Gui.addModule("UtilsAssembly")
        panel = TaskAssemblyCreateDependencyMap()
        Gui.Control.showDialog(panel)

if App.GuiUp:
    Gui.addCommand("Assembly_CreateDependencyMap", CommandCreateDependencyMap())

   
class TaskAssemblyCreateDependencyMap(QtWidgets.QDialog):
    def __init__(self):  
        super().__init__()
        self.assembly = UtilsAssembly.activeAssembly()

        if not self.assembly:
            return

        self.setWindowTitle("Assembly Dependency Map")
        self.form = Gui.PySideUic.loadUi(":/panels/TaskAssemblyCreateDependencyMap.ui")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.form)

        # generate button
        self.form.btnGenerate.clicked.connect(self.updateGraph)
        
        # buttonBox = QDialogButtonBox(QDialogButtonBox.hidejoints)

        # self.hideJoints = QtWidgets.QCheckBox("Hide Joints")
        # self.hideJoints.setChecked(True)

        self.updateGraph()

        #render the graph
        self.g.render(filename="assembly_dependency_map", format="png")
        self.g.view()  # Open the rendered graph in the default viewer

    def updateGraph(self):
        self.g = graphviz.Graph()
        self.g.attr()

        self.addNodesToGraph(self.g)
        self.addEdgesToGraph(self.g, self.assembly)

    

    def addNodesToGraph(self, g):
        assembly = UtilsAssembly.activeAssembly()
        subassembly = UtilsAssembly.getSubAssemblies(assembly)
        for sub in subassembly:
            self.addsSubGraphNodes(g, sub)
        with g.subgraph(name = 'cluster_0 ') as s:
            print("Getparts")
            for part in UtilsAssembly.getParts(assembly):
                print("----Assembly parts:" + part.Label + " " + part.Name)
                s.node(part.Name, style="filled", fillcolor="lightgrey")
        

    def addsSubGraphNodes(self, g, assembly):
        #subgraph
        with g.subgraph(name = 'cluster_' + assembly.Name) as s:
            s.attr(style="filled", color= "lightpink", label=assembly.Name)
            print("Subgraph nodes:")
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
                #if hidejoints isnt checked
                # if self.hideJoints.isChecked() == False:
                #     g.node(joint.Label, label=joint.Label, style="filled", fillcolor = "green",shape='Mdiamond')
                #     g.edge(part1.Label, joint.Label)
                #     g.edge(joint.Label, part2.Label)
                # else:
                g.edge(part1.Label, part2.Label)

    def accept(self):
        self.deactivate()
        return True

    def reject(self):
        self.deactivate()
        return True

    def deactivate(self):
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()