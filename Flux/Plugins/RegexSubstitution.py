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
    QVBoxLayout,
    QTextEdit,
    QWidget
)
from PyQt5.QtGui import QValidator
from Flux.Plugins import FluxPlugin
from Flux.UI.qglyphname import QGlyphName
import re
import fontFeatures
from PyQt5.QtCore import Qt
import sys
from Flux.computedroutine import ComputedRoutine


plugin_name = "Regular Expression Substitution"


class REValidator(QValidator):
    def __init__(self):
        super().__init__()

    def validate(self, s, pos):
        try:
            re.compile(s)
        except Exception as e:
            return (QValidator.Intermediate, s, pos)
        return (QValidator.Acceptable, s, pos)

    def fixup(self, s):
        # Trim multiple spaces?
        pass

class Dialog(FluxPlugin):

    def __init__(self, project):
        self.project = project
        self.glyphnames = self.project.font.keys()
        self.routine = None
        super().__init__(project)

    def createForm(self):
        window = QWidget()
        window_layout = QVBoxLayout(window)

        before = QWidget()
        before_layout = QFormLayout(before)

        self.routine_name = QLineEdit()
        before_layout.addRow(QLabel(f"Routine name"), self.routine_name)

        self.before = QGlyphName(self.project, allow_classes=True, multiple=True)
        before_layout.addRow(QLabel(f"Match glyphs before"), self.before)
        window_layout.addWidget(before)

        form = QGroupBox()
        form_layout = QFormLayout(form)

        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Regular expression")
        self.filter.setValidator(REValidator())

        self.match = QLineEdit()
        self.match.setPlaceholderText("Regular expression")
        self.match.setValidator(REValidator())

        self.replace = QLineEdit()

        form_layout.addRow(QLabel(f"Match glyphs"), self.filter)
        form_layout.addRow(QLabel(f"Replace ..."), self.match)
        form_layout.addRow(QLabel(f"With ..."), self.replace)
        window_layout.addWidget(form)

        after = QWidget()
        after_layout = QFormLayout(after)
        self.after = QGlyphName(self.project, allow_classes=True, multiple=True)
        after_layout.addRow(QLabel(f"Match glyphs after"), self.after)
        window_layout.addWidget(after)

        self.preview = QTextEdit()
        window_layout.addWidget(self.preview)

        self.before.changed.connect(self.recompute)
        self.filter.textChanged.connect(self.recompute)
        self.match.textChanged.connect(self.recompute)
        self.replace.textChanged.connect(self.recompute)
        self.after.changed.connect(self.recompute)

        return window

    def parameters(self):
        return {
            "routine": self.routine_name.text(),
            "before": self.before.text(),
            "filter": self.filter.text(),
            "match": self.match.text(),
            "replace": self.replace.text(),
            "after": self.after.text(),
        }

    def recompute(self):
        if not self.filter.hasAcceptableInput() or not self.match.hasAcceptableInput():
            return
        p = self.parameters()
        self.routine = ComputedRoutine(name=p["routine"], parameters = p)
        self.routine.plugin = __name__
        self.routine.project = self.project
        self.routine.module = sys.modules[__name__]
        self.preview.setText(self.routine.asFea())


    def accept(self):
        self.project.fontfeatures.routines.extend([self.routine])
        return super().accept()

    # Disable enter
    def keyPressEvent(self, evt):
        if evt.key() == Qt.Key_Enter or evt.key() == Qt.Key_Return:
            return
        return super().keyPressEvent(evt)


def rulesFromComputedRoutine(routine):
    p = routine.parameters
    glyphnames = routine.project.font.keys()
    rules = []
    for g in glyphnames:
        if not re.search(p["filter"], g):
            continue
        try:
            new = re.sub(p["match"], p["replace"], g)
        except:
            continue
        if new not in glyphnames:
            continue
        sub = fontFeatures.Substitution( [[g]], [[new]])
        # XXX classes
        if p["before"]:
            sub.input = [ [glyph] for glyph in p["before"].split() ] + sub.input
        if p["after"]:
            sub.input.extend([ [glyph] for glyph in p["after"].split() ])
        rules.append(sub)
    return rules
