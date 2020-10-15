from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QTreeView,
    QMenu,
    QAbstractItemView,
)
from PyQt5.QtCore import (
    QAbstractItemModel,
    QItemSelectionModel,
    QModelIndex,
    Qt,
    pyqtSlot,
    QByteArray,
    QDataStream,
    QIODevice,
    QMimeData,
    QVariant,
)
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
        index = self.model().index(featureRow, 0)
        if featureRow:
            self.scrollTo(self.model().index(featureRow + 1, 0))
            self.setCurrentIndex(index)
            self.setExpanded(index, True)
        if routine:
            routines = [x.name for x in self.project.fontfeatures.features[feature]]
            routineRow = routines.index(routine)
            index = self.model().index(routineRow, 0, index)
            self.scrollTo(self.model().index(featureRow + 1, 0))
            self.setCurrentIndex(index)
            self.setExpanded(index, True)
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
            event.setDropAction(Qt.MoveAction)

            return super(QTreeView, self).dropEvent(event)
        print("Foreign")
        if data.hasFormat("application/x-qabstractitemmodeldatalist"):
            ba = data.data("application/x-qabstractitemmodeldatalist")
            data_items = self.decode_data(ba)
            routineName = data_items[0][0]
            routine = self.model().routineCalled(routineName)
            insertPos = event.pos()
            destination = self.indexAt(event.pos())
            if self.model().indexIsFeature(destination):
                # Easy-peasy
                destFeature = list(self.project.fontfeatures.features.keys())[
                    destination.row()
                ]
                routineList = self.project.fontfeatures.features[destFeature]
                print(f"Dropping {routineName} to end of {destFeature}")
                self.project.fontfeatures.features[destFeature].append(routine)
                self.update()
                self.setExpanded(destination, True)
            elif self.model().indexIsRoutine(destination):
                destParent = self.model().parent(destination)
                print(
                    "Parent destination for this drop is: ",
                    destParent.row(),
                    destParent.column(),
                    destParent.internalPointer(),
                )
                print("Destination inside parent is ", destination.row())
                self.model().insertRows(destination.row(), 1, destParent)
                self.model().setData(destination, routineName)
            else:
                event.reject()
                return
            event.accept()

    def contextMenu(self, position):
        indexes = self.selectedIndexes()
        menu = QMenu()
        menu.addAction("Add feature", self.addFeature)
        if len(indexes) > 0:
            if self.model().indexIsRoutine(indexes[0]):
                menu.addAction("Delete routine", self.deleteItem)
            else:
                menu.addAction("Delete feature", self.deleteItem)
        menu.exec_(self.viewport().mapToGlobal(position))

    def doubleClickHandler(self, index):
        pass

    @pyqtSlot()
    def addFeature(self):
        index = self.model().appendRow()
        self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
        self.edit(index)

    @pyqtSlot()
    def deleteItem(self):
        # Check if routine is in use
        self.model().removeRowWithIndex(self.selectedIndexes()[0])

    @pyqtSlot()
    def deleteRoutine(self):
        # Check if routine is in use
        self.model().removeRowWithIndex(self.selectedIndexes()[0])


class FeatureListModel(QAbstractItemModel):
    def __init__(self, proj, parent=None):
        super(FeatureListModel, self).__init__(parent)
        self.project = proj
        self.rootIndex = QModelIndex()
        self.retained_objects = {}

    # Horrific hack to avoid GC bug
    def makeSingleton(self, row):
        if not row in self.retained_objects:
            self.retained_objects[row] = {"row": row}
        return self.retained_objects[row]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        return "Features"

    def rowCount(self, index=QModelIndex()):
        # print("Getting row count at index ", self.describeIndex(index))
        if index.row() == -1:
            return len(self.project.fontfeatures.features.keys())
        if index.isValid():
            item = index.internalPointer()
            if isinstance(item, list):
                return len(item)
        return 0

    def getFeatureNameAtRow(self, row):
        keys = list(self.project.fontfeatures.features.keys())
        return keys[row]

    def getRoutinesAtRow(self, row):
        values = list(self.project.fontfeatures.features.values())
        return values[row]

    def columnCount(self, index=QModelIndex()):
        return 1

    def describeIndex(self, index):
        if not index.isValid():
            return "root of tree"
        if self.indexIsFeature(index):
            frow = index.row()
            return f"feature at row {frow}"
        else:
            parentrow = index.internalPointer()["row"]
            return f"Item {index.row()} of feature at row {parentrow}"

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        if isinstance(index.internalPointer(), list):
            return QModelIndex()
        else:
            row = index.internalPointer()["row"]
            return self.index(row, 0)
        return index.internalPointer()

    def index(self, row, column, parent=QModelIndex()):
        """ Returns the index of the item in the model specified by the given row, column and parent index """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            ix = self.createIndex(row, column, self.getRoutinesAtRow(row))
        else:
            ix = self.createIndex(row, column, self.makeSingleton(parent.row()))
        return ix

    def change_key(self, old, new):
        for _ in range(len(self.project.fontfeatures.features)):
            k, v = self.project.fontfeatures.features.popitem(False)
            self.project.fontfeatures.features[new if old == k else k] = v

    def setData(self, index, value, role=Qt.EditRole):
        print("Set data called", index, index.row(), index.column())
        print(
            "Parent ",
            self.parent(index),
            self.parent(index).row(),
            self.parent(index).column(),
        )
        print("Role was", role)
        print("Index was " + self.describeIndex(index))
        print("Value was ", value)
        print("Internal pointer", index.internalPointer())
        if self.indexIsFeature(index):
            print("Renaming a feature", index.internalPointer())
            self.dataChanged.emit(index, index)
            self.change_key(
                list(self.project.fontfeatures.features.keys())[index.row()], value
            )
            return True
        else:
            routines = self.getRoutinesAtRow(index.internalPointer()["row"])
            print(
                "Internal pointer of parent before set",
                self.parent(index).internalPointer(),
            )
            print(
                "Setting routine",
                index.row(),
                index.column(),
                routines,
                self.parent(index),
            )
            routines[index.row()] = self.routineCalled(value)
            self.dataChanged.emit(index, index)
            print(
                "Internal pointer of parent now", self.parent(index).internalPointer()
            )
        return True

    def routineCalled(self, value):
        return ([x for x in self.project.fontfeatures.routines if x.name == value])[0]

    def indexIsRoutine(self, index):
        return index.isValid() and isinstance(index.internalPointer(), dict)

    def getRoutine(self, index):
        routines = self.getRoutinesAtRow(index.internalPointer()["row"])
        return routines[index.row()]

    def indexIsFeature(self, index):
        return index.isValid() and isinstance(index.internalPointer(), list)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if self.indexIsFeature(index):
                return self.getFeatureNameAtRow(index.row())
            else:
                routine = self.getRoutine(index)
                if routine:
                    return routine.name
                else:
                    return "<No Routine>"
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        flag = Qt.ItemFlags(QAbstractItemModel.flags(self, index))
        if self.indexIsFeature(index):
            flag = (
                flag | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
            )
        return flag | Qt.ItemIsDragEnabled

    def insertRows(self, row, count, parent=QModelIndex()):
        """ Insert a row into the model. """
        print("Inserting a row at row ", row)
        print("Parent= ", self.describeIndex(parent))
        self.beginInsertRows(parent, row, row + count)
        if not parent.isValid():
            self.project.fontfeatures.features["<New Feature>"] = []
        else:
            parent.internalPointer().insert(row, None)
            print("Internal pointer of parent is now", parent.internalPointer())
        self.endInsertRows()
        return True

    def appendRow(self):
        self.insertRows(len(self.project.fontfeatures.features.keys()), 1)
        return self.index(len(self.project.fontfeatures.features.keys()) - 1, 0)

    def removeRows(self, row, count, parent):
        assert count == 1
        index = self.index(row, 0, parent)
        return self.removeRowWithIndex(index)

    def removeRowWithIndex(self, index):
        print("Remove row called", index)
        self.beginRemoveRows(self.parent(index), index.row(), index.row())
        if self.indexIsFeature(index):
            key = list(self.project.fontfeatures.features.keys())[index.row()]
            del self.project.fontfeatures.features[key]
        else:
            routineList = self.getRoutinesAtRow(index.internalPointer()["row"])
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
        return Qt.MoveAction  # | Qt.CopyAction


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
