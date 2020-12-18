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
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QCompleter,
    QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QStringListModel
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.shaperLib.Buffer import Buffer
from .qbufferrenderer import QBufferRenderer
from .qglyphname import QGlyphName
from fontFeatures import Positioning, ValueRecord, Substitution, Chaining, Rule, Routine
import sys
import darkdetect

if darkdetect.isDark():
    precontext_style = "background-color: #322b2b"
    postcontext_style = "background-color: #2b2b32"
else:
    precontext_style = "background-color: #ffaaaa"
    postcontext_style = "background-color: #aaaaff"


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


class QRuleEditor(QDialog):
    def __init__(self, project, editor, rule):  # Rule is some fontFeatures object
        self.project = project
        self.editor = editor
        self.inputslots = []
        self.precontextslots = []
        self.postcontextslots = []
        self.outputslots = []
        self.buffer_direction = "RTL"
        self.buffer_script = "Latin"
        self.index = None
        if rule:
            self.backup_rule = Rule.fromXML(rule.toXML()) # Deep copy
        else:
            self.backup_rule = None

        super(QRuleEditor, self).__init__()

        splitter = QSplitter()
        self.slotview = QHBoxLayout()
        scroll = QScrollArea()
        scroll.setLayout(self.slotview)

        self.outputview_before = QBufferRenderer(project)
        self.outputview_after = QBufferRenderer(project)
        self.before_after = QWidget()
        self.before_after_layout_v = QVBoxLayout()

        self.asFea = QLabel()

        featureButtons = QWidget()
        self.featureButtonLayout = QHBoxLayout()
        featureButtons.setLayout(self.featureButtonLayout)
        self.selectedFeatures = []

        layoutarea = QWidget()
        self.before_after_layout_h = QHBoxLayout()
        self.before_after_layout_h.addWidget(self.outputview_before)
        self.before_after_layout_h.addWidget(self.outputview_after)
        layoutarea.setLayout(self.before_after_layout_h)

        self.before_after_layout_v.addWidget(featureButtons)
        self.before_after_layout_v.addWidget(self.asFea)
        self.before_after_layout_v.addWidget(layoutarea)

        self.before_after.setLayout(self.before_after_layout_v)

        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(scroll)

        splitter.addWidget(self.before_after)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        for button in buttons.buttons():
            button.setDefault(False)
            button.setAutoDefault(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        v_box_1 = QVBoxLayout()
        self.setLayout(v_box_1)
        v_box_1.addWidget(splitter)
        v_box_1.addWidget(buttons)
        self.setRule(rule)

    def keyPressEvent(self, evt):
        return

    def accept(self):
        self.editor.fontfeaturespanel.lookuplist.update(self.index)
        self.editor.setWindowModified(True)
        self.editor.showDebugger()

    def reject(self):
        for k in dir(self.backup_rule):
            self.rule = getattr(self.backup_rule, k)
        self.editor.fontfeaturespanel.lookuplist.update()
        self.editor.showDebugger()

    def setRule(self, rule, index=None):
        self.rule = rule
        self.index = index
        self.arrangeSlots()
        self.representative_string = self.makeRepresentativeString()
        self.resetBuffer()

    def resetBuffer(self):
        if self.rule:
            try:
                self.asFea.setText(self.rule.asFea())
            except Exception as e:
                print("Can't serialize" , e)
        self.outputview_before.set_buf(self.makeBuffer("before"))
        self.outputview_after.set_buf(self.makeBuffer("after"))

    @pyqtSlot()
    def changeRepresentativeString(self):
        l = self.sender()
        if l.text().startswith("@"):
            self.representative_string[l.slotnumber] = self.project.fontfeatures.namedClasses[l.text()[1:]][0]
        else:
            self.representative_string[l.slotnumber] = l.text()

        self.resetBuffer()

    @pyqtSlot()
    def replacementChanged(self):
        l = self.sender()
        replacements = l.text().split()
        self.rule.replacement = [ [x] for x in replacements ]
        self.resetBuffer()

    @pyqtSlot()
    def addGlyphToSlot(self):
        l = self.sender()
        glyphname = l.text()
        # Check for class names
        if glyphname.startswith("@") and glyphname[1:] in self.project.fontfeatures.namedClasses.keys():
            # It's OK
            pass
        elif glyphname not in self.project.font.keys():
            print(f'{glyphname} not found')
            l.setText("")
            return
        l.owner.contents[l.owner.slotindex].append(glyphname)
        self.arrangeSlots()
        self.representative_string = self.makeRepresentativeString()
        self.resetBuffer()

    @pyqtSlot()
    def removeGlyphFromSlot(self):
        l = self.sender()
        del l.contents[l.slotindex][l.indexWithinSlot]
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
                elif isinstance(self.rule, Substitution) and len(self.rule.shaper_inputs()) == 1:
                    self.rule.replacement.insert(0, [])
                elif isinstance(self.rule, Chaining):
                    self.rule.lookups.insert(0, [])
        elif action == "+>":
            sender.contents.append([])
            # If these are input glyphs, add another replacement etc.
            if sender.contents == self.rule.shaper_inputs():
                if isinstance(self.rule, Positioning):
                    self.rule.valuerecords.append(ValueRecord())
                elif isinstance(self.rule, Substitution) and len(self.rule.shaper_inputs()) == 1:
                    self.rule.replacement.append([])
                elif isinstance(self.rule, Chaining):
                    self.rule.lookups.append([])

        elif action == "-":
            del sender.contents[self.sender().ix]
        self.arrangeSlots()
        self.representative_string = self.makeRepresentativeString()
        self.resetBuffer()

    def makeASlot(self, slotnumber, contents, style=None, editingWidgets=None):
        print(f'slot number {slotnumber} editing widgets', editingWidgets)
        for ix, glyphslot in enumerate(contents):
            slot = QWidget()
            slotLayout = QVBoxLayout()
            if style:
                slot.setStyleSheet(style)

            for ixWithinSlot, glyph in enumerate(glyphslot):
                glyphHolder = QWidget()
                glyphHolderLayout = QHBoxLayout()
                glyphHolder.setLayout(glyphHolderLayout)
                l = QPushButton(glyph)
                l.setDefault(False)
                l.setAutoDefault(False)
                l.slotnumber = slotnumber
                # l.setFlat(True)
                l.clicked.connect(self.changeRepresentativeString)
                # l.setAlignment(Qt.AlignCenter)
                # if style:
                #     l.setStyleSheet(style)
                glyphHolderLayout.addWidget(l)

                remove = QPushButton("x")
                remove.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Preferred)
                remove.slotindex = ix
                remove.indexWithinSlot = ixWithinSlot
                remove.contents = contents
                remove.clicked.connect(self.removeGlyphFromSlot)
                glyphHolderLayout.addWidget(remove)

                slotLayout.addWidget(glyphHolder)

            # This is the part that adds a new glyph to a slot
            newglyph = QGlyphName(self.project)
            newglyph.slotindex = ix
            newglyph.contents = contents
            newglyph.glyphline.returnPressed.connect(self.addGlyphToSlot)
            slotLayout.addWidget(newglyph)


            slotLayout.addStretch()
            if editingWidgets and ix < len(editingWidgets):
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

    def lookupCombobox(self, current):
        c = QComboBox()
        names = [x.name for x in self.project.fontfeatures.routines]
        for name in names:
            c.addItem(name)
        if current in names:
            c.setCurrentIndex(names.index(current))
        elif current: # XXX fontFeatures needs refactoring
            c.addItem(current)
            c.setCurrentIndex(len(names))
        return c

    def addPrecontext(self):
        self.rule.precontext = [[]]
        self.arrangeSlots()

    def addPostcontext(self):
        self.rule.postcontext = [[]]
        self.arrangeSlots()

    def makeEditingWidgets(self):
        editingWidgets = []
        if isinstance(self.rule, Substitution):
            replacements = [x[0] for x in self.rule.replacement if x]
            widget = QGlyphName(self.project, multiple = len(self.rule.shaper_inputs()) < 2)
            widget.setText(" ".join(replacements) or "")
            widget.position = 0
            widget.returnPressed.connect(self.replacementChanged)
            editingWidgets.append(widget)
        else:
            for ix, i in enumerate(self.rule.shaper_inputs()):
                if isinstance(self.rule, Positioning):
                    widget = QValueRecordEditor(self.rule.valuerecords[ix])
                    widget.changed.connect(self.resetBuffer)
                    editingWidgets.append(widget)
                elif isinstance(self.rule, Chaining):
                    lookup = self.rule.lookups[ix] and self.rule.lookups[ix][0].name
                    widget = self.lookupCombobox(lookup)
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

        slotnumber = 0

        if not hasattr(self.rule, "precontext") or not self.rule.precontext:
            widget = QPushButton("<<+")
            widget.clicked.connect(self.addPrecontext)
            self.slotview.addWidget(widget)
        else:
            self.slotview.addStretch()
            slotnumber = self.makeASlot(
                slotnumber, self.rule.precontext, precontext_style
            )

        editingWidgets = self.makeEditingWidgets()
        slotnumber = self.makeASlot(
            slotnumber, self.rule.shaper_inputs(), editingWidgets=editingWidgets
        )

        if not hasattr(self.rule, "postcontext") or not self.rule.postcontext:
            widget = QPushButton("+>>")
            widget.clicked.connect(self.addPostcontext)
            self.slotview.addWidget(widget)
        else:
            self.makeASlot(
                slotnumber, self.rule.postcontext, postcontext_style
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

        representative_string = [x for x in inputglyphs if x]
        for ix, g in enumerate(representative_string):
            if g.startswith("@") and g[1:] in self.project.fontfeatures.namedClasses.keys():
                representative_string[ix] = self.project.fontfeatures.namedClasses[g[1:]][0]

        # We use this representative string to guess information about
        # how the *real* shaping process will take place; buffer direction
        # and script, and hence choice of complex shaper, and hence from
        # that choice of features to be processed.
        unicodes = [self.project.font.codepointForGlyph(x) for x in representative_string]
        unicodes = [x for x in unicodes if x]
        tounicodes = "".join(map (chr, unicodes))
        bufferForGuessing = Buffer(self.project.font, unicodes = tounicodes)
        self.buffer_direction = bufferForGuessing.direction
        self.buffer_script = bufferForGuessing.script
        # print("Guessed buffer direction ", self.buffer_direction)
        # print("Guessed buffer script ", self.buffer_script)
        shaper = Shaper(self.project.fontfeatures, self.project.font)
        bufferForGuessing = Buffer(self.project.font, glyphs = representative_string)
        shaper.execute(bufferForGuessing)
        self.availableFeatures = []
        for stage in shaper.stages:
            if not isinstance(stage, list):
                continue
            for f in stage:
                if f not in self.availableFeatures and f in self.project.fontfeatures.features:
                    self.availableFeatures.append(f)
        self.makeFeatureButtons()

        return representative_string

    def makeFeatureButtons(self):
        self.clearLayout(self.featureButtonLayout)
        for f in self.availableFeatures:
            self.selectedFeatures.append(f)
            featureButton = QCheckBox(f)
            featureButton.setChecked(True)
            featureButton.stateChanged.connect(self.resetBuffer)
            self.featureButtonLayout.addWidget(featureButton)

    def makeShaperFeatureArray(self):
        features = []
        for i in range(self.featureButtonLayout.count()):
            item = self.featureButtonLayout.itemAt(i).widget()
            features.append({ "tag": item.text(), "value": item.isChecked() })
        return features


    def makeBuffer(self, before_after="before"):
        buf = Buffer(
            self.project.font, glyphs=self.representative_string, direction=self.buffer_direction
        )
        shaper = Shaper(self.project.fontfeatures, self.project.font)

        shaper.execute(buf,features = self.makeShaperFeatureArray())
        routine = Routine(rules=[self.rule])
        if before_after == "after" and self.rule:
            buf.clear_mask() # XXX
            try:
                routine.apply_to_buffer(buf)
            except Exception as e:
                print("Couldn't shape: "+str(e))
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
