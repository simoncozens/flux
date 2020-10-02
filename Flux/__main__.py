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
)
from Flux.UI.qfontfeatures import QFontFeaturesPanel
from Flux.UI.qshapingdebugger import QShapingDebugger
from Flux.UI.qruleeditor import QRuleEditor
from Flux.project import FluxProject
from Flux.ThirdParty.qtoaster import QToaster


app = QApplication(sys.argv)
app.setApplicationName("Flux")

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
