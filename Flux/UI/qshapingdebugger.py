from .qbufferrenderer import QBufferRenderer
from PyQt5.QtWidgets import (
    QSplitter,
    QLineEdit,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QSizePolicy,
    QHeaderView,
    QFormLayout,
    QVBoxLayout,
    QGroupBox,
    QCheckBox,
    QWidget,
)
from PyQt5.QtCore import Qt
from Flux.ThirdParty.QFlowLayout import QFlowLayout
from fontFeatures.shaperLib.Buffer import Buffer, BufferItem
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.shaperLib.BaseShaper import BaseShaper
from copy import copy, deepcopy
import re

valid_glyph_name_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-*:^|~"

class QShapingDebugger(QSplitter):
    def __init__(self, editor, project):
        self.editor = editor
        self.project = project
        super(QSplitter, self).__init__()
        self.text = self.project.debuggingText or self.getReasonableTextForFont(self.project.font)

        # First box: Text and features
        self.firstbox = QWidget()
        self.firstboxLayout = QVBoxLayout()
        self.firstbox.setLayout(self.firstboxLayout)

        textbox = QLineEdit()
        textbox.setText(self.text)
        textbox.setMaximumHeight(textbox.height())
        textbox.textChanged[str].connect(self.textChanged)

        self.featuregroup = QGroupBox("Features")
        self.featuregrouplayout = QFlowLayout()
        self.featuregroup.setLayout(self.featuregrouplayout)
        self.features = {}
        self.fillFeatureGroup()
        self.firstboxLayout.addWidget(textbox)
        self.firstboxLayout.addWidget(self.featuregroup)

        # Second box: Output and renderer
        self.secondbox = QWidget()
        self.secondboxLayout = QVBoxLayout()
        self.secondbox.setLayout(self.secondboxLayout)

        self.shaperOutput = QLabel()
        self.shaperOutput.setWordWrap(True)
        sp = self.shaperOutput.sizePolicy()
        sp.setVerticalPolicy(QSizePolicy.Maximum)
        self.shaperOutput.setSizePolicy(sp)

        self.qbr = QBufferRenderer(project, None)
        sp = self.secondbox.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Maximum)
        sp.setVerticalPolicy(QSizePolicy.MinimumExpanding)
        self.secondbox.setSizePolicy(sp)

        self.secondboxLayout.addWidget(self.shaperOutput)
        self.secondboxLayout.addWidget(self.qbr)

        # Third box: message table
        self.messageTable = QTableWidget()
        self.messageTable.setColumnCount(2)
        self.messageTable.verticalHeader().setVisible(False)
        self.messageTable.setHorizontalHeaderLabels(["message", "buffer"])
        header = self.messageTable.horizontalHeader()
        headerWidth = self.messageTable.viewport().size().width()
        header.resizeSection(0, headerWidth * 2 / 3)
        header.setStretchLastSection(True)
        self.messageTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.messageTable.selectionModel().selectionChanged.connect(
            self.renderPartialTrace
        )

        self.setOrientation(Qt.Vertical)
        self.addWidget(self.firstbox)
        self.addWidget(self.secondbox)
        self.addWidget(self.messageTable)
        self.fullBuffer = None
        self.lastBuffer = None
        self.shapeText()

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def fillFeatureGroup(self):
        prev = self.features
        fkeys = self.project.fontfeatures.features.keys()
        self.clearLayout(self.featuregrouplayout)
        self.features = {}
        for k in fkeys:
            box = self.features[k] = QCheckBox(k)
            box.setTristate()
            if k in prev:
                box.setCheckState(prev[k].checkState())
            else:
                box.setCheckState(Qt.PartiallyChecked)
            box.stateChanged.connect(self.shapeText)
            self.featuregrouplayout.addWidget(box)

    def update(self):
        self.fillFeatureGroup()
        self.shapeText()

    def buildBuffer(self):
        buf = Buffer(self.project.font)
        t = self.text
        i = 0
        while i < len(t):
            if t[i] == "/": # Start of glyph name
                i = i + 1
                glyphname = ""
                while i < len(t) and t[i] in valid_glyph_name_chars:
                    glyphname += t[i]
                    i = i + 1
                if len(glyphname) and glyphname in self.project.font:
                    print("Adding glyph item %s" % glyphname)
                    item = BufferItem.new_glyph(glyphname, self.project.font)
                    item.codepoint = self.project.font.codepointForGlyph(glyphname)
                    buf.items.append(item)
                else:
                    buf.items.extend([BufferItem.new_unicode(ord(x)) for x in "/"+glyphname])
            else:
                item = BufferItem.new_unicode(ord(t[i]))
                print("Adding buffer item %s" % item)
                i = i + 1
                buf.items.append(item)
        buf.guess_segment_properties()
        return buf

    def shapeText(self):
        features = []
        for k, box in self.features.items():
            if box.checkState() == Qt.PartiallyChecked:
                continue
            features.append({"tag": k, "value": box.isChecked()})

        buf = self.buildBuffer()
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
        shaper = Shaper(
            self.project.fontfeatures,
            self.project.font,
            message_function=self.addToTable,
        )
        # try:
        shaper.execute(buf, features=features)
        # except Exception as e:
            # print("Shaping exception: ", e)
        self.qbr.set_buf(buf)
        self.fullBuffer = buf
        self.shaperOutput.setText(buf.serialize())

    def addToTable(self, msg, buffer=None, serialize_options=None):
        if msg.startswith("Before"):
            return
        if not buffer:  # Easy one
            rowPosition = self.messageTable.rowCount()
            self.messageTable.insertRow(rowPosition)
            message_item = QTableWidgetItem(msg)
            self.messageTable.setItem(rowPosition, 0, message_item)
            return

        # Urgh
        b = BaseShaper(None, None, buffer)
        for i in range(0,len(buffer.items)):
            b.propagate_attachment_offsets(i)

        ser = buffer.serialize(additional=serialize_options)

        if self.lastBuffer == ser:
            m = re.match(r"After (\w+ \(\w+\))", msg)
            if m:
                self.skipped.append(m[1])
                return
        elif self.skipped:
            rowPosition = self.messageTable.rowCount()
            self.messageTable.insertRow(rowPosition)
            message_item = QTableWidgetItem(
                "Routines executed but had no effect: %s" % ",".join(self.skipped)
            )
            self.messageTable.setItem(rowPosition, 0, message_item)
            self.skipped = []
        self.lastBuffer = ser
        rowPosition = self.messageTable.rowCount()
        self.messageTable.insertRow(rowPosition)
        message_item = QTableWidgetItem(msg)
        self.messageTable.setItem(rowPosition, 0, message_item)
        self.partialBuffers[rowPosition] = (copy(buffer), msg)
        self.partialBuffers[rowPosition][0].items = deepcopy(buffer.items)
        buffer_item = QTableWidgetItem(ser)
        self.messageTable.setItem(rowPosition, 1, buffer_item)

    def renderPartialTrace(self):
        indexes = self.messageTable.selectedIndexes()
        if len(indexes) != 2:
            return
        row = indexes[0].row()
        if row in self.partialBuffers:
            buf, msg = self.partialBuffers[row]
            self.qbr.set_buf(buf)
            m = re.match(r"After (\w+) \((\w+)\)", msg)
            if m:
                routine, feature = m[1], m[2]
                self.editor.fontfeaturespanel.lookuplist.highlight(routine)
                self.editor.fontfeaturespanel.featurelist.highlight(feature, routine)

        # else:
        #     self.qbr.set_buf(self.fullBuffer)

    def textChanged(self, text):
        self.text = text
        self.project.debuggingText = text
        self.shapeText()

    def getReasonableTextForFont(self, font):
        text = ""
        if font.glyphForCodepoint(0x627, fallback=False):  # Arabic
            text = text + "ابج "
        if font.glyphForCodepoint(0x915, fallback=False):  # Devanagari
            text = text + "कचण "
        if font.glyphForCodepoint(0x61, fallback=False):  # Latin
            text = text + "abc "
        return text.strip()
