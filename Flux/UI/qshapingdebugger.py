from .qbufferrenderer import QBufferRenderer
from PyQt5.QtWidgets import (
    QSplitter,
    QLineEdit,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView
)
from PyQt5.QtCore import Qt
from fontFeatures.jankyPOS.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from copy import copy, deepcopy


class QShapingDebugger(QSplitter):
    def __init__(self, project):
      self.text = ""
      self.project = project
      super(QSplitter, self).__init__()
      self.qbr = QBufferRenderer(project, None)
      textbox = QLineEdit()
      textbox.setMaximumHeight(textbox.height())
      textbox.textChanged[str].connect(self.textChanged)
      self.messageTable = QTableWidget()
      self.messageTable.setColumnCount(2)
      self.messageTable.verticalHeader().setVisible(False)
      self.messageTable.setHorizontalHeaderLabels(["message", "buffer"])
      self.messageTable.horizontalHeader().setStretchLastSection(True)
      self.messageTable.setSelectionBehavior(QAbstractItemView.SelectRows)
      self.messageTable.selectionModel().selectionChanged.connect(self.renderPartialTrace)
      self.shaperOutput = QLabel()
      self.setOrientation(Qt.Vertical)
      self.addWidget(textbox)
      self.addWidget(self.shaperOutput)
      self.addWidget(self.qbr)
      self.addWidget(self.messageTable)
      self.fullBuffer = None
      self.shapeText()

    def shapeText(self):
      buf = Buffer(self.project.font.font, unicodes=self.text)
      self.messageTable.setRowCount(0)
      if not self.text:
        return
      self.partialBuffers = {}
      shaper = Shaper(self.project.fontfeatures, self.project.font,
        message_function=self.addToTable
        )
      shaper.execute(buf)
      self.qbr.set_buf(buf)
      self.fullBuffer = buf
      self.shaperOutput.setText(buf.serialize())

    def addToTable(self, msg, buffer=None, serialize_options=None):
        rowPosition = self.messageTable.rowCount()
        self.messageTable.insertRow(rowPosition)
        message_item = QTableWidgetItem(msg)
        if buffer:
            self.partialBuffers[rowPosition] = copy(buffer)
            self.partialBuffers[rowPosition].items = deepcopy(buffer.items)
            ser = buffer.serialize(additional=serialize_options)
            buffer_item = QTableWidgetItem(ser)
            self.messageTable.setItem(rowPosition,1,buffer_item)
        self.messageTable.setItem(rowPosition,0,message_item)

    def renderPartialTrace(self):
        indexes = self.messageTable.selectedIndexes()
        row = indexes[0].row()
        if row in self.partialBuffers:
            self.qbr.set_buf(self.partialBuffers[row])
        else:
            self.qbr.set_buf(self.fullBuffer)

    def textChanged(self, text):
      self.text = text
      self.shapeText()
