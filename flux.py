import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QHBoxLayout, QLineEdit, QSplitter
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
from fontFeatures.optimizer import Optimizer
from qfontfeatures import QFontFeaturesPanel
from vharfbuzz import Vharfbuzz
from qvharfbuzz import QVHarfbuzzWidget
from qhbshapetrace import QHBShapeTrace
from fontFeatures.feeLib import FeeParser


app = 0
if QApplication.instance():
    app = QApplication.instance()
else:
    app = QApplication(sys.argv)

font = "/Users/simon/hacks/fonts/qalam/master_ttf/Qalam-Regular.ttf"
p = FeeParser(font)
p.parseFile("/Users/simon/hacks/fonts/qalam/qalam.fee")
fea = p.fontfeatures
vf = Vharfbuzz(font)
text = "چبَے"
qhb = QVHarfbuzzWidget(vf, 56, None)
hbshapetrace = QHBShapeTrace(vf, text)

def textChanged(text):
    buf = vf.shape(text)
    qhb.set_buf(buf)
    hbshapetrace.set_text(text)

textChanged(text)

w = QWidget()
w.resize(510, 210)


v_box_1 = QVBoxLayout()
v_box_1.addWidget(QFontFeaturesPanel(fea))

v_box_2 = QVBoxLayout()

textbox = QLineEdit()
textbox.textChanged[str].connect(textChanged)

split = QSplitter()
split.setOrientation(Qt.Vertical)
split.addWidget(textbox)
split.addWidget(qhb)
split.addWidget(hbshapetrace)
v_box_2.addWidget(split)

h_box = QHBoxLayout()
h_box.addLayout(v_box_1)
h_box.addLayout(v_box_2)

w.setLayout(h_box)


w.show()
sys.exit(app.exec_())
