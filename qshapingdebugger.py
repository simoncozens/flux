from qbufferrenderer import QBufferRenderer
from PyQt5.QtWidgets import (
    QSplitter,
    QLineEdit,
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from fontFeatures.jankyPOS.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper

class QShapingDebugger(QSplitter):
    def __init__(self, project):
      self.text = "سبے"
      self.project = project
      super(QSplitter, self).__init__()
      self.qbr = QBufferRenderer(project, None)
      textbox = QLineEdit()
      textbox.textChanged[str].connect(self.textChanged)
      self.setOrientation(Qt.Vertical)
      self.addWidget(textbox)
      self.addWidget(self.qbr)
      self.shapeText()

    def shapeText(self):
      buf = Buffer(self.project.font.font, unicodes=self.text, direction="RTL")
      shaper = Shaper(self.project.fontfeatures, self.project.font)
      shaper.execute(buf)
      self.qbr.set_buf(buf)

    def textChanged(self, text):
      self.text = text
      self.shapeText()
