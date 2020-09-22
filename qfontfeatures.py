from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, \
    QSplitter, QVBoxLayout
from classlist import GlyphClassList


class QFontFeaturesPanel(QSplitter):
    def __init__(self, project):
        self.project = project
        super(QFontFeaturesPanel, self).__init__()
        self.setOrientation(Qt.Vertical)
        self.lookups = {}
        self.addWidget(self.make_class_list())
        self.addWidget(self.make_free_routine_list())
        # self.addWidget(self.make_feature_list())

    def make_class_list(self):
        return GlyphClassList(self.project)

    def make_free_routine_list(self):
        routine_list = QTreeWidget()
        routine_list.setHeaderLabels(["Routines"])
        for routine in self.project.fontfeatures.allRoutines():
            name = routine.name or "Anonymous routine"
            routine_item = QTreeWidgetItem([name])
            for rule in routine.rules:
                rule_item = QTreeWidgetItem([rule.asFea()])
                routine_item.addChild(rule_item)
            routine_list.addTopLevelItem(routine_item)
        return routine_list

    def make_feature_list(self):
        feature_list = QTreeWidget()
        feature_list.setHeaderLabels(["Features"])
        for feature, contents in self.project.features.items():
            feature_item = QTreeWidgetItem([feature])
            for routine in contents:
                name = routine.name or "<Routine>"
                routine_item = QTreeWidgetItem([name])
                for rule in routine.rules:
                    rule_item = QTreeWidgetItem([rule.asFea()])
                    routine_item.addChild(rule_item)
                feature_item.addChild(routine_item)
            feature_list.addTopLevelItem(feature_item)
        return feature_list
