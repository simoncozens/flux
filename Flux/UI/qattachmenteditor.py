from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QListWidget,
    QCheckBox
)
from PyQt5.QtCore import pyqtSlot
from fontFeatures.shaperLib.Shaper import Shaper
from fontFeatures.shaperLib.Buffer import Buffer
from .qruleeditor import QRuleEditor
from fontFeatures import Attachment
import sys

class QAttachmentEditor(QRuleEditor):
    @pyqtSlot()
    def changeRepresentativeString(self):
        l = self.sender()
        glyph = l.currentItem().text()
        if l.role == "base":
            self.representative_string[0] = glyph
        else:
            self.representative_string[1] = glyph

        self.resetBuffer()

    @pyqtSlot()
    def updateRule(self):
        combo = self.sender()
        if combo.role == "mark":
            self.rule.mark_name = combo.currentText()
            self.rule.marks = self.project.fontfeatures.anchors[self.rule.mark_name]
        else:
            self.rule.base_name = combo.currentText()
            self.rule.bases = self.project.fontfeatures.anchors[self.rule.base_name]
        self.arrangeSlots()
        self.representative_string = self.makeRepresentativeString()
        self.resetBuffer()

    def makeFeatureButtons(self):
        self.clearLayout(self.featureButtonLayout)
        for f in self.availableFeatures:
            self.selectedFeatures.append(f)
            featureButton = QCheckBox(f)
            featureButton.setChecked(False)
            featureButton.stateChanged.connect(self.resetBuffer)
            self.featureButtonLayout.addWidget(featureButton)

    def makeASlot(self, anchorname, title):
        slot = QWidget()
        slotLayout = QVBoxLayout()
        slot.setLayout(slotLayout)

        label = QLabel(title[0].upper() + title[1:])
        slotLayout.addWidget(label)

        anchorChooser = QComboBox()
        anchors = list(sorted(self.project.fontfeatures.anchors.keys()))
        for a in anchors:
            anchorChooser.addItem(a)
        if anchorname in anchors:
            anchorChooser.setCurrentIndex(anchors.index(anchorname))
        anchorChooser.role = title
        anchorChooser.currentIndexChanged.connect(self.updateRule)
        slotLayout.addWidget(anchorChooser)

        slotLayout.addStretch()

        glyphList = QListWidget()
        if anchorname in self.project.fontfeatures.anchors:
            for g in self.project.fontfeatures.anchors[anchorname]:
                glyphList.addItem(g)
        glyphList.role = title
        glyphList.currentItemChanged.connect(self.changeRepresentativeString)
        slotLayout.addWidget(glyphList)
        return slot

    def resetBuffer(self):
        # We're not going to display the feature code because it's horrible.
        before = self.makeBuffer("before")
        if before and len(before.items) == 2:
            before.items[0].color = (255,120,120)
            before.items[-1].color = (120,255,120)
        if self.rule and self.rule.base_name and self.rule.mark_name:
            before.items[0].anchor = self.rule.bases[self.representative_string[0]]
            before.items[1].anchor = self.rule.marks[self.representative_string[1]]
            self.outputview_before.set_buf(before)
            self.outputview_after.set_buf(self.makeBuffer("after"))


    def arrangeSlots(self):
        self.clearLayout(self.slotview)
        if not self.rule:
            return

        self.slotview.addWidget(self.makeASlot(self.rule.base_name, "base"))
        self.slotview.addStretch()
        self.slotview.addWidget(self.makeASlot(self.rule.mark_name, "mark"))

    def makeRepresentativeString(self):
        inputglyphs = []
        if not self.rule or not self.rule.bases or not self.rule.marks:
            return inputglyphs

        inputglyphs = [ list(self.rule.bases.keys())[0], list(self.rule.marks.keys())[0] ]

        # We use this representative string to guess information about
        # how the *real* shaping process will take place; buffer direction
        # and script, and hence choice of complex shaper, and hence from
        # that choice of features to be processed.
        unicodes = [self.project.font.map_glyph_to_unicode(x) for x in inputglyphs]
        unicodes = [x for x in unicodes if x]
        tounicodes = "".join(map (chr, unicodes))
        bufferForGuessing = Buffer(self.project.font, unicodes = tounicodes)
        self.buffer_direction = bufferForGuessing.direction
        self.buffer_script = bufferForGuessing.script
        # print("Guessed buffer direction ", self.buffer_direction)
        # print("Guessed buffer script ", self.buffer_script)
        shaper = Shaper(self.project.fontfeatures, self.project.font)
        shaper.execute(bufferForGuessing)
        self.availableFeatures = []
        for stage in shaper.stages:
            if not isinstance(stage, list):
                continue
            for f in stage:
                if f not in self.availableFeatures and f in self.project.fontfeatures.features:
                    self.availableFeatures.append(f)
        self.makeFeatureButtons()

        return inputglyphs

if __name__ == "__main__":
    from Flux.project import FluxProject

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

    rule = Attachment(
        "top", "_top", proj.fontfeatures.anchors["top"], proj.fontfeatures.anchors["_top"]
    )
    v_box_1.addWidget(QAttachmentEditor(proj, None, rule))

    w.setLayout(v_box_1)

    w.show()
    sys.exit(app.exec_())
