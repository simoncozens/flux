from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QTreeView,
    QMenu,
    QAbstractItemView,
)
from PyQt5.QtCore import QAbstractItemModel, QItemSelectionModel, QModelIndex, Qt, pyqtSlot, QByteArray, QDataStream, QIODevice, QMimeData, QVariant
from PyQt5.QtGui import QDrag
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
        self.setSelectionBehavior(self.SelectRows)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.doubleClicked.connect(self.doubleClickHandler)

    def highlight(self, feature, routine=None):
        self.collapseAll()
        featureRow = list(self.project.fontfeatures.features.keys()).index(feature)
        index = self.model().index(featureRow,0)
        if featureRow:
            self.scrollTo(self.model().index(featureRow+1,0))
            self.setCurrentIndex(index)
            self.setExpanded(index,True)
        if routine:
            routines = [x.name for x in self.project.fontfeatures.features[feature]]
            routineRow = routines.index(routine)
            index = self.model().index(routineRow,0,index)
            self.scrollTo(self.model().index(featureRow+1,0))
            self.setCurrentIndex(index)
            self.setExpanded(index,True)
        pass

    def update(self):
        self.model().beginResetModel()
        self.model().endResetModel()
        super().update()

    def decode_data(self, bytearray):

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
                item[Qt.ItemDataRole(key)] = value.value()

            data.append(item)

        return data

    def dropEvent(self, event):
        data = event.mimeData()
        if event.source() == self:
            print("Local")
            return super(QTreeView, self).dropEvent(event)
        print("Foreign")
        if data.hasFormat('application/x-qabstractitemmodeldatalist'):
            ba = data.data('application/x-qabstractitemmodeldatalist')
            data_items = self.decode_data(ba)
            routineName = data_items[0][0]
            routine = ([ x for x in self.project.fontfeatures.routines if x.name == routineName])[0]
            insertPos   = event.pos()
            destination = self.indexAt(event.pos())
            if self.model().indexIsFeature(destination):
                # Easy-peasy
                destFeature = list(self.project.fontfeatures.features.keys())[destination.row()]
                routineList = self.project.fontfeatures.features[destFeature]
                print(f"Dropping {routineName} to end of {destFeature}")
                self.model().beginInsertRows(destination, len(routineList), len(routineList)+1)
                self.setExpanded(destination, True)
                self.project.fontfeatures.features[destFeature].append(routine)
                self.model().endInsertRows()


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
        self.model().removeRows(self.selectedIndexes())

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
            return Qt.ItemIsEnabled | Qt.ItemIsDropEnabled
        flag = Qt.ItemFlags(QAbstractItemModel.flags(self, index))
        if self.indexIsFeature(index):
            flag = flag | Qt.ItemIsEditable | Qt.ItemIsDragEnabled
        return flag | Qt.ItemIsDragEnabled

    def insertRows(self, position, item=None, rows=1, index=QModelIndex()):
        """ Insert a row into the model. """
        if isinstance(rows, QModelIndex):
            print(position, item, rows, index)
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
        print("Remove row called", index)
        """ Remove a row from the model. """
        self.beginRemoveRows(self.parent(index), index.row(), index.row())
        if self.indexIsFeature(index):
            key = list(self.project.fontfeatures.features.keys())[index.row()]
            del self.project.fontfeatures.features[key]
        else:
            routineList = self.parent(index).internalPointer()
            del routineList[index.row()]
        self.endRemoveRows()
        return True

    def addRule(self, ix, rule):
        # lookup = ix.internalPointer()
        # self.beginInsertRows(ix, ix.row(), ix.row())
        # lookup.rules.append(rule)
        # self.endInsertRows()
        return True

    def supportedDropActions(self):
        return Qt.MoveAction | Qt.CopyAction

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

