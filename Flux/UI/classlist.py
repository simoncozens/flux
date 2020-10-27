from PyQt5.QtCore import (
    Qt,
    pyqtSlot,
    QModelIndex,
    QAbstractTableModel,
    QItemSelectionModel,
    QMimeData,
    QRect
)
from PyQt5.QtWidgets import QTreeView, QMenu, QStyledItemDelegate, QLineEdit
from .glyphpredicateeditor import AutomatedGlyphClassDialog
from .qglyphname import QGlyphName

class GlyphNameDelegate(QStyledItemDelegate):
    def __init__(self, tree):
        super().__init__()
        self.project = tree.project
        self.model = tree.model()

    def createEditor(self, parent, option, index):
        # Check if index is actually non-computed class
        if self.model.isAutomatic(index):
            return super().createEditor(parent, option, index)
        editor = QGlyphName(self.project, multiple = True, allow_classes = True)
        editor.setParent(parent)
        editor.setAttribute(Qt.WA_TranslucentBackground, False)
        editor.setAttribute(Qt.WA_OpaquePaintEvent, True)
        editor.layout.setContentsMargins(0,0,0,0)
        # editor = QLineEdit(parent)
        return editor

    def updateEditorGeometry(self, editor, option, index):
        r = QRect(option.rect)
        if editor.windowFlags() & Qt.Popup and editor.parent() is not None:
            r.setTopLeft(editor.parent().mapToGlobal(r.topLeft()))
        sizeHint = editor.sizeHint()

        if (r.width()<sizeHint.width()): r.setWidth(sizeHint.width())
        if (r.height()<sizeHint.height()): r.setHeight(sizeHint.height())
        # Warning, this is gross.
        r.setTop(r.top() - 9)
        editor.setGeometry(r)
    def setEditorData(self, editor, index):
        editor.setText(index.data())

    def setModelData(self, editor, model, index):
        model.setData(index,editor.text())

class GlyphClassModel(QAbstractTableModel):
    def __init__(self, glyphclasses={}, parent=None):
        super(GlyphClassModel, self).__init__(parent)
        self.glyphclasses = glyphclasses
        self.order = list(sorted(self.glyphclasses.keys()))

    def rowCount(self, index=QModelIndex()):
        return len(self.order)

    def columnCount(self, index=QModelIndex()):
        return 2

    def isAutomatic(self, index):
        name = self.order[index.row()]
        return self.glyphclasses[name]["type"] == "automatic"

    def getPredicates(self, index):
        assert self.isAutomatic(index)
        name = self.order[index.row()]
        if "predicates" not in self.glyphclasses[name]:
            return []
        return self.glyphclasses[name]["predicates"]

    def setPredicates(self, index, predicates):
        name = self.order[index.row()]
        self.glyphclasses[name]["predicates"] = predicates

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
                return "<computed>"
        return None


    def mimeData(self, indexes):
        mimedata = QMimeData()
        name = self.order[indexes[0].row()]
        mimedata.setText("@"+name)
        return mimedata

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
            self.glyphclasses[""] = {"type": "manual", "contents": []}

        self.endInsertRows()
        return True

    def appendRow(self):
        self.insertRows(len(self.order))
        return self.index(len(self.order) - 1, 0)

    def removeRows(self, indexes):
        positions = [i.row() for i in indexes if i.column() == 0]
        print(positions)
        for i in reversed(sorted(positions)):
            self.removeRow(i)

        self.order = sorted(list(self.glyphclasses.keys()))
        print("Computing order", self.order)

    def removeRow(self, position, rows=1, index=QModelIndex()):
        """ Remove a row from the model. """
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        assert rows == 1
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
                del self.glyphclasses[name]
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
        flag = flag | Qt.ItemIsDragEnabled
        if index.column() == 0:
            return flag | Qt.ItemIsEditable

        name = self.order[index.row()]
        if self.glyphclasses[name]["type"] == "automatic":
            return flag
        else:
            return flag | Qt.ItemIsEditable


class GlyphClassList(QTreeView):
    def __init__(self, project):
        super(QTreeView, self).__init__()
        self.project = project
        self.setModel(GlyphClassModel(project.glyphclasses))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setItemDelegate(GlyphNameDelegate(self))
        self.setDragEnabled(True)
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
            predicates, result = AutomatedGlyphClassDialog.editDefinition(
                self.project, self.model().getPredicates(index)
            )
            if result:
                self.model().setPredicates(index, predicates)


    @pyqtSlot()
    def deleteClass(self):
        self.model().removeRows(self.selectedIndexes())

    @pyqtSlot()
    def addClass(self):
        index = self.model().appendRow()
        self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
        self.edit(index)

    @pyqtSlot()
    def addComputedClass(self):
        index = self.model().appendRow()
        self.model().glyphclasses[""] = {"type": "automatic"}
        self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
        self.edit(index)

