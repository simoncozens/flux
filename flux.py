import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QHBoxLayout, QLineEdit, QSplitter
from fontFeatures.ttLib import unparse
from fontTools.ttLib import TTFont
from fontFeatures.optimizer import Optimizer
from qfontfeatures import QFontFeaturesPanel
from qbufferrenderer import QBufferRenderer
from qhbshapetrace import QHBShapeTrace
from fontFeatures.feeLib import FeeParser
from ttfontinfo import TTFontInfo
from fluxproject import FluxProject
from fontFeatures.jankyPOS.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
import sys


app = QApplication(sys.argv)

proj = FluxProject(sys.argv[1])

# text = "سبے"
# hbshapetrace = QHBShapeTrace(font, text)

buf = Buffer(proj.font.font, unicodes="سبے")
shaper = Shaper(proj.fontfeatures, proj.font)
shaper.execute(buf)

qbr = QBufferRenderer(proj, buf)

def textChanged(text):
    buf = font.vharfbuzz.shape(text)
    qhb.set_buf(buf)
    hbshapetrace.set_text(text)

# textChanged(text)

w = QWidget()
w.resize(510, 210)


v_box_1 = QVBoxLayout()
v_box_1.addWidget(QFontFeaturesPanel(proj))

v_box_2 = QVBoxLayout()
textbox = QLineEdit()
textbox.textChanged[str].connect(textChanged)

split = QSplitter()
split.setOrientation(Qt.Vertical)
split.addWidget(textbox)
split.addWidget(qbr)
# split.addWidget(hbshapetrace)
v_box_2.addWidget(split)

h_box = QHBoxLayout()
h_box.addLayout(v_box_1)
h_box.addLayout(v_box_2)

w.setLayout(h_box)


w.show()
sys.exit(app.exec_())
