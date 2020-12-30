from dataclasses import dataclass
from lxml import etree
from Flux.UI.qglyphname import QGlyphPicker, QGlyphBox
from PyQt5.QtWidgets import (
    QWidget,
    QDialog,
    QFormLayout,
    QSpinBox,
    QApplication,
    QVBoxLayout,
    QLabel,
    QDialogButtonBox,
    QComboBox,
)
from PyQt5.QtCore import Qt
from typing import Optional


@dataclass
class GlyphAction:
    glyph: str
    width: Optional[int] = None
    category: Optional[str] = None
    duplicate_from: Optional[str] = None

    def toXML(self):
        root = etree.Element("glyphaction")
        root.attrib["glyph"] = self.glyph
        if self.duplicate_from:
            root.attrib["duplicate_from"] = self.duplicate_from
        if self.width is not None:
            root.attrib["width"] = str(self.width)
        if self.category:
            root.attrib["category"] = self.category
        return root

    @classmethod
    def fromXML(klass, el):
        return klass(
            glyph=el.get("glyph"),
            duplicate_from=el.get("duplicate_from"),
            width=int(el.get("width")),
            category=el.get("category"),
        )

    def perform(self, font):
        if self.duplicate_from:
            font[self.glyph] = font[self.duplicate_from].copy()
        if self.width is not None:
            font[self.glyph].width = self.width
        if self.category:
            font[self.glyph].set_category(self.category)

    def doesSomething(self, font):
        effect = self.duplicate_from is not None
        if self.width is not None and self.width != font[self.glyph].width:
            effect = True
        if self.category is not None and self.category != font[self.glyph].category:
            effect = True
        return effect


class QGlyphActionDialog(QDialog):
    def __init__(self, project, glyphname):
        super(QDialog, self).__init__()
        v_box_1 = QVBoxLayout()
        self.project = project
        self.glyph = self.project.font[glyphname]

        self.formWidget = QWidget()
        self.formLayout = QFormLayout()
        self.formWidget.setLayout(self.formLayout)

        self.widthLine = QSpinBox()
        self.widthLine.setMinimum(0)
        self.widthLine.setMaximum(2000)
        self.widthLine.setValue(self.glyph.width)

        self.categoryCB = QComboBox()
        items = ["base", "ligature", "mark"]
        self.categoryCB.addItems(items)
        if self.glyph.category in items:
            self.categoryCB.setCurrentIndex(items.index(self.glyph.category))

        self.formLayout.addRow(QLabel(glyphname))
        self.formLayout.addRow(QLabel("Width"), self.widthLine)
        self.formLayout.addRow(QLabel("Category"), self.categoryCB)

        v_box_1.addWidget(self.formWidget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        v_box_1.addWidget(buttons)
        self.setLayout(v_box_1)

    def accept(self):
        self.action = self.project.glyphactions.get(
            self.glyph.name, GlyphAction(glyph=self.glyph.name)
        )
        newWidth = self.widthLine.value()
        if newWidth != self.glyph.width:
            self.action.width = newWidth
        newCategory = self.categoryCB.currentText()
        if newCategory != self.glyph.category:
            self.action.category = newCategory
        return super().accept()


class QGlyphActionBox(QGlyphBox):
    def mouseDoubleClickEvent(self, event):
        dialog = QGlyphActionDialog(self.parent.project, self.glyph)
        result = dialog.exec_()
        if result:
            action = dialog.action
            if action.doesSomething(self.parent.project.font):
                print(etree.tostring(action.toXML()))
                action.perform(self.parent.project.font)
                self.parent.project.glyphactions[action.glyph] = action


class QGlyphActionPicker(QGlyphPicker):
    def setupGrid(self):
        self.clearLayout(self.qgrid)
        for g in self.project.font.keys():
            w = QGlyphActionBox(self, g)
            self.widgets[g] = w

    @classmethod
    def pickGlyph(self, project):
        dialog = QGlyphActionPicker(project)
        result = dialog.exec_()
        if dialog.selected:
            return dialog.selected.glyph


if __name__ == "__main__":
    from Flux.project import FluxProject
    import sys

    app = 0
    if QApplication.instance():
        app = QApplication.instance()
    else:
        app = QApplication(sys.argv)
    proj = FluxProject("qalam.fluxml")
    QGlyphActionPicker.pickGlyph(proj)
    sys.exit(app.exec_())
