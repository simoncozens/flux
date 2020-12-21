import sys
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QApplication,
    QHBoxLayout,
    QStackedWidget,
    QMenuBar,
    QAction,
    QFileDialog,
    QSplitter,
    QMessageBox
)
from PyQt5.QtCore import Qt, QSettings, QStandardPaths
from Flux.UI.qfontfeatures import QFontFeaturesPanel
from Flux.UI.qshapingdebugger import QShapingDebugger
from Flux.UI.qruleeditor import QRuleEditor
from Flux.UI.qattachmenteditor import QAttachmentEditor
from Flux.project import FluxProject
from Flux.ThirdParty.qtoaster import QToaster
import Flux.Plugins
import os.path, pkgutil, sys
from functools import partial


class FluxEditor(QSplitter):
    def __init__(self, proj):
        super(QSplitter, self).__init__()
        self.settings = QSettings()
        geometry = self.settings.value('mainwindowgeometry', '')
        if geometry:
            self.restoreGeometry(geometry)

        self.mainMenu = QMenuBar(self)
        self.project = proj
        self.loadPlugins()
        if not proj:
            self.openFluxOrFont() # Exits if there still isn't one
        self.setWindowTitle("Flux - %s" % (self.project.filename or self.project.fontfile))
        self.setupFileMenu()
        self.setupPluginMenu()
        self.left = QWidget()
        self.right = QWidget()
        self.rebuild_ui()

    def rebuild_ui(self):
        self.v_box_1 = QVBoxLayout()
        self.fontfeaturespanel = QFontFeaturesPanel(self.project, self)
        self.v_box_1.addWidget(self.fontfeaturespanel)

        self.setOrientation(Qt.Horizontal)

        self.v_box_2 = QVBoxLayout()
        self.stack = QStackedWidget()
        self.shapingDebugger = QShapingDebugger(self, self.project)
        self.ruleEditor = QRuleEditor(self.project, self, None)
        self.attachmentEditor = QAttachmentEditor(self.project, self, None)
        self.stack.addWidget(self.shapingDebugger)
        self.stack.addWidget(self.ruleEditor)
        self.stack.addWidget(self.attachmentEditor)
        self.v_box_2.addWidget(self.stack)

        if self.left.layout():
            QWidget().setLayout(self.left.layout())
            QWidget().setLayout(self.right.layout())
        self.left.setLayout(self.v_box_1)
        self.right.setLayout(self.v_box_2)
        self.addWidget(self.left)
        self.addWidget(self.right)

    def loadPlugins(self):
        pluginpath = os.path.dirname(Flux.Plugins.__file__)
        if hasattr(sys, "frozen"):
            pluginpath = "lib/python3.8/flux/Plugins"
        pluginpath2 = os.path.join(QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)[0], "Plugins")
        plugin_loaders = pkgutil.iter_modules([pluginpath, pluginpath2])
        self.plugins = {}
        for loader, module_name, is_pkg in plugin_loaders:
            if is_pkg:
                continue
            _module = loader.find_module(module_name).load_module(module_name)
            _module.module_name = module_name
            self.plugins[module_name] = _module


    def setupFileMenu(self):
        openFile = QAction("&New Project", self)
        openFile.setShortcut("Ctrl+N")
        openFile.setStatusTip("New Project")
        openFile.triggered.connect(self.newProject)

        self.saveFile = QAction("&Save", self)
        self.saveFile.setShortcut("Ctrl+S")
        self.saveFile.setStatusTip("Save")
        self.saveFile.triggered.connect(self.file_save)
        if not hasattr(self.project, "filename"):
            self.saveFile.setEnabled(False)

        saveAsFile = QAction("&Save As...", self)
        saveAsFile.setStatusTip("Save As...")
        saveAsFile.triggered.connect(self.file_save_as)

        importFea = QAction("Import FEA", self)
        importFea.triggered.connect(self.importFEA)

        exportFea = QAction("Export FEA", self)
        exportFea.triggered.connect(self.exportFEA)

        exportOtf = QAction("Export OTF", self)
        exportOtf.triggered.connect(self.exportOTF)

        fileMenu = self.mainMenu.addMenu("&File")
        fileMenu.addAction(openFile)
        fileMenu.addAction(self.saveFile)
        fileMenu.addAction(saveAsFile)
        fileMenu.addSeparator()
        fileMenu.addAction(importFea)
        fileMenu.addSeparator()
        fileMenu.addAction(exportFea)
        fileMenu.addAction(exportOtf)

    def setupPluginMenu(self):
        pluginMenu = self.mainMenu.addMenu("&Plugins")
        for plugin in self.plugins.values():
            p = QAction(plugin.plugin_name, self)
            p.triggered.connect(partial(self.runPlugin, plugin))
            pluginMenu.addAction(p)
        pluginMenu.addSeparator()
        dummy = QAction("Reload plugins", self)
        pluginMenu.addAction(dummy)

    def runPlugin(self,plugin):
        print(plugin.plugin_name)
        dialog = plugin.Dialog(self.project)
        result = dialog.exec_()
        if result:
            # Update everything
            self.update()

    def newProject(self):
        if self.project and self.isWindowModified():
            # Offer chance to save
            pass
        # Open the glyphs file
        glyphs = QFileDialog.getOpenFileName(
            self, "Open font file", filter="Font file (*.glyphs *.ufo *.otf *.ttf)"
        )
        if not glyphs:
            return
        self.project = FluxProject.new(glyphs[0])
        self.setWindowTitle("Flux - %s" % (self.project.filename or self.project.fontfile))
        self.rebuild_ui()

    def openFluxOrFont(self): # Exits if there still isn't one
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("Please open a font file or a .fluxml file to get started")
        msg.setWindowTitle("Flux")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

        filename = QFileDialog.getOpenFileName(
            self, "Open Flux file", filter="Flux or font file (*.glyphs *.ufo *.otf *.ttf *.fluxml)"
        )
        if not filename or not filename[0]:
            if not self.project:
                sys.exit(0)
            return
        if filename[0].endswith(".fluxml"):
            self.project = FluxProject(filename[0])
        else:
            self.project = FluxProject.new(filename[0])
        self.setWindowTitle("Flux - %s" % (self.project.filename or self.project.fontfile))

    def file_save_as(self):
        filename = QFileDialog.getSaveFileName(
            self, "Save File", filter="Flux projects (*.fluxml)"
        )
        if filename and filename[0]:
            self.project.filename = filename[0]
            self.project.save(filename[0])
            QToaster.showMessage(self, "Saved successfully", desktop=True)
            self.setWindowTitle("Flux - %s" % (self.project.filename or "New Project"))
            self.saveFile.setEnabled(True)
            self.setWindowModified(False)

    def file_save(self):
        if not self.project.filename:
            return self.file_save_as()
        self.project.save(self.project.filename)
        QToaster.showMessage(self, "Saved successfully", desktop=True)
        self.setWindowModified(False)

    def importFEA(self):
        filename = QFileDialog.getOpenFileName(
            self, "Open File", filter="AFDKO feature file (*.fea)"
        )
        if not filename:
            return
        res = self.project.loadFEA(filename[0])
        if res is None:
            QToaster.showMessage(self, "Imported successfully", desktop=True, parentWindow=False)
            self.update()
        else:
            QToaster.showMessage(self, "Failed to import: " + res, desktop=True)

    def exportFEA(self):
        filename = QFileDialog.getSaveFileName(
            self, "Save File", filter="AFDKO feature file (*.fea)"
        )
        if not filename:
            return
        res = self.project.saveFEA(filename[0])
        if res is None:
            QToaster.showMessage(self, "Saved successfully", desktop=True)
        else:
            QToaster.showMessage(self, "Failed to save: " + res, desktop=True)

    def exportOTF(self):
        self.project.saveOTF()

    def update(self):
        self.fontfeaturespanel.update()
        self.shapingDebugger.update()
        super().update()

    def reshape(self):
        self.shapingDebugger.update()

    def showRuleEditor(self, rule, index=None):
        self.ruleEditor.setRule(rule, index)
        self.stack.setCurrentIndex(1)
        pass

    def showAttachmentEditor(self, rule, index=None):
        self.attachmentEditor.setRule(rule, index)
        self.stack.setCurrentIndex(2)
        pass

    def showDebugger(self):
        self.stack.setCurrentIndex(0)
        pass

    def closeEvent(self, event):
        geometry = self.saveGeometry()
        self.settings.setValue('mainwindowgeometry', geometry)
        if not self.isWindowModified():
            event.accept()
            return
        quit_msg = "You have unsaved changes. Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'Message',
                         quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

