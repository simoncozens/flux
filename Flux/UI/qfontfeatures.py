from PyQt5.QtCore import Qt, QDataStream, QMimeData, QVariant
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, \
    QSplitter, QVBoxLayout, QAbstractItemView, QMenu
from .classlist import GlyphClassList
from .lookuplist import LookupList


class QFeatureList(QTreeWidget):
    def __init__(self, editor, features):
        super(QTreeWidget, self).__init__()
        self.editor = editor
        self.features = features
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setHeaderLabels(["Features"])
        self.rebuild()

    def rebuild(self):
        self.clear()
        for feature, contents in self.features.items():
            feature_item = QTreeWidgetItem([feature])
            feature_item.setFlags(feature_item.flags() | Qt.ItemIsEditable)
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
            self.addTopLevelItem(feature_item)

    def contextMenu(self, position):
        indexes = self.selectedIndexes()
        menu = QMenu()
        menu.addAction("Add feature", self.addFeature)
        menu.exec_(self.viewport().mapToGlobal(position))

    def addFeature(self):
        feature_item = QTreeWidgetItem(["new feature"])
        feature_item.setFlags(feature_item.flags() | Qt.ItemIsEditable)
        self.addTopLevelItem(feature_item)
        self.features.append("new feature")

    def dragEnterEvent(self, event):
        # if (event.mimeData().hasFormat('application/x-routine')):
            # print("Accepting")
        event.accept()
        # else:
            # print("Ignoring")
            # event.ignore()

    def dropEvent(self, event):
        destination = self.indexAt(event.pos())
        ba = event.mimeData().data('application/x-qabstractitemmodeldatalist')
        data_items = self.decodeData(ba)
        print(data_items)
        lookupname = data_items[0][Qt.DisplayRole].value()
        r = [lu for lu in self.editor.project.fontfeatures.routines if lu.name == lookupname]
        if not r:
            return
        if self.model().parent(destination).isValid():
            parent_destination = self.model().parent(destination)
        else:
            key = list(self.features.items())[destination.row()][0]
            print(key)
            self.features[key].append(r[0])
            print(self.features[key])
            self.rebuild()
            self.editor.update()


        event.acceptProposedAction()

    def decodeData(self, bytearray):
        data = []
        item = {}
        ds = QDataStream(bytearray)
        while not ds.atEnd():
            row = ds.readInt32()
            column = ds.readInt32()
            map_items = ds.readInt32()
            for i in range(map_items):
                key = ds.readInt32()
                value = QVariant()
                ds >> value
                item[Qt.ItemDataRole(key)] = value
            data.append(item)
        return data

class QFontFeaturesPanel(QSplitter):
    def __init__(self, project, editor):
        self.project = project
        self.editor = editor
        super(QFontFeaturesPanel, self).__init__()
        self.setOrientation(Qt.Vertical)
        self.lookups = {}
        self.addWidget(GlyphClassList(self.project))
        self.addWidget(LookupList(self.project, self))
        self.addWidget(QFeatureList(self.editor, self.project.fontfeatures.features))

    def update(self):
        for i in range(0,self.count()):
            self.widget(i).update()
        super().update()
