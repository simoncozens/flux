from PyQt5.QtWidgets import QWidget, QApplication, QScrollArea, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QLineEdit, QSpinBox, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.jankyPOS.Buffer import Buffer
from qbufferrenderer import QBufferRenderer
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
        for ix,k in enumerate(self.fieldnames):
            t = QSpinBox()
            t.setSingleStep(10)
            t.setRange(-10000,10000)
            t.setValue(getattr(self.valuerecord, k) or 0)
            t.valueChanged.connect(self.serialize)
            # label = QLabel(t)
            # label.setText(self.labelnames[ix])
            # label.move(label.x()+0,label.y()-50)
            self.boxes.append(t)
            self.boxlayout.addWidget(t)
        self.setLayout(self.boxlayout)

    def serialize(self):
        for ix,k in enumerate(self.fieldnames):
            try:
                val = int(self.boxes[ix].text())
                setattr(self.valuerecord, k, int(self.boxes[ix].value()))
            except Exception as e:
                print(e)
        print(self.valuerecord.asFea())
        self.changed.emit()


class QRuleEditor(QSplitter):
    def __init__(self, project, rule): # Rule is some fontFeatures object
        self.project = project
        self.rule = rule
        self.representative_string = self.makeRepresentativeString()
        print(self.representative_string)
        self.inputslots = []
        self.precontextslots = []
        self.postcontextslots = []
        self.outputslots = []

        super(QRuleEditor, self).__init__()


        self.slotview = QHBoxLayout()
        self.arrangeSlots()
        scroll = QScrollArea()
        scroll.setLayout(self.slotview)


        self.outputview_before = QBufferRenderer(project, self.beforeBuffer())
        self.outputview_after  = QBufferRenderer(project, self.afterBuffer())
        self.before_after = QWidget()
        self.before_after_layout_v = QVBoxLayout()

        self.asFea = QLabel(self.rule.asFea())

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

        # scroll.setWidgetResizable(True)

    def resetBuffer(self):
        self.asFea.setText(self.rule.asFea())
        print(self.representative_string)
        self.outputview_after.set_buf(self.afterBuffer())
        self.outputview_before.set_buf(self.beforeBuffer())

    @pyqtSlot()
    def changeRepresentativeString(self):
        l = self.sender()
        print("L was %i , %s " % (l.slotnumber, l.text()))
        self.representative_string[l.slotnumber] = l.text()
        self.resetBuffer()

    @pyqtSlot()
    def addGlyphToSlot(self):
        print("Add a glyph")
        l = self.sender()
        glyphname = l.text()
        self.rule.glyphs[l.slotindex].append(glyphname)
        self.arrangeSlots()

    def makeASlot(self, slotnumber, contents, style=None, editingWidgets = None):
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
            line.returnPressed.connect(self.addGlyphToSlot)
            slotLayout.addWidget(line)
            slotLayout.addStretch()
            if editingWidgets:
                slotLayout.addWidget(editingWidgets[ix])
            slotnumber = slotnumber + 1

            slot.setLayout(slotLayout)
            self.slotview.addWidget(slot)
        return slotnumber

    def makeEditingWidgets(self):
        editingWidgets = []
        for ix,i in enumerate(self.rule.shaper_inputs()):
            if isinstance(self.rule,Positioning):
                widget = QValueRecordEditor(self.rule.valuerecords[ix])
                widget.changed.connect(self.resetBuffer)
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

        self.slotview.addStretch()
        slotnumber = 0
        if hasattr(self.rule, "precontext"):
            slotnumber = self.makeASlot(slotnumber, self.rule.precontext,"background-color:#ffaaaa;")

        editingWidgets = self.makeEditingWidgets()
        slotnumber = self.makeASlot(slotnumber, self.rule.shaper_inputs(), editingWidgets=editingWidgets)

        if hasattr(self.rule, "postcontext"):
            self.makeASlot(slotnumber, self.rule.postcontext,"background-color:#aaaaff;")

        self.slotview.addStretch()

    def makeRepresentativeString(self):
        inputglyphs = []
        if hasattr(self.rule, "precontext"):
            inputglyphs.extend([ x[0] for x in self.rule.precontext ])

        inputglyphs.extend( [ x[0] for x in self.rule.shaper_inputs() ] )

        if hasattr(self.rule, "postcontext"):
            inputglyphs.extend([ x[0] for x in self.rule.postcontext ])

        return inputglyphs

    def beforeBuffer(self):
        buf = Buffer(self.project.font,
            glyphs = self.representative_string,
            direction = "RTL")
        shaper = Shaper(proj.fontfeatures, proj.font)
        shaper.execute(buf)
        return buf

    def afterBuffer(self):
        buf = Buffer(self.project.font,
            glyphs = self.representative_string,
            direction = "RTL")
        shaper = Shaper(proj.fontfeatures, proj.font)
        shaper.execute(buf)
        self.rule.apply_to_buffer(buf)
        return buf


if __name__ == "__main__":
    from fluxproject import FluxProject
    from fontFeatures import Positioning, ValueRecord

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

    v = ValueRecord(yPlacement=0)
    rule = Positioning( [["dda", "tda"]], [v],
        precontext = [["BEm2","BEi3"]],
        postcontext = [["GAFm1", "GAFf1"]],
    )

    v_box_1.addWidget(QRuleEditor(proj, rule))

    w.setLayout(v_box_1)


    w.show()
    sys.exit(app.exec_())
