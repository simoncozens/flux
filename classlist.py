from PyQt5.QtCore import Qt, pyqtSlot, QModelIndex, QAbstractTableModel, QItemSelectionModel
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QTreeView, QMenu
import qtawesome as qta
from glyphpredicateeditor import AutomatedGlyphClassDialog

initialClasses = {
    "above_nuktas": { "type": "manual", "contents": ["sda","dda","tda"]},
    "below_nuktas": { "type": "manual", "contents": ["sdb","ddb","tdb"]},
    "all_nuktas": { "type": "automatic" },
    "above_other_marks": { "type": "manual", "contents": ["toeda","MADDA","DAMMA"]},
    "all_above_marks": { "type": "automatic" },
}

class GlyphClassModel(QAbstractTableModel):
    def __init__(self, glyphclasses = {}, parent = None):
        super(GlyphClassModel, self).__init__(parent)
        self.glyphclasses = glyphclasses
        self.order = list(sorted(self.glyphclasses.keys()))

    def rowCount(self, index=QModelIndex()):
        return len(self.order)

    def columnCount(self, index=QModelIndex()):
        return 2

    def isAutomatic(self, index):
        name = self.order[index.row()]
        return self.glyphclasses[name]["type"]=="automatic"

    def getPredicates(self, index):
        assert(self.isAutomatic(index))
        name = self.order[index.row()]
        if "predicates" not in self.glyphclasses[name]:
            return []
        return self.glyphclasses[name]["predicates"]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if not 0 <= index.row() < len(self.order):
            return None

        name = self.order[index.row()]
        if not name in self.glyphclasses:
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == 0:
                return name
            elif index.column() == 1 and not self.isAutomatic(index):
                return " ".join(self.glyphclasses[name]["contents"])
        if role == Qt.DecorationRole:
            if index.column() == 1 and self.isAutomatic(index):
                return qta.icon('fa5s.cog')
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """ Set the headers to be displayed. """
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == 0:
                return "Name"
            elif section == 1:
                return "Contents"
        return None

    def insertRows(self, position, item=None, rows=1, index=QModelIndex()):
        """ Insert a row into the model. """
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)

        if "" not in self.order:
            self.order.append("")
            self.glyphclasses[""] = { "type": "manual", "contents" : []}

        self.endInsertRows()
        return True

    def appendRow(self):
        self.insertRows(len(self.order))
        return self.index(len(self.order)-1, 0)

    def removeRows(self, indexes):
        positions = [ i.row() for i in indexes if i.column() == 0 ]
        print(positions)
        for i in reversed(sorted(positions)):
            self.removeRow(i)

        self.order = sorted(list(self.glyphclasses.keys()))
        print("Computing order", self.order)

    def removeRow(self, position, rows=1, index=QModelIndex()):
        """ Remove a row from the model. """
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        assert(rows == 1)
        del self.glyphclasses[self.order[position]]
        print("Deleting %s" % self.order[position])
        self.endRemoveRows()
        return True

    def setData(self, index, value, role=Qt.EditRole):
        """ Adjust the data (set it to <value>) depending on the given 
            index and role. 
        """
        if role != Qt.EditRole:
            return False

        if index.isValid() and 0 <= index.row() < len(self.order):
            name = self.order[index.row()]
            if index.column() == 0 and name != value:
                self.glyphclasses[value] = self.glyphclasses[name]
                del(self.glyphclasses[name])
            elif index.column() == 1:
                self.glyphclasses[name]["contents"] = value.split(" ")
            else:
                return False

            self.order = sorted(list(self.glyphclasses.keys()))
            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index):
        """ Set the item flags at the given index. Seems like we're 
            implementing this function just to see how it's done, as we 
            manually adjust each tableView to have NoEditTriggers.
        """
        if not index.isValid():
            return Qt.ItemIsEnabled
        flag = Qt.ItemFlags(QAbstractTableModel.flags(self, index))
        if index.column() == 0:
            return flag | Qt.ItemIsEditable

        name = self.order[index.row()]
        if self.glyphclasses[name]["type"] == "automatic":
            return flag
        else:
            return flag | Qt.ItemIsEditable

class GlyphClassList(QTreeView):
    # def __init__(self, fontinfomodel):
    def __init__(self, font):
        super(QTreeView, self).__init__()
        self.font = font
        self.setModel(GlyphClassModel(initialClasses))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.doubleClicked.connect(self.doubleClickHandler)

    def contextMenu(self, position):
        indexes = self.selectedIndexes()
        menu = QMenu()
        if len(indexes) > 0:
            menu.addAction("Delete class", self.deleteClass)
        menu.addAction("Add class", self.addClass)
        menu.addAction("Add computed class", self.addComputedClass)
        menu.exec_(self.viewport().mapToGlobal(position))

    def doubleClickHandler(self, index):
        if self.model().isAutomatic(index) and index.column() == 1:
            AutomatedGlyphClassDialog.editDefinition(self.font,self.model().getPredicates(index))

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
        pass
