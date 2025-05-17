import os
import FreeCAD as App

from PySide.QtCore import QT_TRANSLATE_NOOP

if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui, QtWidgets

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
        deps = assembly.getDependencies()
        Gui.doCommand(commands)

        self.panel = TaskAssemblyCreateDependencyMap(deps)
        Gui.Control.showDialog(self.panel)

if App.GuiUp:
    Gui.addCommand("Assembly_CreateDependencyMap", CommandCreateDependencyMap())


class TaskAssemblyCreateDependencyMap(QtWidgets.QDialog):
    def __init__(self, deps=None, parent=None):
        super(TaskAssemblyCreateDependencyMap, self).__init__(parent)

        self.setWindowTitle("Current Dependency Map")
        self.setGeometry(100, 100, 400, 300)
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel("This is a Dependency Map")
        layout.addWidget(label)
        self.text_area = QtWidgets.QTextEdit()
        self.text_area.setReadOnly(True)

        if deps:
            # If deps is a Python list of strings or objects with __str__ output
            self.text_area.setText("\n".join(str(dep) for dep in deps))
        else:
            self.text_area.setText("No dependencies found.")
        layout.addWidget(self.text_area)