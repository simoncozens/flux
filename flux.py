import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QHBoxLayout, QLineEdit
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
from fontFeatures.optimizer import Optimizer
from qfontfeatures import QFontFeaturesPanel
from vharfbuzz import Vharfbuzz
from qvharfbuzz import QVHarfbuzzWidget


app = 0
if QApplication.instance():
    app = QApplication.instance()
else:
    app = QApplication(sys.argv)

font = "/Users/simon/Library/Fonts/NotoNastaliqUrdu-Regular.ttf"
fea = unparse(TTFont(font))
vf = Vharfbuzz(font)
buf = vf.shape("چبَے")
qhb = QVHarfbuzzWidget(vf, 56, buf)

def textChanged(text):
    buf = vf.shape(text)
    qhb.set_buf(buf)

w = QWidget()
w.resize(510, 210)


v_box_1 = QVBoxLayout()
v_box_1.addWidget(QFontFeaturesPanel(fea))

v_box_2 = QVBoxLayout()

textbox = QLineEdit()
textbox.textChanged[str].connect(textChanged)

v_box_2.addWidget(textbox)
v_box_2.addWidget(qhb)

h_box = QHBoxLayout()
h_box.addLayout(v_box_1)
h_box.addLayout(v_box_2)

w.setLayout(h_box)


w.show()
sys.exit(app.exec_())
