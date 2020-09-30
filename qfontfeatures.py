from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, \
    QSplitter, QVBoxLayout, QAbstractItemView
from classlist import GlyphClassList
from lookuplist import LookupList


class QFontFeaturesPanel(QSplitter):
    def __init__(self, project):
        self.project = project
        super(QFontFeaturesPanel, self).__init__()
        self.setOrientation(Qt.Vertical)
        self.lookups = {}
        self.addWidget(GlyphClassList(self.project))
        self.addWidget(LookupList(self.project))
        self.addWidget(self.make_feature_list())

    def make_feature_list(self):
        feature_list = QTreeWidget()
        feature_list.setDragEnabled(True)
        feature_list.setAcceptDrops(True)
        # feature_list.setDragDropMode(QAbstractItemView.InternalMove)
        feature_list.setHeaderLabels(["Features"])
        for feature, contents in self.project.fontfeatures.features.items():
            feature_item = QTreeWidgetItem([feature])
            for routine in contents:
                name = routine.name or "<Routine>"
                routine_item = QTreeWidgetItem([name])
                routine_item.setFlags(routine_item.flags() & ~Qt.ItemIsDropEnabled)
                # for rule in routine.rules:
                #     rule_item = QTreeWidgetItem([rule.asFea()])
                #     rule_item.setFlags(rule_item.flags() & ~Qt.ItemIsDropEnabled)
                #     rule_item.setFlags(rule_item.flags() & ~Qt.ItemIsDragEnabled)
                #     routine_item.addChild(rule_item)
                feature_item.addChild(routine_item)
            feature_list.addTopLevelItem(feature_item)
        return feature_list
