from PyQt5.QtCore import Qt, QDataStream, QMimeData, QVariant
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, \
    QSplitter, QVBoxLayout, QAbstractItemView, QMenu
from .classlist import GlyphClassList
from .lookuplist import LookupList
from .featurelist import FeatureList


class QFontFeaturesPanel(QSplitter):
    def __init__(self, project, editor):
        self.project = project
        self.editor = editor
        super(QFontFeaturesPanel, self).__init__()
        self.setOrientation(Qt.Vertical)
        self.addWidget(GlyphClassList(self.project))
        self.lookuplist = LookupList(self.project, self)
        self.addWidget(self.lookuplist)
        self.featurelist = FeatureList(self.project, self)
        self.addWidget(self.featurelist)

    def update(self):
        for i in range(0,self.count()):
            self.widget(i).update()
        super().update()
