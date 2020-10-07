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
    QSplitter
)
from PyQt5.QtCore import Qt
from Flux.UI.qfontfeatures import QFontFeaturesPanel
from Flux.UI.qshapingdebugger import QShapingDebugger
from Flux.UI.qruleeditor import QRuleEditor
from Flux.project import FluxProject
from Flux.ThirdParty.qtoaster import QToaster
import Flux.Plugins
import os.path, pkgutil

# from Foundation import NSBundle
# bundle = NSBundle.mainBundle()
# if bundle:
#     app_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
#     if app_info:
#         app_info['CFBundleName'] = "Flux"

app = QApplication(sys.argv)
app.setApplicationName("Flux")

proj = None
if len(sys.argv) > 1:
    proj = FluxProject(sys.argv[1])

# Load all available plugins
pluginpath = os.path.dirname(Flux.Plugins.__file__)
# Additional plugin path here?
plugin_loaders = pkgutil.iter_modules([pluginpath])
plugins = {}
for loader, module_name, is_pkg in plugin_loaders:
    if is_pkg:
        continue
    _module = loader.find_module(module_name).load_module(module_name)
    plugins[module_name] = _module


class FluxEditor(QSplitter):
    def __init__(self, proj):
        super(QSplitter, self).__init__()
        self.mainMenu = QMenuBar(self)
        self.project = proj
        if not proj:
            self.newProject()
        self.v_box_1 = QVBoxLayout()
        self.fontfeaturespanel = QFontFeaturesPanel(self.project, self)
        self.v_box_1.addWidget(self.fontfeaturespanel)

        self.setOrientation(Qt.Horizontal)

        self.v_box_2 = QVBoxLayout()
        self.stack = QStackedWidget()
        self.shapingDebugger = QShapingDebugger(self.project)
        self.ruleEditor = QRuleEditor(self.project, self, None)
        self.stack.addWidget(self.shapingDebugger)
        self.stack.addWidget(self.ruleEditor)
        self.v_box_2.addWidget(self.stack)

        self.left = QWidget()
        self.left.setLayout(self.v_box_1)
        self.right = QWidget()
        self.right.setLayout(self.v_box_2)
        self.addWidget(self.left)
        self.addWidget(self.right)
        self.setupFileMenu()
        self.setupPluginMenu()

    def setupFileMenu(self):
        openFile = QAction("&New Project", self)
        openFile.setShortcut("Ctrl+N")
        openFile.setStatusTip("New Project")
        openFile.triggered.connect(self.newProject)

        saveFile = QAction("&Save File", self)
        saveFile.setShortcut("Ctrl+S")
        saveFile.setStatusTip("Save File")
        # saveFile.triggered.connect(self.file_save)

        saveFile = QAction("&Save As...", self)
        saveFile.setStatusTip("Save As...")
        saveFile.triggered.connect(self.file_save_as)

        exportFea = QAction("Export FEA", self)
        exportFea.triggered.connect(self.exportFEA)

        exportOtf = QAction("Export OTF", self)
        exportOtf.triggered.connect(self.exportOTF)

        fileMenu = self.mainMenu.addMenu("&File")
        fileMenu.addAction(openFile)
        fileMenu.addAction(saveFile)
        fileMenu.addSeparator()
        fileMenu.addAction(exportFea)
        fileMenu.addAction(exportOtf)

    def setupPluginMenu(self):
        pluginMenu = self.mainMenu.addMenu("&Plugins")
        for plugin in plugins.values():
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
        if self.project:
            # Offer chance to save
            pass
        # Open the glyphs file
        glyphs = QFileDialog.getOpenFileName(
            self, "Open Glyphs file", filter="Glyphs (*.glyphs)"
        )
        if not glyphs:
            return
        self.project = FluxProject.new(glyphs[0])

    def file_save_as(self):
        filename = QFileDialog.getSaveFileName(
            self, "Save File", filter="Flux projects (*.fluxml)"
        )
        if filename:
            self.project.save(filename[0])
            QToaster.showMessage(self, "Saved successfully", desktop=False)

    def exportFEA(self):
        filename = QFileDialog.getSaveFileName(
            self, "Save File", filter="AFDKO feature file (*.fea)"
        )
        if not filename:
            return
        res = self.project.saveFEA(filename[0])
        if res is None:
            QToaster.showMessage(self, "Saved successfully", desktop=False)
        else:
            QToaster.showMessage(self, "Failed to save: " + res, desktop=False)

    def exportOTF(self):
        self.project.saveOTF()

    def update(self):
        self.fontfeaturespanel.update()
        self.shapingDebugger.shapeText()
        super().update()

    def showRuleEditor(self, rule):
        self.ruleEditor.setRule(rule)
        self.stack.setCurrentIndex(1)
        pass

    def showDebugger(self):
        self.stack.setCurrentIndex(0)
        pass


f = FluxEditor(proj)
f.show()
sys.exit(app.exec_())
