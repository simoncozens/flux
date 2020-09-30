from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QScrollArea,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QLabel,
    QLineEdit,
    QSpinBox,
    QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.jankyPOS.Buffer import Buffer
from qbufferrenderer import QBufferRenderer
from fontFeatures import Positioning, ValueRecord, Substitution, Chaining
import sys


class QValueRecordEditor(QWidget):
    changed = pyqtSignal()
    fieldnames = ["xPlacement", "yPlacement", "xAdvance", "yAdvance"]
    labelnames = ["Δx", "Δy", "+x", "+y"]

    def __init__(self, vr):
        self.valuerecord = vr
        self.boxlayout = QHBoxLayout()
        self.boxes = []
        super(QWidget, self).__init__()
        for ix, k in enumerate(self.fieldnames):
            t = QSpinBox()
            t.setSingleStep(10)
            t.setRange(-10000, 10000)
            t.setValue(getattr(self.valuerecord, k) or 0)
            t.valueChanged.connect(self.serialize)
            # label = QLabel(t)
            # label.setText(self.labelnames[ix])
            # label.move(label.x()+0,label.y()-50)
            self.boxes.append(t)
            self.boxlayout.addWidget(t)
        self.setLayout(self.boxlayout)

    def serialize(self):
        for ix, k in enumerate(self.fieldnames):
            try:
                val = int(self.boxes[ix].text())
                setattr(self.valuerecord, k, int(self.boxes[ix].value()))
            except Exception as e:
                print(e)
        self.changed.emit()


class QRuleEditor(QSplitter):
    def __init__(self, project, rule):  # Rule is some fontFeatures object
        self.project = project
        self.inputslots = []
        self.precontextslots = []
        self.postcontextslots = []
        self.outputslots = []

        super(QRuleEditor, self).__init__()

        self.slotview = QHBoxLayout()
        scroll = QScrollArea()
        scroll.setLayout(self.slotview)

        self.outputview_before = QBufferRenderer(project)
        self.outputview_after = QBufferRenderer(project)
        self.before_after = QWidget()
        self.before_after_layout_v = QVBoxLayout()

        self.asFea = QLabel()

        layoutarea = QWidget()
        self.before_after_layout_h = QHBoxLayout()
        self.before_after_layout_h.addWidget(self.outputview_before)
        self.before_after_layout_h.addWidget(self.outputview_after)
        layoutarea.setLayout(self.before_after_layout_h)

        self.before_after_layout_v.addWidget(self.asFea)
        self.before_after_layout_v.addWidget(layoutarea)

        self.before_after.setLayout(self.before_after_layout_v)

        self.setOrientation(Qt.Vertical)
        self.addWidget(scroll)

        self.addWidget(self.before_after)
        self.setRule(rule)

    def setRule(self, rule):
        self.rule = rule
        self.arrangeSlots()
        self.representative_string = self.makeRepresentativeString()
        self.resetBuffer()

    def resetBuffer(self):
        if self.rule:
            self.asFea.setText(self.rule.asFea())
        self.outputview_before.set_buf(self.makeBuffer("before"))
        self.outputview_after.set_buf(self.makeBuffer("after"))

    @pyqtSlot()
    def changeRepresentativeString(self):
        l = self.sender()
        self.representative_string[l.slotnumber] = l.text()
        self.resetBuffer()

    @pyqtSlot()
    def replacementChanged(self):
        l = self.sender()
        self.rule.replacement[l.position] = l.text()
        self.resetBuffer()

    @pyqtSlot()
    def addGlyphToSlot(self):
        l = self.sender()
        glyphname = l.text()
        l.contents[l.slotindex].append(glyphname)
        self.arrangeSlots()
        self.representative_string = self.makeRepresentativeString()
        self.resetBuffer()

    @pyqtSlot()
    def addRemoveSlot(self):
        sender = self.sender()
        action = sender.text()
        if action == "<+":
            sender.contents.insert(0, [])
            # If these are input glyphs, add another replacement etc.
            if sender.contents == self.rule.shaper_inputs():
                if isinstance(self.rule, Positioning):
                    self.rule.valuerecords.insert(0, ValueRecord())
                elif isinstance(self.rule, Substitution):
                    self.rule.replacement.insert(0, [])
                elif isinstance(self.rule, Chaining):
                    self.rule.lookups.insert(0, [])
        elif action == "+>":
            sender.contents.append([])
            # If these are input glyphs, add another replacement etc.
            if sender.contents == self.rule.shaper_inputs():
                if isinstance(self.rule, Positioning):
                    self.rule.valuerecords.append(ValueRecord())
                elif isinstance(self.rule, Substitution):
                    self.rule.replacement.append([])
                elif isinstance(self.rule, Chaining):
                    self.rule.lookups.append([])

        elif action == "-":
            del sender.contents[self.sender().ix]
        self.arrangeSlots()
        self.representative_string = self.makeRepresentativeString()
        self.resetBuffer()

    def makeASlot(self, slotnumber, contents, style=None, editingWidgets=None):
        for ix, glyphslot in enumerate(contents):
            slot = QWidget()
            slotLayout = QVBoxLayout()
            for glyph in glyphslot:
                l = QPushButton(glyph)
                l.setDefault(False)
                l.setAutoDefault(False)
                l.slotnumber = slotnumber
                # l.setFlat(True)
                l.clicked.connect(self.changeRepresentativeString)
                # l.setAlignment(Qt.AlignCenter)
                if style:
                    l.setStyleSheet(style)
                slotLayout.addWidget(l)

            line = QLineEdit()
            line.slotindex = ix
            line.contents = contents
            line.returnPressed.connect(self.addGlyphToSlot)
            slotLayout.addWidget(line)
            slotLayout.addStretch()
            if editingWidgets:
                slotLayout.addWidget(editingWidgets[ix])

            pushbuttonsArea = QWidget()
            pushbuttonsLayout = QHBoxLayout()
            pushbuttonsArea.setLayout(pushbuttonsLayout)
            if ix == 0:
                addASlotLeft = QPushButton("<+")
                addASlotLeft.contents = contents
                addASlotLeft.clicked.connect(self.addRemoveSlot)
                pushbuttonsLayout.addWidget(addASlotLeft)
            pushbuttonsLayout.addStretch()
            if not (editingWidgets and len(contents) == 1):
                removeASlot = QPushButton("-")
                removeASlot.contents = contents
                removeASlot.ix = ix
                removeASlot.clicked.connect(self.addRemoveSlot)
                pushbuttonsLayout.addWidget(removeASlot)
            pushbuttonsLayout.addStretch()
            if ix == len(contents) - 1:
                addASlotRight = QPushButton("+>")
                addASlotRight.contents = contents
                addASlotRight.clicked.connect(self.addRemoveSlot)
                pushbuttonsLayout.addWidget(addASlotRight)
            slotLayout.addWidget(pushbuttonsArea)

            slotnumber = slotnumber + 1

            slot.setLayout(slotLayout)
            self.slotview.addWidget(slot)
        return slotnumber

    def makeEditingWidgets(self):
        editingWidgets = []
        for ix, i in enumerate(self.rule.shaper_inputs()):
            if isinstance(self.rule, Positioning):
                widget = QValueRecordEditor(self.rule.valuerecords[ix])
                widget.changed.connect(self.resetBuffer)
                editingWidgets.append(widget)
            if isinstance(self.rule, Substitution):
                replacements = [x[0] for x in self.rule.replacement if x]
                widget = QLineEdit(" ".join(replacements) or "")
                widget.position = ix
                widget.returnPressed.connect(self.replacementChanged)
                editingWidgets.append(widget)

        return editingWidgets

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def arrangeSlots(self):
        self.clearLayout(self.slotview)
        if not self.rule:
            return
        self.slotview.addStretch()
        slotnumber = 0
        if hasattr(self.rule, "precontext"):
            slotnumber = self.makeASlot(
                slotnumber, self.rule.precontext, "background-color:#ffaaaa;"
            )

        editingWidgets = self.makeEditingWidgets()
        slotnumber = self.makeASlot(
            slotnumber, self.rule.shaper_inputs(), editingWidgets=editingWidgets
        )

        if hasattr(self.rule, "postcontext"):
            self.makeASlot(
                slotnumber, self.rule.postcontext, "background-color:#aaaaff;"
            )

        self.slotview.addStretch()

    def makeRepresentativeString(self):
        inputglyphs = []
        if not self.rule:
            return inputglyphs
        # "x and x[0]" thing because slots may be empty if newly added
        if hasattr(self.rule, "precontext"):
            inputglyphs.extend([x and x[0] for x in self.rule.precontext])

        inputglyphs.extend([x and x[0] for x in self.rule.shaper_inputs()])

        if hasattr(self.rule, "postcontext"):
            inputglyphs.extend([x and x[0] for x in self.rule.postcontext])

        return [x for x in inputglyphs if x]

    def makeBuffer(self, before_after="before"):
        buf = Buffer(
            self.project.font, glyphs=self.representative_string, direction="RTL"
        )
        shaper = Shaper(self.project.fontfeatures, self.project.font)
        shaper.execute(buf)
        if before_after == "after" and self.rule:
            self.rule.apply_to_buffer(buf)
        return buf


if __name__ == "__main__":
    from fluxproject import FluxProject

    app = 0
    if QApplication.instance():
        app = QApplication.instance()
    else:
        app = QApplication(sys.argv)

    w = QWidget()
    w.resize(510, 210)
    v_box_1 = QVBoxLayout()

    proj = FluxProject("qalam.fluxml")
    proj.fontfeatures.features["mark"] = [proj.fontfeatures.routines[2]]
    proj.fontfeatures.features["curs"] = [proj.fontfeatures.routines[1]]

    # v = ValueRecord(yPlacement=0)
    # rule = Positioning(
    #     [["dda", "tda"]],
    #     [v],
    #     precontext=[["BEm2", "BEi3"]],
    #     postcontext=[["GAFm1", "GAFf1"]],
    # )
    rule = Substitution(input_=[["space"]], replacement=[["space"]])

    v_box_1.addWidget(QRuleEditor(proj, None))

    w.setLayout(v_box_1)

    w.show()
    sys.exit(app.exec_())
