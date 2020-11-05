from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QPushButton,
    QCompleter,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QScrollArea,
    QGridLayout,
    QScrollArea,
     QStyle,

)
from Flux.ThirdParty.QFlowLayout import QFlowLayout
from fontFeatures.shaperLib.Buffer import Buffer
from Flux.UI.qbufferrenderer import QBufferRenderer
from PyQt5.QtCore import Qt, pyqtSignal, QStringListModel, QMargins
from PyQt5.QtGui import QValidator

import darkdetect

if darkdetect.isDark():
    selected_style = "background-color: #322b2b;"
    deselected_style = "background-color: #322b2b;"
else:
    selected_style = "background-color: #322b2b;"


class GlyphNameValidator(QValidator):
    def __init__(self, parent):
        super().__init__()
        self.glyphSet = parent.project.font.keys()
        self.multiple = parent.multiple
        self.allow_classes = parent.allow_classes

    def validate(self, s, pos):
        if s in self.glyphSet:
            return (QValidator.Acceptable, s, pos)
        if not self.multiple and " " in s:
            return (QValidator.Invalid, s, pos)
        if not self.allow_classes and "@" in s:
            return (QValidator.Invalid, s, pos)
        # XXX Other things not acceptable in glyphs here?
        if self.multiple:
            if all([ (g in self.glyphSet) for g in s.split()]):
                return (QValidator.Acceptable, s, pos)
        return (QValidator.Intermediate, s, pos)

    def fixup(self, s):
        # Trim multiple spaces?
        pass

class QGlyphBox(QWidget):
    def __init__(self, parent, glyph):
        super().__init__()
        wlayout = QVBoxLayout()
        self.setLayout(wlayout)
        self.parent = parent
        self.glyph = glyph
        buf = Buffer(self.parent.project.font, glyphs = [glyph])
        renderer = QBufferRenderer(self.parent.project, buf)
        wlayout.addWidget(renderer)
        label = QLabel(glyph)
        label.setAlignment(Qt.AlignCenter)
        wlayout.addWidget(label)
        renderer.resizeEvent(None)
        # self.setContentsMargins(QMargins(25, 25, 25, 25))
        self.setMaximumSize(100,100)

    def mousePressEvent(self, e):
        if self.parent.selected:
            self.parent.selected.deselect()
        self.select()

    def deselect(self):
        self.setStyleSheet("")
        print("Deselect called")

    def select(self):
        self.setStyleSheet(selected_style)
        self.parent.selected = self

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return w

class QGlyphPicker(QDialog):
    def __init__(self, project):
        super(QGlyphPicker, self).__init__()
        self.project = project
        self.selected = None
        v_box_1 = QVBoxLayout()
        self.qgrid =  QFlowLayout()

        self.qgridWidget = QWidget()
        self.qgridWidget.setLayout(self.qgrid)

        self.scroll = QScrollArea()
        self.scroll.setWidget(self.qgridWidget)
        self.scroll.setWidgetResizable(True)

        v_box_1.addWidget(self.scroll)

        self.searchbar = QLineEdit()
        v_box_1.addWidget(self.searchbar)
        self.searchbar.textChanged.connect(self.filterGrid)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        v_box_1.addWidget(buttons)
        self.setLayout(v_box_1)
        self.widgets = {}
        self.setupGrid()
        self.drawGrid()

    def setupGrid(self):
        self.clearLayout(self.qgrid)
        for g in self.project.font.glyphs:
            w = QGlyphBox(self, g)
            self.widgets[g] = w

    def drawGrid(self):
        for g in self.project.font.glyphs:
            self.qgrid.addWidget(self.widgets[g])

    def filterGrid(self):
        t = self.searchbar.text()
        for g in self.project.font.glyphs:
            v = True
            if t and t not in g:
                v = False
            self.widgets[g].setVisible(v)

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    @classmethod
    def pickGlyph(self, project):
        dialog = QGlyphPicker(project)
        result = dialog.exec_()
        if dialog.selected:
            return dialog.selected.glyph

class MultiCompleter(QCompleter):

    def __init__(self, parent=None):
        super(MultiCompleter, self).__init__(parent)

        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setWrapAround(False)

    # Add texts instead of replace
    def pathFromIndex(self, index):
        path = QCompleter.pathFromIndex(self, index)

        lst = str(self.widget().text()).split(' ')

        if len(lst) > 1:
            path = '%s %s' % (' '.join(lst[:-1]), path)

        return path

    # Add operator to separate between texts
    def splitPath(self, path):
        path = str(path.split(' ')[-1]).lstrip(' ')
        return [path]

class QGlyphName(QWidget):
    changed = pyqtSignal()

    def __init__(self, project, multiple = False, allow_classes = False, parent=None):
        self.project = project
        self.multiple = multiple
        self.allow_classes = allow_classes
        super(QGlyphName, self).__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.glyphline = QLineEdit()
        if not hasattr(self.project, "completermodel"):
            self.project.completermodel = QStringListModel()
            self.project.completermodel.setStringList(self.project.font.glyphs)
        self.glyphline.setValidator(GlyphNameValidator(self))

        if multiple:
            self.completer = MultiCompleter()
        else:
            self.completer = QCompleter()
        self.completer.setModel(self.project.completermodel)
        self.glyphline.setCompleter(self.completer)
        self.glyphline.owner = self
        if self.allow_classes:
            self.setAcceptDrops(True)

        self.layout.addWidget(self.glyphline)

        self.glyphPickerButton = QPushButton("")
        self.glyphPickerButton.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        self.glyphPickerButton.clicked.connect(self.launchGlyphPicker)

        self.layout.addWidget(self.glyphPickerButton)

    def appendText(self, text):
        if self.glyphline.text():
            self.glyphline.setText(self.glyphline.text() + " " + text)
        else:
            self.glyphline.setText(text)

    def text(self):
        return self.glyphline.text()

    def setText(self, f):
        return self.glyphline.setText(f)

    def dropEvent(self, event):
        data = event.mimeData()
        if not data.hasText() or not data.text().startswith("@"):
            event.reject()
            return
        self.appendText(data.text())
        if not self.multiple:
            self.glyphline.returnPressed.emit()

    @property
    def returnPressed(self):
        return self.glyphline.returnPressed

    def launchGlyphPicker(self):
        result = QGlyphPicker.pickGlyph(self.project)
        if result:
            self.appendText(result)


if __name__ == "__main__":
    from Flux.project import FluxProject
    import sys

    app = 0
    if QApplication.instance():
        app = QApplication.instance()
    else:
        app = QApplication(sys.argv)

    w = QWidget()
    w.resize(510, 210)

    proj = FluxProject("qalam.fluxml")
    foo = QGlyphName(proj)
    foo.setParent(w)

    w.show()
    sys.exit(app.exec_())
