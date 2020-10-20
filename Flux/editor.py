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
from PyQt5.QtCore import Qt
from Flux.UI.qfontfeatures import QFontFeaturesPanel
from Flux.UI.qshapingdebugger import QShapingDebugger
from Flux.UI.qruleeditor import QRuleEditor
from Flux.UI.qattachmenteditor import QAttachmentEditor
from Flux.project import FluxProject
from Flux.ThirdParty.qtoaster import QToaster
import Flux.Plugins
import os.path, pkgutil, sys

class FluxEditor(QSplitter):
    def __init__(self, proj):
        super(QSplitter, self).__init__()
        self.mainMenu = QMenuBar(self)
        self.project = proj
        self.loadPlugins()
        if not proj:
            self.openFluxOrGlyphs()
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

        self.left = QWidget()
        self.left.setLayout(self.v_box_1)
        self.right = QWidget()
        self.right.setLayout(self.v_box_2)
        self.addWidget(self.left)
        self.addWidget(self.right)
        self.setupFileMenu()
        self.setupPluginMenu()

    def loadPlugins(self):
        # Load all available plugins
        pluginpath = os.path.dirname(Flux.Plugins.__file__)
        # Additional plugin path here?
        plugin_loaders = pkgutil.iter_modules([pluginpath])
        self.plugins = {}
        for loader, module_name, is_pkg in plugin_loaders:
            if is_pkg:
                continue
            _module = loader.find_module(module_name).load_module(module_name)
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
            p.triggered.connect(lambda: self.runPlugin(plugin))
            pluginMenu.addAction(p)
        pluginMenu.addSeparator()
        dummy = QAction("Reload plugins", self)
        pluginMenu.addAction(dummy)

    def runPlugin(self, plugin):
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
            self, "Open Glyphs file", filter="Glyphs (*.glyphs)"
        )
        if not glyphs:
            return
        self.project = FluxProject.new(glyphs[0])

    def openFluxOrGlyphs(self):
        filename = QFileDialog.getOpenFileName(
            self, "Open Flux/Glyphs file", filter="Flux or Glyphs (*.glyphs *.fluxml)"
        )
        if not filename:
            if not self.project:
                sys.exit(0)
            return
        if filename[0].endswith(".glyphs"):
            self.project = FluxProject.new(filename[0])
        else:
            self.project = FluxProject(filename[0])

    def file_save_as(self):
        filename = QFileDialog.getSaveFileName(
            self, "Save File", filter="Flux projects (*.fluxml)"
        )
        if filename:
            self.project.save(filename[0])
            QToaster.showMessage(self, "Saved successfully", desktop=True)
            self.project.filename = filename
            self.saveFile.setEnabled(True)
            self.setWindowModified(False)

    def file_save(self):
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
        self.shapingDebugger.shapeText()
        super().update()

    def reshape(self):
        self.shapingDebugger.shapeText()

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
