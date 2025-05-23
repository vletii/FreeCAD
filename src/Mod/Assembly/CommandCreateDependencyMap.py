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
        #return App.ActiveDocument is not None
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

        self.panel = AssemblyCreateDependencyMapGraphviz()
        Gui.Control.showDialog(self.panel)

if App.GuiUp:
    Gui.addCommand("Assembly_CreateDependencyMap", CommandCreateDependencyMap())

   
class AssemblyCreateDependencyMapGraphviz(QtWidgets.QDialog):
    def __init__(self):  
        super().__init__()
        self.assembly = UtilsAssembly.activeAssembly()
        if not self.assembly:
            return
        
        # layout = QtWidgets.QVBoxLayout(self)
        # self.setWindowTitle("Assembly Dependency Map")
        # buttonBox = QDialogButtonBox(
        #     QDialogButtonBox.hidejoints
        # )




        # self.hideJoints = QtWidgets.QCheckBox("Hide Joints")
        # self.hideJoints.setChecked(True)


        # #generate button
        # self.generateButton = QtWidgets.QPushButton("Generate")
        # self.generateButton.setToolTip("Generate the Dependency Map")
        # self.generateButton.clicked.connect(self.updateGraph)

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