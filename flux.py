import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QSplitter,
    QStackedWidget,
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

proj = FluxProject(sys.argv[1])


class FluxEditor(QWidget):
    def __init__(self, proj):
        super(QWidget, self).__init__()
        self.project = proj
        v_box_1 = QVBoxLayout()
        v_box_1.addWidget(QFontFeaturesPanel(proj, self))

        v_box_2 = QVBoxLayout()
        self.stack = QStackedWidget()
        self.shapingDebugger = QShapingDebugger(proj)
        self.ruleEditor = QRuleEditor(proj, None)
        self.stack.addWidget(self.shapingDebugger)
        self.stack.addWidget(self.ruleEditor)
        v_box_2.addWidget(self.stack)

        h_box = QHBoxLayout()
        h_box.addLayout(v_box_1)
        h_box.addLayout(v_box_2)

        self.setLayout(h_box)

    def showRuleEditor(self, rule):
        self.ruleEditor.setRule(rule)
        self.stack.setCurrentIndex(1)
        pass


FluxEditor(proj).show()
sys.exit(app.exec_())
