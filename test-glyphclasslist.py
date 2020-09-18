import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QHBoxLayout, QLineEdit, QSplitter
from classlist import GlyphClassList
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
v_box_1.addWidget(GlyphClassList(font))

w.setLayout(v_box_1)


w.show()
sys.exit(app.exec_())
