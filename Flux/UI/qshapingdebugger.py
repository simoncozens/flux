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
from fontFeatures.shaperLib.Buffer import Buffer
from fontFeatures.shaperLib.Shaper import Shaper
from copy import copy, deepcopy
import re


class QShapingDebugger(QSplitter):
    def __init__(self, editor, project):
      self.editor = editor
      self.project = project
      super(QSplitter, self).__init__()
      self.text = self.getReasonableTextForFont(self.project.font)
      self.qbr = QBufferRenderer(project, None)
      textbox = QLineEdit()
      textbox.setText(self.text)
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
      self.lastBuffer = None
      self.shapeText()

    def shapeText(self):
      buf = Buffer(self.project.font, unicodes=self.text)
      self.messageTable.setRowCount(0)
      if not self.text:
        buf.clear_mask()
        self.qbr.set_buf(buf)
        self.fullBuffer = buf
        self.shaperOutput.setText(buf.serialize())
        return
      self.messageTable.clearSelection()
      self.lastBuffer = None
      self.skipped = []
      self.partialBuffers = {}
      shaper = Shaper(self.project.fontfeatures, self.project.font,
        message_function=self.addToTable
        )
      try:
          shaper.execute(buf)
      except Exception as e:
          print("Shaping exception: ", e)
      self.qbr.set_buf(buf)
      self.fullBuffer = buf
      self.shaperOutput.setText(buf.serialize())

    def addToTable(self, msg, buffer=None, serialize_options=None):
        if msg.startswith("Before"):
            return
        if not buffer: # Easy one
            rowPosition = self.messageTable.rowCount()
            self.messageTable.insertRow(rowPosition)
            message_item = QTableWidgetItem(msg)
            self.messageTable.setItem(rowPosition,0,message_item)
            return

        ser = buffer.serialize(additional=serialize_options)

        if self.lastBuffer == ser:
            m = re.match(r'After (\w+ \(\w+\))', msg)
            if m:
                self.skipped.append(m[1])
                return
        elif self.skipped:
            rowPosition = self.messageTable.rowCount()
            self.messageTable.insertRow(rowPosition)
            message_item = QTableWidgetItem("Routines executed but had no effect: %s" % ",".join(self.skipped))
            self.messageTable.setItem(rowPosition,0,message_item)
            self.skipped = []
        self.lastBuffer = ser
        rowPosition = self.messageTable.rowCount()
        self.messageTable.insertRow(rowPosition)
        message_item = QTableWidgetItem(msg)
        self.messageTable.setItem(rowPosition,0,message_item)
        self.partialBuffers[rowPosition] = (copy(buffer), msg)
        self.partialBuffers[rowPosition][0].items = deepcopy(buffer.items)
        buffer_item = QTableWidgetItem(ser)
        self.messageTable.setItem(rowPosition,1,buffer_item)

    def renderPartialTrace(self):
        indexes = self.messageTable.selectedIndexes()
        if len(indexes) != 2:
            return
        row = indexes[0].row()
        if row in self.partialBuffers:
            buf, msg = self.partialBuffers[row]
            self.qbr.set_buf(buf)
            m = re.match(r'After (\w+) \((\w+)\)', msg)
            if m:
                routine, feature = m[1], m[2]
                self.editor.fontfeaturespanel.lookuplist.highlight(routine)
                self.editor.fontfeaturespanel.featurelist.highlight(feature, routine)


        # else:
        #     self.qbr.set_buf(self.fullBuffer)

    def textChanged(self, text):
      self.text = text
      self.shapeText()

    def getReasonableTextForFont(self, font):
        text = ""
        if font.glyphForCodepoint(0x627): # Arabic
            text  = text + "ابج "
        elif font.glyphForCodepoint(0x915): # Devanagari
            text = text + "कचण "
        elif font.glyphForCodepoint(0x61): # Latin
            text = text + "abc "
        return text.strip()
