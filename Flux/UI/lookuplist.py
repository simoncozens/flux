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
from fontFeatures import Routine, Attachment, Substitution, Positioning, Chaining, ValueRecord
from Flux.project import FluxProject

class LookupList(QTreeView):
    def __init__(self, project, parent):
        super(QTreeView, self).__init__()
        self.project = project
        self.parent = parent
        self.setModel(LookupListModel(project))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.doubleClicked.connect(self.doubleClickHandler)

    def update(self):
        print(self.project.fontfeatures.routines)
        self.model().beginResetModel()
        self.model().endResetModel()
        super().update()

    def startDrag(self, dropActions):
        item = self.selectedIndexes()[0].internalPointer()
        if not isinstance(item, Routine):
            return
        super(QTreeView, self).startDrag(dropActions)

    def contextMenu(self, position):
        indexes = self.selectedIndexes()
        menu = QMenu()
        menu.addAction("Add routine", self.addRoutine)
        if len(indexes) > 0:
            if isinstance(indexes[0].internalPointer(), Routine):
                menu.addAction("Delete routine", self.deleteItem)
                menu.addAction("Add substitution rule", self.addSubRule)
                menu.addAction("Add positioning rule", self.addPosRule)
                # menu.addAction("Add attachment rule", self.addAttRule)
                menu.addAction("Add chaining rule", self.addChainRule)
            else:
                menu.addAction("Delete rule", self.deleteItem)
        menu.exec_(self.viewport().mapToGlobal(position))

    @pyqtSlot()
    def addSubRule(self):
        self.model().addRule(self.selectedIndexes()[0], Substitution([[]],[[]]))

    @pyqtSlot()
    def addPosRule(self):
        self.model().addRule(self.selectedIndexes()[0], Positioning([[]],[ValueRecord()]))

    @pyqtSlot()
    def addChainRule(self):
        self.model().addRule(self.selectedIndexes()[0], Chaining([[]],lookups= [[]]))

    def doubleClickHandler(self, index):
        if isinstance(index.internalPointer(), Routine):
            return
        if isinstance(index.internalPointer(), Attachment):
            # XXX
            pass
        self.parent.editor.showRuleEditor(index.internalPointer())

    @pyqtSlot()
    def addRoutine(self):
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

class LookupListModel(QAbstractItemModel):
    def __init__(self, proj, parent = None):
        super(LookupListModel, self).__init__(parent)
        self.project = proj
        self.lookups = proj.fontfeatures.routines

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        return "Lookups"

    def rowCount(self, index=QModelIndex()):
        if index.row() == -1:
            return len(self.lookups)
        if index.isValid():
            item = index.internalPointer()
            if isinstance(item, Routine):
                return len(item.rules)
        return 0

    def columnCount(self, index=QModelIndex()):
        return 1

    def parent(self, index):
        if isinstance(index.internalPointer(), Routine):
            return QModelIndex()
        rule = index.internalPointer()
        # Now go find it
        for row, routine in enumerate(self.lookups):
            if rule in routine.rules:
                return self.createIndex(row, 0, routine)
        return QModelIndex()

    def index(self, row, column, index=QModelIndex()):
        """ Returns the index of the item in the model specified by the given row, column and parent index """

        if not self.hasIndex(row, column, index):
            return QModelIndex()
        # print(row, column, index.internalPointer())
        if not index.isValid():
            ix = self.createIndex(row, column, self.lookups[row])
        else:
            item = index.internalPointer()
            ix = self.createIndex(row, column, item.rules[row])
        return ix

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False

        if index.isValid() and 0 <= index.row() < len(self.lookups):
            self.lookups[index.row()].name = value
            # self.dataChanged.emit(index, index)
            return True

        return False

    def indexIsRoutine(self, index):
        item = index.internalPointer()
        return isinstance(item, Routine)

    def indexIsRule(self, index):
        item = index.internalPointer()
        return not isinstance(item, Routine)

    def data(self, index, role=Qt.DisplayRole):
        # print("Getting index ", index.row(), index.column(), index.internalPointer())
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            item = index.internalPointer()
            if self.indexIsRoutine(index):
                return item.name
            else:
                fea = item.asFea() or "<New %s Rule>" % item.__class__.__name__
                return fea.split("\n")[0]
        return None

    def flags(self, index):
        """ Set the item flags at the given index. Seems like we're
            implementing this function just to see how it's done, as we
            manually adjust each tableView to have NoEditTriggers.
        """
        if not index.isValid():
            return Qt.ItemIsEnabled
        flag = Qt.ItemFlags(QAbstractItemModel.flags(self, index))
        if self.indexIsRoutine(index):
            return flag | Qt.ItemIsEditable | Qt.ItemIsDragEnabled
        return flag | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    def insertRows(self, position, item=None, rows=1, index=QModelIndex()):
        """ Insert a row into the model. """
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)

        self.lookups.append(Routine(name="",rules=[]))
        self.endInsertRows()
        return True

    def appendRow(self):
        self.insertRows(len(self.lookups))
        return self.index(len(self.lookups)-1, 0)

    def removeRows(self, indexes):
        for i in indexes:
            self.removeRow(i)

    def removeRow(self, index):
        """ Remove a row from the model. """
        self.beginRemoveRows(self.parent(index), index.row(), index.row())
        if self.indexIsRoutine(index):
            del self.lookups[index.row()]
        else:
            lookup = self.parent(index).internalPointer()
            del lookup.rules[index.row()]
        self.endRemoveRows()
        return True

    def addRule(self, ix, rule):
        lookup = ix.internalPointer()
        self.beginInsertRows(ix, ix.row(), ix.row())
        lookup.rules.append(rule)
        self.endInsertRows()
        return True

if __name__ == "__main__":
    from fluxproject import FluxProject

    app = 0
    if QApplication.instance():
        app = QApplication.instance()
    else:
        app = QApplication(sys.argv)

    w = QWidget()
    w.resize(510, 210)
    v_box_1 = QVBoxLayout()

    proj = FluxProject("qalam.fluxml")

    tree = LookupList(proj)
    v_box_1.addWidget(tree)

    w.setLayout(v_box_1)

    w.show()
    sys.exit(app.exec_())

