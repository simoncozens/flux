from .qbufferrenderer import QBufferRenderer
from PyQt5.QtWidgets import (
    QSplitter,
    QLineEdit,
    QLabel
)
from PyQt5.QtCore import Qt
from fontFeatures.jankyPOS.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper

class QShapingDebugger(QSplitter):
    def __init__(self, project):
      self.text = "سبے"
      self.project = project
      super(QSplitter, self).__init__()
      self.qbr = QBufferRenderer(project, None)
      textbox = QLineEdit()
      textbox.setMaximumHeight(textbox.height())
      textbox.textChanged[str].connect(self.textChanged)
      self.shaperOutput = QLabel()
      self.setOrientation(Qt.Vertical)
      self.addWidget(textbox)
      self.addWidget(self.shaperOutput)
      self.addWidget(self.qbr)
      self.shapeText()

    def shapeText(self):
      buf = Buffer(self.project.font.font, unicodes=self.text)
      shaper = Shaper(self.project.fontfeatures, self.project.font)
      shaper.execute(buf)
      self.qbr.set_buf(buf)
      self.shaperOutput.setText(buf.serialize())

    def textChanged(self, text):
      self.text = text
      self.shapeText()
