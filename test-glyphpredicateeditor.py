import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QHBoxLayout, QLineEdit, QSplitter, QTextEdit
from glyphpredicateeditor import GlyphClassPredicateEditor
from fontTools.ttLib import TTFont


font = TTFont("Qalam-Regular.ttf")

app = 0
if QApplication.instance():
    app = QApplication.instance()
else:
    app = QApplication(sys.argv)

w = QWidget()
w.resize(510, 210)
v_box_1 = QVBoxLayout()
gpe = GlyphClassPredicateEditor(font)
v_box_1.addLayout(gpe)
qte = QTextEdit()
v_box_1.addWidget(qte)

def update():
	qte.setText(" ".join(sorted(gpe.matches)))

gpe.changed.connect(update)

w.setLayout(v_box_1)


w.show()
sys.exit(app.exec_())
