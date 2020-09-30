from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QHBoxLayout,
    QVBoxLayout,
    QTreeView,
    QMenu,
    QAbstractItemView
)
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QAbstractItemModel, pyqtSlot
from PyQt5.QtGui import QStandardItemModel
import sys
from fontFeatures import Routine, Attachment
from fluxproject import FluxProject

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

    def contextMenu(self, position):
        indexes = self.selectedIndexes()
        menu = QMenu()
        if len(indexes) == 0:
            menu.addAction("Add routine", self.deleteClass)
        if isinstance(indexes[0].internalPointer(), Routine):
            menu.addAction("Delete routine", self.deleteClass)
            menu.addAction("Add substitution rule", self.addClass)
            menu.addAction("Add positioning rule", self.addClass)
            menu.addAction("Add attachment rule", self.addClass)
            menu.addAction("Add chaining rule", self.addClass)
        else:
            menu.addAction("Delete rule", self.deleteClass)
        menu.exec_(self.viewport().mapToGlobal(position))

    def doubleClickHandler(self, index):
        if isinstance(index.internalPointer(), Routine):
            pass
        if isinstance(index.internalPointer(), Attachment):
            # XXX
            pass
        self.parent.editor.showRuleEditor(index.internalPointer())

    @pyqtSlot()
    def deleteClass(self):
        self.model().removeRows(self.selectedIndexes())

    @pyqtSlot()
    def addClass(self):
        index = self.model().appendRow()
        self.selectionModel().select(
            index,
            QItemSelectionModel.ClearAndSelect)

    @pyqtSlot()
    def addComputedClass(self):
        index = self.model().appendRow()
        pass

class LookupListModel(QAbstractItemModel):
    def __init__(self, proj, parent = None):
        super(LookupListModel, self).__init__(parent)
        self.project = proj
        self.lookups = proj.fontfeatures.routines

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

    def data(self, index, role=Qt.DisplayRole):
        # print("Getting index ", index.row(), index.column(), index.internalPointer())
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            item = index.internalPointer()
            if isinstance(item, Routine):
                return item.name
            else:
                fea = item.asFea()
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
        if isinstance(index.internalPointer(), Routine):
            return flag | Qt.ItemIsEditable | Qt.ItemIsDragEnabled
        return flag | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled


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

