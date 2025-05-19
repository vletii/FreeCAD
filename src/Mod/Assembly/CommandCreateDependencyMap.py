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
        # return App.ActiveDocument is not None
        return UtilsAssembly.isAssemblyCommandActive()

    def Activated(self):
        print("CommandCreateDependencyMap.Activated()")
        
        assembly = UtilsAssembly.activeAssembly()
        if not assembly:
            return

        Gui.addModule("UtilsAssembly")
        # App.setActiveTransaction("Create a Dependency Map")
        # App.closeActiveTransaction()

        Gui.doCommand("assembly = UtilsAssembly.activeAssembly()")
        Gui.doCommand("deps = assembly.getDependencies()")
        Gui.doCommand("print(deps)")
        commands = (
            f'assembly = UtilsAssembly.activeAssembly()\n'
            "deps = assembly.getDependencies()\n"
            "print(deps)\n"
        )
        
        Gui.doCommand(commands)

        self.panel = TaskAssemblyCreateDependencyMapGraphviz()
        Gui.Control.showDialog(self.panel)

if App.GuiUp:
    Gui.addCommand("Assembly_CreateDependencyMap", CommandCreateDependencyMap())

   
class TaskAssemblyCreateDependencyMapGraphviz(QtGui.QDialog):
    def __init__(self):  
        super().__init__()
        self.assembly = UtilsAssembly.activeAssembly()
        if not self.assembly:
            return

        self.form = QtGui.QWidget()  
        self.form.setWindowTitle("Assembly Dependencies")  
        

        self.colors = {
            "default": "lightgrey",
            "grounded": "lightblue",
            "joint": "#00FF00",
            "subassembly1": "#0000FF",
            "subassembly2": "#FFFF00",
            "subassembly3": "#FF00FF",
        }

        self.updateGraph()
        self.form.setWindowTitle("Assembly Dependencies")
        self.form.setGeometry(100, 100, 800, 600)

        #render the graph
        self.g.render(filename="assembly_dependency_map", format="dot")
        self.g.render(filename="assembly_dependency_map", format="png")
        self.g.view()  # Open the rendered graph in the default viewer

    def updateGraph(self):
        self.g = graphviz.Graph()
        self.g.attr()

        self.addNodesToGraph(self.g)
        self.addEdgesToGraph(self.g, self.assembly)

    def addNodesToGraph(self, g):
        assembly = UtilsAssembly.activeAssembly()
        with g.subgraph(name = 'cluster_0 ') as s:
            print("Getparts")
            for part in UtilsAssembly.getParts(assembly):
                
                g.node(part.Name, color=self.colors["default"], style="filled", fillcolor=self.colors["default"])
        subassembly = UtilsAssembly.getSubAssemblies(assembly)
        for sub in subassembly:
            self.addsSubGraphNodes(g, sub)
    def addsSubGraphNodes(self, g, assembly):
        with g.subgraph(name = f'cluster_{assembly}') as s:
            s.attr(label=assembly)
            s.attr(color=self.colors["subassembly1"])
            s.attr(style="filled")
            s.attr(fillcolor=self.colors["subassembly1"])
            s.attr("node", style="filled", fillcolor=self.colors["subassembly1"])
            
            for obj in UtilsAssembly.getParts(assembly):
                g.node(obj.Name, label=obj.Label, color=self.colors["default"], style="filled", fillcolor=self.colors["default"])

    def addEdgesToGraph(self, g, assembly):
        joints = assembly.Joints
        for joint in joints:
            g.node(f'"{joint.Label}"', label=joint.Label, color=self.colors["joint"], style="filled", fillcolor=self.colors["joint"], shape='ellipse')
            part1 = UtilsAssembly.getMovingPart(assembly, joint.Reference1)
            part2 = UtilsAssembly.getMovingPart(assembly, joint.Reference2)

            if part1 and part2:
                g.edge(f'"{part1.Name}"', f'"{joint.Label}"')
                g.edge(f'"{joint.Label}"', f'"{part2.Name}"')