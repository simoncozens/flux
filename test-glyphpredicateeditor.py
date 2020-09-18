import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QHBoxLayout, QLineEdit, QSplitter, QTextEdit, QDialogButtonBox
from glyphpredicateeditor import AutomatedGlyphClassDialog
from fontTools.ttLib import TTFont


font = TTFont("Qalam-Regular.ttf")

app = 0
if QApplication.instance():
    app = QApplication.instance()
else:
    app = QApplication(sys.argv)

w = AutomatedGlyphClassDialog(font)


w.show()
sys.exit(app.exec_())
