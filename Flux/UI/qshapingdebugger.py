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
    QHBoxLayout,
    QSlider,
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
import weakref


valid_glyph_name_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-*:^|~"


class VariationAwareBuffer(Buffer):
    def guess_segment_properties(self):
        for i in self.items:
            i.buffer = weakref.ref(self)
        super().guess_segment_properties()

    def store_unicode(self, unistring):
        self.items = [VariationAwareBufferItem.new_unicode(ord(char)) for char in unistring ]
        for i in self.items:
            i.buffer = weakref.ref(self)

class VariationAwareBufferItem(BufferItem):
    @classmethod
    def new_unicode(klass, codepoint):
        self = klass()
        self.codepoint = codepoint
        self.glyph = None
        self.feature_masks = {}
        return self

    @classmethod
    def new_glyph(klass, glyph, font):
        self = klass()
        self.codepoint = None
        self.glyph = glyph
        self.feature_masks = {}
        self.prep_glyph(font)
        return self

    def prep_glyph(self, font):
        super().prep_glyph(font)
        # # Interpolate width
        vf = self.buffer().vf
        if vf:
            glyphs = [vf.masters[master][self.glyph] for master in vf.master_order]
            widthset = {vf.master_order[i]: glyphs[i].width for i in range(len(vf.masters))}
            self.position.xAdvance = vf.interpolate_tuples(widthset, self.buffer().location)

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

        # Second box: Variations
        self.secondbox = QWidget()
        self.secondboxLayout = QHBoxLayout()
        self.secondbox.setLayout(self.secondboxLayout)
        self.sliders = []

        if self.project.variations:
            for axis in self.project.variations.designspace.axes:
                self.secondboxLayout.addWidget(QLabel(axis.name))
                slider = QSlider(0x01)
                slider.name = axis.name
                slider.setMinimum(axis.map_forward(axis.minimum))
                slider.setMaximum(axis.map_forward(axis.maximum))
                self.sliders.append(slider)

                slider.valueChanged.connect(self.shapeText)
                self.secondboxLayout.addWidget(slider)
        # Third box: Output and renderer
        self.thirdbox = QWidget()
        self.thirdboxLayout = QVBoxLayout()
        self.thirdbox.setLayout(self.thirdboxLayout)

        self.shaperOutput = QLabel()
        self.shaperOutput.setWordWrap(True)
        sp = self.shaperOutput.sizePolicy()
        sp.setVerticalPolicy(QSizePolicy.Maximum)
        self.shaperOutput.setSizePolicy(sp)

        self.qbr = QBufferRenderer(project, None)
        sp = self.thirdbox.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Maximum)
        sp.setVerticalPolicy(QSizePolicy.MinimumExpanding)
        self.thirdbox.setSizePolicy(sp)

        self.thirdboxLayout.addWidget(self.shaperOutput)
        self.thirdboxLayout.addWidget(self.qbr)

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
        if self.project.variations:
            self.addWidget(self.secondbox)
        self.addWidget(self.thirdbox)
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
        buf = VariationAwareBuffer(self.project.font)
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
                    item = VariationAwareBufferItem.new_glyph(glyphname, self.project.font)
                    item.codepoint = self.project.font.codepointForGlyph(glyphname)
                    buf.items.append(item)
                else:
                    buf.items.extend([VariationAwareBufferItem.new_unicode(ord(x)) for x in "/"+glyphname])
            else:
                item = VariationAwareBufferItem.new_unicode(ord(t[i]))
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
        self.prep_shaper(shaper, buf, features)
        shaper.execute(buf, features=features)

        self.qbr.set_buf(buf)
        self.fullBuffer = buf
        self.shaperOutput.setText(buf.serialize())

    def prep_shaper(self, shaper, buf, features):
        if not self.sliders:
            return
        buf.vf = self.project.variations
        loc = { slider.name: slider.value() for slider in self.sliders }
        buf.location = loc

        self.qbr.set_location(loc)


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
            if m and self.editor:
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
