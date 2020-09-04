from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, \
    QSplitter, QVBoxLayout


class QFontFeaturesPanel(QSplitter):
    def __init__(self, fea):
        self.fea = fea
        super(QFontFeaturesPanel, self).__init__()
        self.setOrientation(Qt.Vertical)
        self.lookups = {}
        self.addWidget(self.make_class_list())
        self.addWidget(self.make_free_routine_list())
        self.addWidget(self.make_feature_list())

    def make_class_list(self):
        glyph_class_list = QTreeWidget()
        glyph_class_list.setHeaderLabels(["Glyph Classes", "Contents"])
        for name,contents in self.fea.namedClasses.items():
            class_item = QTreeWidgetItem([name," ".join(contents)])
            glyph_class_list.addTopLevelItem(class_item)
        return glyph_class_list

    def make_free_routine_list(self):
        routine_list = QTreeWidget()
        routine_list.setHeaderLabels(["Routines"])
        for routine in self.fea.routines:
            name = routine.name or "Anonymous routine"
            routine_item = QTreeWidgetItem([name])
            for rule in routine.rules:
                if rule.address:
                    self.lookups[rule.address] = routine_item
                rule_item = QTreeWidgetItem([rule.asFea()])
                routine_item.addChild(rule_item)
            routine_list.addTopLevelItem(routine_item)
        return routine_list

    def make_feature_list(self):
        feature_list = QTreeWidget()
        feature_list.setHeaderLabels(["Features"])
        for feature, contents in self.fea.features.items():
            feature_item = QTreeWidgetItem([feature])
            for routine in contents:
                name = routine.name or "<Routine>"
                routine_item = QTreeWidgetItem([name])
                for rule in routine.rules:
                    if rule.address:
                        self.lookups[rule.address] = routine_item
                    rule_item = QTreeWidgetItem([rule.asFea()])
                    routine_item.addChild(rule_item)
                feature_item.addChild(routine_item)
            feature_list.addTopLevelItem(feature_item)
        return feature_list
