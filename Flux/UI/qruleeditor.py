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
    QSizePolicy,
    QStyle
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QStringListModel, QSize
from fontFeatures.shaperLib.Shaper import Shaper
from .qbufferrenderer import QBufferRenderer
from .qglyphname import QGlyphName
from fontFeatures import (
    Positioning,
    ValueRecord,
    Substitution,
    Chaining,
    Rule,
    Routine,
    RoutineReference,
)
import sys
import darkdetect
from Flux.variations import VariationAwareBuffer, VariationAwareBufferItem
from fontFeatures.shaperLib.Buffer import Buffer, BufferItem


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

    def __init__(self, vr, vf=None, master=None):
        self.valuerecord = vr
        self.boxlayout = QHBoxLayout()
        self.boxes = []
        self.master = master
        self.vf = vf
        super(QWidget, self).__init__()
        self.add_boxes()
        self.prep_fields()

    def add_boxes(self):
        for ix, k in enumerate(self.fieldnames):
            t = QSpinBox()
            t.setSingleStep(10)
            t.setRange(-10000, 10000)
            t.valueChanged.connect(self.serialize)
            self.boxes.append(t)
            self.boxlayout.addWidget(t)

    def prep_fields(self):
        vr = self.valuerecord
        if self.master:
            vr = self.valuerecord.get_value_for_master(self.vf, self.master)
        for ix, k in enumerate(self.fieldnames):
            t = self.boxes[ix]
            t.setValue(getattr(vr, k) or 0)
            # label = QLabel(t)
            # label.setText(self.labelnames[ix])
            # label.move(label.x()+0,label.y()-50)
        self.setLayout(self.boxlayout)

    def change_master(self, master):
        self.serialize()
        self.master = master
        self.prep_fields()

    def serialize(self):
        value = {self.fieldnames[ix]: int(self.boxes[ix].value()) for ix in range(len(self.boxes))}

        if self.master:
            self.valuerecord.set_value_for_master(self.vf, self.master, ValueRecord(**value))
        else:
            for attr, val in value.items():
                setattr(self.valuerecord, attr, val)
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
        self.all_valuerecord_editors = []
        self.index = None
        if rule:
            self.backup_rule = Rule.fromXML(rule.toXML())  # Deep copy
        else:
            self.backup_rule = None

        super(QRuleEditor, self).__init__()

        splitter = QSplitter()
        self.slotview = QHBoxLayout()
        scroll = QScrollArea()
        scroll.setLayout(self.slotview)

        self.outputview_before = QBufferRenderer(project, VariationAwareBuffer(self.project.font))
        self.outputview_after = QBufferRenderer(project, VariationAwareBuffer(self.project.font))
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

        if self.project.variations:
            self.master_selection = QComboBox()
            for mastername in self.project.variations.masters:
                self.master_selection.addItem(mastername)
            self.master_selection.currentTextChanged.connect(self.masterChanged)
            self.before_after_layout_v.addWidget(self.master_selection)
        else:
            self.master_selection = None

        self.before_after_layout_v.addWidget(featureButtons)
        self.before_after_layout_v.addWidget(self.asFea)
        self.before_after_layout_v.addWidget(layoutarea)

        self.before_after.setLayout(self.before_after_layout_v)

        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(scroll)

        splitter.addWidget(self.before_after)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
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

    @property
    def currentMaster(self):
        if not self.master_selection:
            return None
        return self.master_selection.currentText()

    def masterChanged(self):
        for qvre in self.all_valuerecord_editors:
            qvre.change_master(self.currentMaster)
        self.resetBuffer()

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

    @property
    def location(self):
        sourceIndex = list(self.project.variations.masters.keys()).index(self.currentMaster)
        return self.project.variations.designspace.sources[sourceIndex].location

    def resetBuffer(self):
        if self.rule:
            try:
                self.asFea.setText(self.rule.asFea())
            except Exception as e:
                print("Can't serialize", e)
        self.outputview_before.set_buf(self.makeBuffer("before"))
        self.outputview_after.set_buf(self.makeBuffer("after"))
        if self.currentMaster:
            self.outputview_before.set_location(self.location)
            self.outputview_after.set_location(self.location)

    @pyqtSlot()
    def changeRepresentativeString(self):
        l = self.sender()
        if l.text().startswith("@"):
            self.representative_string[
                l.slotnumber
            ] = self.project.fontfeatures.namedClasses[l.text()[1:]][0]
        else:
            self.representative_string[l.slotnumber] = l.text()

        self.resetBuffer()

    @pyqtSlot()
    def replacementChanged(self):
        l = self.sender()
        replacements = l.text().split()
        self.rule.replacement = [[x] for x in replacements]
        self.resetBuffer()

    @pyqtSlot()
    def addGlyphToSlot(self):
        l = self.sender()
        glyphname = l.text()
        # Check for class names
        if (
            glyphname.startswith("@")
            and glyphname[1:] in self.project.fontfeatures.namedClasses.keys()
        ):
            # It's OK
            pass
        elif glyphname not in self.project.font.keys():
            print(f"{glyphname} not found")
            l.setText("")
            return
        print("Adding ", glyphname)
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
                elif (
                    isinstance(self.rule, Substitution)
                    and len(self.rule.shaper_inputs()) == 1
                ):
                    self.rule.replacement.insert(0, [])
                elif isinstance(self.rule, Chaining):
                    self.rule.lookups.insert(0, [])
        elif action == "+>":
            sender.contents.append([])
            # If these are input glyphs, add another replacement etc.
            if sender.contents == self.rule.shaper_inputs():
                if isinstance(self.rule, Positioning):
                    self.rule.valuerecords.append(ValueRecord())
                elif (
                    isinstance(self.rule, Substitution)
                    and len(self.rule.shaper_inputs()) == 1
                ):
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
            if style:
                slot.setStyleSheet(style)


            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scrollWidget = QWidget()
            scrollLayout = QVBoxLayout()
            scrollWidget.setLayout(scrollLayout)
            scroll.setWidget(scrollWidget)
            for ixWithinSlot, glyph in enumerate(glyphslot):
                glyphHolder = QWidget()
                glyphHolderLayout = QHBoxLayout()
                glyphHolder.setLayout(glyphHolderLayout)
                l = QPushButton(glyph)
                l.setDefault(False)
                l.setAutoDefault(False)
                l.slotnumber = slotnumber
                l.clicked.connect(self.changeRepresentativeString)
                glyphHolderLayout.addWidget(l)

                remove = QPushButton("x")
                remove.slotindex = ix
                remove.indexWithinSlot = ixWithinSlot
                remove.contents = contents
                remove.clicked.connect(self.removeGlyphFromSlot)
                glyphHolderLayout.addWidget(remove)
                scrollLayout.addWidget(glyphHolder)

            slotLayout.addWidget(scroll)

            # This is the part that adds a new glyph to a slot
            newglyph = QGlyphName(self.project, allow_classes=True)
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

    def lookupCombobox(self, current, warning):
        c = QComboBox()
        c.warning = warning
        names = [
            x.name
            for x in self.project.fontfeatures.routines
            if not hasattr(x, "comment")
        ]
        names = ["--- No lookup ---"] + names
        for name in names:
            c.addItem(name)
        if current in names:
            c.setCurrentIndex(names.index(current))
        self.setComboboxWarningIfNeeded(c)
        return c

    @pyqtSlot()
    def chainingLookupChanged(self):
        l = self.sender()
        if l.currentIndex() == 0:
            self.rule.lookups[l.ix] = []
        else:
            self.rule.lookups[l.ix] = [RoutineReference(name=l.currentText())]
        self.setComboboxWarningIfNeeded(l)
        self.resetBuffer()

    def changesGlyphstringLength(self, routine, depth=1):
        if depth > 10:
            return False
        for r in routine.rules:
            if isinstance(r, Substitution) and len(r.input) != len(r.replacement):
                return True
            elif isinstance(r, Chaining):
                for lus in r.lookups:
                    for l in (lus or []):
                        if self.changesGlyphstringLength(l.routine, depth+1):
                            return True
        return False

    def setComboboxWarningIfNeeded(self, combobox):
        # Find routine
        rname = combobox.currentText()
        warningNeeded = False
        if rname:
            routine = None
            for r in self.project.fontfeatures.routines:
                if r.name == rname:
                    routine = r
        if routine and self.changesGlyphstringLength(routine):
            stdicon = self.style().standardIcon(QStyle.SP_MessageBoxWarning)
            combobox.warning.setPixmap(stdicon.pixmap(stdicon.actualSize(QSize(16, 16))))
            combobox.warning.setToolTip("<qt>This lookup may change the length of the glyph stream. Subsequent lookups may not fire at the glyph slots you expect.</qt>")
        else:
            combobox.warning.clear()
            combobox.warning.setToolTip("")

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
            widget = QGlyphName(
                self.project, multiple=len(self.rule.shaper_inputs()) < 2
            )
            widget.setText(" ".join(replacements) or "")
            widget.position = 0
            widget.returnPressed.connect(self.replacementChanged)
            editingWidgets.append(widget)
        else:
            for ix, i in enumerate(self.rule.shaper_inputs()):
                if isinstance(self.rule, Positioning):
                    widget = QValueRecordEditor(self.rule.valuerecords[ix],
                        vf=self.project.variations,
                        master=self.currentMaster)
                    widget.changed.connect(self.resetBuffer)
                    editingWidgets.append(widget)
                    self.all_valuerecord_editors.append(widget)
                elif isinstance(self.rule, Chaining):
                    lookup = self.rule.lookups[ix] and self.rule.lookups[ix][0].name
                    w = QWidget()
                    wl = QHBoxLayout(w)
                    w.setLayout(wl)
                    warning = QLabel()
                    widget = self.lookupCombobox(lookup, warning)
                    widget.ix = ix
                    widget.currentTextChanged.connect(self.chainingLookupChanged)
                    wl.addWidget(widget)
                    wl.addWidget(warning)
                    editingWidgets.append(w)
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
        self.all_valuerecord_editors = []
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
            self.makeASlot(slotnumber, self.rule.postcontext, postcontext_style)

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
            if (
                g.startswith("@")
                and g[1:] in self.project.fontfeatures.namedClasses.keys()
            ):
                representative_string[ix] = self.project.fontfeatures.namedClasses[
                    g[1:]
                ][0]

        # We use this representative string to guess information about
        # how the *real* shaping process will take place; buffer direction
        # and script, and hence choice of complex shaper, and hence from
        # that choice of features to be processed.
        unicodes = [
            self.project.font.codepointForGlyph(x) for x in representative_string
        ]
        unicodes = [x for x in unicodes if x]
        tounicodes = "".join(map(chr, unicodes))
        bufferForGuessing = Buffer(self.project.font, unicodes=tounicodes)
        self.buffer_direction = bufferForGuessing.direction
        self.buffer_script = bufferForGuessing.script
        # print("Guessed buffer direction ", self.buffer_direction)
        # print("Guessed buffer script ", self.buffer_script)
        shaper = Shaper(self.project.fontfeatures, self.project.font)
        bufferForGuessing = Buffer(self.project.font, glyphs=representative_string)
        shaper.execute(bufferForGuessing)
        self.availableFeatures = []
        for stage in shaper.stages:
            if not isinstance(stage, list):
                continue
            for f in stage:
                if (
                    f not in self.availableFeatures
                    and f in self.project.fontfeatures.features
                ):
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
            features.append({"tag": item.text(), "value": item.isChecked()})
        return features

    def makeBuffer(self, before_after="before"):
        buf = VariationAwareBuffer(
            self.project.font,
            direction=self.buffer_direction,
        )
        if self.project.variations:
            buf.location = self.location
            buf.vf = self.project.variations
        buf.items = [VariationAwareBufferItem.new_glyph(g, self.project.font, buf) for g in self.representative_string]
        shaper = Shaper(self.project.fontfeatures, self.project.font)

        shaper.execute(buf, features=self.makeShaperFeatureArray())
        routine = Routine(rules=[self.rule])
        # print("Before shaping: ", buf.serialize())
        if before_after == "after" and self.rule:
            print("Before application: ", buf.serialize())
            print(self.rule.asFea())
            buf.clear_mask()  # XXX
            try:
                routine.apply_to_buffer(buf)
            except Exception as e:
                print("Couldn't shape: " + str(e))
            print("After application: ", buf.serialize())
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
