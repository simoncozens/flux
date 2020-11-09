from fontFeatures.feeLib import FeeParser
from PyQt5.QtWidgets import QLabel, QDialog, QCompleter, QDialogButtonBox, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QStringListModel
import sys

class FluxPlugin(QDialog):
    def __init__(self, project):
        super(QDialog, self).__init__()
        self.project = project
        self.feeparser = FeeParser(project.font)
        self.feeparser.fontfeatures = self.project.fontfeatures
        self.setWindowTitle(sys.modules[self.__module__].plugin_name)
        self.form = self.createForm()
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.form)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def glyphSelector(self, text):
        return self.feeparser.parser(text).glyphselector()
