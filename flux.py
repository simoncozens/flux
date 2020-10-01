import sys
from PyQt5.QtCore import Qt
import PyQt5.QtGui as QtGui
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QSplitter,
    QStackedWidget,
    QMainWindow,
    QMenuBar,
    QAction,
    QFileDialog
)
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
from fontFeatures.optimizer import Optimizer
from qfontfeatures import QFontFeaturesPanel
from qbufferrenderer import QBufferRenderer
from qhbshapetrace import QHBShapeTrace
from qshapingdebugger import QShapingDebugger
from qruleeditor import QRuleEditor
from fontFeatures.feeLib import FeeParser
from ttfontinfo import TTFontInfo
from fluxproject import FluxProject
import sys


app = QApplication(sys.argv)

proj = None
if len(sys.argv) > 1:
    proj = FluxProject(sys.argv[1])

class FluxEditor(QWidget):
    def __init__(self, proj):
        super(QWidget, self).__init__()
        self.mainMenu = QMenuBar(self)
        self.project = proj
        if not proj:
            self.newProject()
        print("Setting up now")
        v_box_1 = QVBoxLayout()
        v_box_1.addWidget(QFontFeaturesPanel(self.project, self))

        v_box_2 = QVBoxLayout()
        self.stack = QStackedWidget()
        self.shapingDebugger = QShapingDebugger(self.project)
        self.ruleEditor = QRuleEditor(self.project, self, None)
        self.stack.addWidget(self.shapingDebugger)
        self.stack.addWidget(self.ruleEditor)
        v_box_2.addWidget(self.stack)

        h_box = QHBoxLayout()
        h_box.addLayout(v_box_1)
        h_box.addLayout(v_box_2)

        self.setLayout(h_box)
        self.setupMenu()

    def setupMenu(self):
        openFile = QAction("&New Project", self)
        openFile.setShortcut("Ctrl+N")
        openFile.setStatusTip('New Project')
        openFile.triggered.connect(self.newProject)

        saveFile = QAction("&Save File", self)
        saveFile.setShortcut("Ctrl+S")
        saveFile.setStatusTip('Save File')
        # saveFile.triggered.connect(self.file_save)

        saveFile = QAction("&Save As...", self)
        saveFile.setStatusTip('Save As...')
        saveFile.triggered.connect(self.file_save_as)

        fileMenu = self.mainMenu.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(saveFile)

    def newProject(self):
        if self.project:
            # Offer chance to save
            pass
        # Open the glyphs file
        glyphs = QFileDialog.getOpenFileName(self, "Open Glyphs file",
            filter="Glyphs (*.glyphs)")
        if not glyphs:
            return
        self.project = FluxProject.new(glyphs[0])

    def file_save_as(self):
        filename = QFileDialog.getSaveFileName(self, 'Save File',filter="Flux projects (*.fluxml)")
        print(filename)
        if filename:
            self.project.save(filename[0])

    def update(self):
        self.shapingDebugger.shapeText()

    def showRuleEditor(self, rule):
        self.ruleEditor.setRule(rule)
        self.stack.setCurrentIndex(1)
        pass

    def showDebugger(self):
        self.stack.setCurrentIndex(0)
        pass


FluxEditor(proj).show()
sys.exit(app.exec_())
