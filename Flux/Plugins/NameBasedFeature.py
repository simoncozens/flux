from PyQt5.QtWidgets import (
    QLabel,
    QDialog,
    QLineEdit,
    QGroupBox,
    QCompleter,
    QFormLayout,
    QComboBox,
    QMessageBox,
    QCheckBox,
)
from PyQt5.QtGui import QValidator
from Flux.Plugins import FluxPlugin
import re
import fontFeatures


plugin_name = "Name-Based Features"


class REValidator(QValidator):
    def __init__(self):
        super().__init__()

    def validate(self, s, pos):
        try:
            re.compile(s)
        except Exception as e:
            return (QValidator.Invalid, s, pos)
        return (QValidator.Acceptable, s, pos)

    def fixup(self, s):
        # Trim multiple spaces?
        pass


class NameBasedFeature:
    def __init__(self, project):
        self.project = project
        self.glyphnames = self.project.font.keys()

    def matches(self):
        return [g for g in self.glyphnames if re.search(self.glyphSuffixRE + "$", g)]

    def applicable(self):
        return len(self.matches()) > 0

    def transform(self, right):
        left = [re.sub(self.glyphSuffixRE, "", g) for g in right]
        return left

    def apply(self):
        right = self.matches()
        left = self.transform(right)
        left2, right2 = [], []
        routine = fontFeatures.Routine(name=self.name.title().replace(" ", ""))
        for l, r in zip(left, right):
            if l in self.glyphnames and r in self.glyphnames:
                routine.addRule(fontFeatures.Substitution([[l]], [[r]]))
        self.project.fontfeatures.routines.extend([routine])
        self.project.fontfeatures.addFeature(self.feature, [routine])


class SlashZero(NameBasedFeature):
    glyphSuffixRE = ".zero"
    feature = "zero"
    name = "slash zero"


class SmallCaps(NameBasedFeature):
    glyphSuffixRE = ".sc"
    feature = "smcp"
    name = "small caps"

    def transform(self, right):
        left = super().transform(right)
        return [g[0].lower() + g[1:] for g in left]


class CapToSmallCaps(NameBasedFeature):
    glyphSuffixRE = ".sc"
    feature = "c2sc"
    name = "caps to small caps"


class Dialog(FluxPlugin):
    tests = [SlashZero, SmallCaps, CapToSmallCaps]

    def createForm(self):
        form = QGroupBox()
        layout = QFormLayout()

        self.boxes = []

        for testclass in self.tests:
            test = testclass(self.project)
            if test.applicable():
                box = QCheckBox()
                box.setChecked(True)
                box.test = test
                layout.addRow(QLabel(f"Derive {testclass.name} feature?"), box)
                self.boxes.append(box)
            else:
                layout.addRow(
                    QLabel(
                        f"No {testclass.glyphSuffixRE} glyphs found for {testclass.name}"
                    )
                )

        form.setLayout(layout)
        return form

    def accept(self):
        for b in self.boxes:
            if b.isChecked():
                b.test.apply()
        return super().accept()
