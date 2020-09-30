import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QHBoxLayout, QLineEdit, QSplitter
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
from fontFeatures.optimizer import Optimizer
from qfontfeatures import QFontFeaturesPanel
from qbufferrenderer import QBufferRenderer
from qhbshapetrace import QHBShapeTrace
from qshapingdebugger import QShapingDebugger
from fontFeatures.feeLib import FeeParser
from ttfontinfo import TTFontInfo
from fluxproject import FluxProject
import sys


app = QApplication(sys.argv)

proj = FluxProject(sys.argv[1])
proj.fontfeatures.features["mark"] = [proj.fontfeatures.routines[2]]
proj.fontfeatures.features["curs"] = [proj.fontfeatures.routines[1]]

w = QWidget()
w.resize(510, 210)

v_box_1 = QVBoxLayout()
v_box_1.addWidget(QFontFeaturesPanel(proj))

v_box_2 = QVBoxLayout()
v_box_2.addWidget(QShapingDebugger(proj))

h_box = QHBoxLayout()
h_box.addLayout(v_box_1)
h_box.addLayout(v_box_2)

w.setLayout(h_box)


w.show()
sys.exit(app.exec_())
