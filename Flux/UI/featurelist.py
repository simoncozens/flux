from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QTreeView,
    QMenu,
    QAbstractItemView
)
from PyQt5.QtCore import QAbstractItemModel, QItemSelectionModel, QModelIndex, Qt, pyqtSlot
import sys
from fontFeatures import Routine
from Flux.project import FluxProject

class FeatureList(QTreeView):
    def __init__(self, project, parent):
        super(QTreeView, self).__init__()
        self.project = project
        self.parent = parent
        self.setModel(FeatureListModel(project))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.doubleClicked.connect(self.doubleClickHandler)

    def update(self):
        self.model().beginResetModel()
        self.model().endResetModel()
        super().update()

    def startDrag(self, dropActions):
        super(QTreeView, self).startDrag(dropActions)

    def contextMenu(self, position):
        indexes = self.selectedIndexes()
        menu = QMenu()
        menu.addAction("Add feature", self.addFeature)
        if len(indexes) > 0:
            if isinstance(indexes[0].internalPointer(), Routine):
                menu.addAction("Delete routine", self.deleteRoutine)
            else:
                menu.addAction("Delete feature", self.deleteItem)
        menu.exec_(self.viewport().mapToGlobal(position))

    def doubleClickHandler(self, index):
        pass

    @pyqtSlot()
    def addFeature(self):
        index = self.model().appendRow()
        self.selectionModel().select(
            index,
            QItemSelectionModel.ClearAndSelect
        )
        self.edit(index)

    @pyqtSlot()
    def deleteItem(self):
        # Check if routine is in use
        self.model().removeRows(self.selectedIndexes())

    @pyqtSlot()
    def deleteRoutine(self):
        # Check if routine is in use
        self.model().removeRoutine(self.selectedIndexes())

class FeatureListModel(QAbstractItemModel):
    def __init__(self, proj, parent = None):
        super(FeatureListModel, self).__init__(parent)
        self.project = proj

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        return "Features"

    def rowCount(self, index=QModelIndex()):
        if index.row() == -1:
            return len(self.project.fontfeatures.features.keys())
        if index.isValid():
            item = index.internalPointer()
            if isinstance(item, list):
                return len(item)
        return 0

    def columnCount(self, index=QModelIndex()):
        return 1

    def parent(self, index):
        if isinstance(index.internalPointer(), list):
            return QModelIndex()
        rule = index.internalPointer()
        # Now go find it
        for row, key in enumerate(self.project.fontfeatures.features.keys()):
            if rule in self.project.fontfeatures.features[key]:
                return self.createIndex(row, 0, self.project.fontfeatures.features[key])
        return QModelIndex()

    def index(self, row, column, index=QModelIndex()):
        """ Returns the index of the item in the model specified by the given row, column and parent index """

        if not self.hasIndex(row, column, index):
            return QModelIndex()
        # print(row, column, index.internalPointer())
        if not index.isValid():
            ix = self.createIndex(row, column, list(self.project.fontfeatures.features.values())[row])
        else:
            item = index.internalPointer()
            ix = self.createIndex(row, column, item[row])
        return ix

    def change_key(self, old, new):
        for _ in range(len(self.project.fontfeatures.features)):
            k, v = self.project.fontfeatures.features.popitem(False)
            self.project.fontfeatures.features[new if old == k else k] = v

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        self.change_key(list(self.project.fontfeatures.features.keys())[index.row()], value)
        return True

    def indexIsRoutine(self, index):
        item = index.internalPointer()
        return isinstance(item, Routine)

    def indexIsFeature(self, index):
        item = index.internalPointer()
        return not isinstance(item, Routine)

    def data(self, index, role=Qt.DisplayRole):
        # print("Getting index ", index.row(), index.column(), index.internalPointer())
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            item = index.internalPointer()
            if self.indexIsFeature(index):
                return list(self.project.fontfeatures.features.keys())[index.row()]
            else:
                return item.name
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        flag = Qt.ItemFlags(QAbstractItemModel.flags(self, index))
        if self.indexIsFeature(index):
            flag = flag | Qt.ItemIsEditable | Qt.ItemIsDragEnabled
        return flag | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    def insertRows(self, position, item=None, rows=1, index=QModelIndex()):
        """ Insert a row into the model. """
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)
        self.project.fontfeatures.features["<New Feature>"] = []
        self.endInsertRows()
        return True

    def appendRow(self):
        self.insertRows(len(self.project.fontfeatures.features.keys()))
        return self.index(len(self.project.fontfeatures.features.keys())-1, 0)

    def removeRows(self, indexes):
        for i in indexes:
            self.removeRow(i)

    def removeRow(self, index):
        print("Remove row called")
        """ Remove a row from the model. """
        self.beginRemoveRows(self.parent(index), index.row(), index.row())
        # if self.indexIsFeature(index):
        #     del self.lookups[index.row()]
        # else:
        #     lookup = self.parent(index).internalPointer()
        #     del lookup.rules[index.row()]
        self.endRemoveRows()
        return True

    def addRule(self, ix, rule):
        # lookup = ix.internalPointer()
        # self.beginInsertRows(ix, ix.row(), ix.row())
        # lookup.rules.append(rule)
        # self.endInsertRows()
        return True

if __name__ == "__main__":
    app = 0
    if QApplication.instance():
        app = QApplication.instance()
    else:
        app = QApplication(sys.argv)

    w = QWidget()
    w.resize(510, 210)
    v_box_1 = QVBoxLayout()

    proj = FluxProject("qalam.fluxml")
    tree = FeatureList(proj, None)
    v_box_1.addWidget(tree)

    w.setLayout(v_box_1)

    w.show()
    sys.exit(app.exec_())

