from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QTreeView,
    QMenu,
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox
)
from PyQt5.QtCore import (
    QAbstractItemModel,
    QItemSelectionModel,
    QModelIndex,
    Qt,
    pyqtSlot,
    QMimeData
)
from PyQt5.QtGui import QValidator
import sys
from fontFeatures import (
    Routine,
    Attachment,
    Substitution,
    Positioning,
    Chaining,
    ValueRecord,
    Rule
)
from Flux.project import FluxProject
import re
from Flux.ThirdParty.HTMLDelegate import HTMLDelegate
from Flux.computedroutine import ComputedRoutine
from Flux.dividerroutine import DividerRoutine


class FeatureValidator(QValidator):
    def validate(self, s, pos):
        if re.search(r"[^a-z0-9]", s) or len(s) > 4:
            return (QValidator.Invalid, s, pos)
        if len(s) < 4:
            return (QValidator.Intermediate, s, pos)
        return (QValidator.Acceptable, s, pos)


class LookupFlagEditor(QDialog):

    simpleChecks = [
        (0x02, "Ignore Base Glyphs"),
        (0x08, "Ignore Mark Glyphs"),
        (0x04, "Ignore Ligatures"),
        (0x01, "Cursive last glyph on baseline"),
    ]

    def __init__(self, routine):
        super(QDialog, self).__init__()
        self.checkboxes = []
        self.routine = routine
        self.flags = routine.flags
        layout = QVBoxLayout()
        for flagbit, description in self.simpleChecks:
            cb = QCheckBox(description)
            cb.flagbit = flagbit
            cb.stateChanged.connect(self.toggleBit)
            if routine.flags & flagbit:
                cb.setCheckState(Qt.Checked)
            layout.addWidget(cb)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    @pyqtSlot()
    def toggleBit(self):
        cb = self.sender()
        self.flags = self.flags ^ cb.flagbit

    def accept(self):
        self.routine.flags = self.flags
        super().accept()


class AddToFeatureDialog(QDialog):
    def __init__(self):
        super(QDialog, self).__init__()
        self.featureEdit = QLineEdit()
        self.featureEdit.setValidator(FeatureValidator())
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Add this routine to feature..."))
        layout.addWidget(self.featureEdit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def accept(self):
        if not self.featureEdit.hasAcceptableInput():
            return
        self.feature = self.featureEdit.text()
        return super().accept()


class LookupList(QTreeView):
    def __init__(self, project, parent):
        super(QTreeView, self).__init__()
        self.project = project
        self.parent = parent
        self.setModel(LookupListModel(project, parent=self))
        self.setItemDelegate(HTMLDelegate())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.TargetMoveAction)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragDropOverwriteMode(False)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.doubleClicked.connect(self.doubleClickHandler)

    def highlight(self, routineName):
        routineNames = [x.name for x in self.project.fontfeatures.routines]
        if not routineName in routineNames:
            return
        self.collapseAll()
        routineRow = routineNames.index(routineName)
        if routineRow:
            self.scrollTo(self.model().index(routineRow + 1, 0))
            self.setCurrentIndex(self.model().index(routineRow, 0))
            self.setExpanded(self.model().index(routineRow, 0), True)
        pass

    def update(self, index=QModelIndex()):
        if index.isValid():
            self.model().dataChanged.emit(index, index)
        else:
            self.model().beginResetModel()
            self.model().dataChanged.emit(index, index)
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
        if indexes:
            thing = indexes[0].internalPointer()
            if isinstance(thing, Rule) and hasattr(thing, "computed"):
                pass
            elif isinstance(thing, Routine):
                menu.addAction("Delete routine", self.deleteItem)
                menu.addAction("Add to feature...", self.addToFeature)
                menu.addAction("Add separator", self.addSeparatorRoutine)
                if isinstance(thing, ComputedRoutine):
                    menu.addAction("Reify", self.reify)
                else:
                    menu.addAction("Add substitution rule", self.addSubRule)
                    menu.addAction("Add positioning rule", self.addPosRule)
                    menu.addAction("Add attachment rule", self.addAttRule)
                    menu.addAction("Add chaining rule", self.addChainRule)
                menu.addAction("Set routine flags", self.setFlags)
            else:
                menu.addAction("Delete rule", self.deleteItem)
        menu.exec_(self.viewport().mapToGlobal(position))

    @pyqtSlot()
    def addSubRule(self):
        self.model().addRule(self.selectedIndexes()[0], Substitution([[]], [[]]))
        self.parent.editor.setWindowModified(True)

    @pyqtSlot()
    def addPosRule(self):
        self.model().addRule(
            self.selectedIndexes()[0], Positioning([[]], [ValueRecord()])
        )
        self.parent.editor.setWindowModified(True)

    @pyqtSlot()
    def addChainRule(self):
        self.model().addRule(self.selectedIndexes()[0], Chaining([[]], lookups=[[]]))
        self.parent.editor.setWindowModified(True)

    @pyqtSlot()
    def addAttRule(self):
        self.model().addRule(self.selectedIndexes()[0], Attachment("", ""))
        self.parent.editor.setWindowModified(True)

    @pyqtSlot()
    def addToFeature(self):
        index = self.selectedIndexes()[0]
        routine = index.internalPointer()
        dialog = AddToFeatureDialog()
        result = dialog.exec_()
        if result:
            self.project.fontfeatures.addFeature(dialog.feature, [routine])
            self.model().dataChanged.emit(index, index)
            self.parent.editor.setWindowModified(True)
            self.parent.editor.update()

    @pyqtSlot()
    def setFlags(self):
        index = self.selectedIndexes()[0]
        routine = index.internalPointer()
        dialog = LookupFlagEditor(routine)
        result = dialog.exec_()
        if result:
            self.model().dataChanged.emit(index, index)
            self.parent.editor.setWindowModified(True)


    @pyqtSlot()
    def reify(self):
        index = self.selectedIndexes()[0]
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Are you sure?")
        msg.setText("A manual routine will no longer automatically respond to changes in your font. Do you still want to convert this to a manual routine?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg.exec_()
        if retval == QMessageBox.Yes:
            self._reify(index)

    def _reify(self, index):
        oldroutine = index.internalPointer()
        rindex = index.row()
        newroutine = oldroutine.reify()
        self.project.fontfeatures.routines[rindex] = newroutine
        for k,v in self.project.fontfeatures.features.items():
            self.project.fontfeatures.features[k] = [ newroutine if r==oldroutine else r for r in v]

        self.parent.editor.setWindowModified(True)
        self.parent.editor.update()

    def doubleClickHandler(self, index):
        if isinstance(index.internalPointer(), Routine):
            return
        if hasattr(index.internalPointer(), "computed"):
            index = index.parent()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Reify?")
            msg.setText("This is an automatic rule. To edit it manually, you need to convert its routine to a manual routine. Do you want to do this now?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            retval = msg.exec_()
            if retval == QMessageBox.Yes:
                self._reify(index)
            return
        if isinstance(index.internalPointer(), Attachment):
            self.parent.editor.showAttachmentEditor(
                index.internalPointer(), index=index
            )
            return
        self.parent.editor.showRuleEditor(index.internalPointer(), index=index)

    @pyqtSlot()
    def addRoutine(self):
        if self.selectedIndexes():
            index = self.selectedIndexes()[0]
            self.model().insertRows(index.row()+1, 1)
            index = self.model().index(index.row()+1, 0)
        else:
            index = self.model().appendRow()
        self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
        self.edit(index)
        self.parent.editor.setWindowModified(True)

    @pyqtSlot()
    def addSeparatorRoutine(self):
        index = self.selectedIndexes()[0]
        self.model().insertRows(index.row()+1, 1)
        self.project.fontfeatures.routines[index.row()+1] = DividerRoutine()
        self.parent.editor.setWindowModified(True)

    @pyqtSlot()
    def deleteItem(self):
        # XXX Check if routine is in use. Remove from Feature
        self.model().removeRows(self.selectedIndexes()[0].row(), 1, QModelIndex())
        self.parent.editor.setWindowModified(True)


class LookupListModel(QAbstractItemModel):
    def __init__(self, proj, parent=None):
        super(LookupListModel, self).__init__(parent)
        self._parent = parent
        self.project = proj

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        return "Lookups"

    def rowCount(self, index=QModelIndex()):
        if index.row() == -1:
            return len(self.project.fontfeatures.routines)
        if index.isValid():
            item = index.internalPointer()
            if isinstance(item, Routine):
                item.editor = self._parent.parent.editor
                return len(item.rules)
        return 0

    def columnCount(self, index=QModelIndex()):
        return 1

    def supportedDropActions(self):
        return Qt.MoveAction

    def parent(self, index):
        if isinstance(index.internalPointer(), Routine):
            return QModelIndex()
        rule = index.internalPointer()
        # Now go find it
        for row, routine in enumerate(self.project.fontfeatures.routines):
            routine.editor = self._parent.parent.editor
            if rule in routine.rules:
                return self.createIndex(row, 0, routine)
        return QModelIndex()

    def index(self, row, column, index=QModelIndex()):
        """ Returns the index of the item in the model specified by the given row, column and parent index """

        if not self.hasIndex(row, column, index):
            return QModelIndex()
        # print(row, column, index.internalPointer())
        if not index.isValid():
            ix = self.createIndex(row, column, self.project.fontfeatures.routines[row])
        else:
            item = index.internalPointer()
            item.editor = self._parent.parent.editor
            ix = self.createIndex(row, column, item.rules[row])
        return ix

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False

        if index.isValid() and 0 <= index.row() < len(
            self.project.fontfeatures.routines
        ):
            if  isinstance(self.project.fontfeatures.routines[index.row()], DividerRoutine):
                self.project.fontfeatures.routines[index.row()].comment = value
            else:
                self.project.fontfeatures.routines[index.row()].name = value
            # self.dataChanged.emit(index, index)
            return True

        return False

    def indexIsRoutine(self, index):
        item = index.internalPointer()
        return isinstance(item, Routine)

    def indexIsRule(self, index):
        item = index.internalPointer()
        return not isinstance(item, Routine)

    def describeFlags(self, routine):
        flags = []
        if not routine.flags:
            return ""
        if routine.flags & 0x2:
            flags.append("IgnoreBase")
        if routine.flags & 0x8:
            flags.append("IgnoreMark")
        if routine.flags & 0x4:
            flags.append("IgnoreLig")
        if routine.flags & 0x1:
            flags.append("RightToLeft")
        if len(flags):
            return " (" + ",".join(flags) + ")"
        return ""

    def data(self, index, role=Qt.DisplayRole):
        # print("Getting index ", index.row(), index.column(), index.internalPointer())
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.EditRole and self.indexIsRoutine(index) and isinstance(item,DividerRoutine):
            return item.comment
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if self.indexIsRoutine(index):
                if isinstance(item, DividerRoutine):
                    return f'<i style="color:#aaa">{item.comment or "————"}</i>'
                else:
                    return (item.name or "")+ self.describeFlags(item)
            elif hasattr(item, "computed"):
                return f'<i style="color:#aaa">{item.asFea()}</i>'
            elif isinstance(item, Attachment):
                return (
                    f'Attach {item.mark_name or "Nothing"} to {item.base_name or "Nothing"}'
                    + self.describeFlags(item)
                )
            else:
                fea = item.asFea() or "<New %s Rule>" % item.__class__.__name__
                return fea.split("\n")[0]
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsDropEnabled
        flag = Qt.ItemFlags(QAbstractItemModel.flags(self, index))
        if self.indexIsRoutine(index):
            return flag | Qt.ItemIsEditable | Qt.ItemIsDragEnabled
        return flag | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    def insertRows(self, position, rows=1, parent=QModelIndex()):
        """ Insert a row into the model. """
        assert(rows == 1)
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)

        self.project.fontfeatures.routines.insert(position,Routine(name="", rules=[]))
        self.endInsertRows()
        return True

    def appendRow(self):
        self.insertRows(len(self.project.fontfeatures.routines))
        return self.index(len(self.project.fontfeatures.routines) - 1, 0)

    def removeRows(self, row, count, parent):
        self.beginRemoveRows(parent, row, row+1)
        self.project.fontfeatures.routines.pop(row)
        self.endRemoveRows()
        return True

    def mimeData(self, indexes):
        mimeData = super().mimeData(indexes)
        mimeData.setText("row id: %i" %  indexes[0].row())
        return mimeData

    def dropMimeData(self, data, action, destrow, column, parent):
        if parent.isValid():
            return False
        if not data.hasText() or not "row id:" in data.text():
            return False
        rowid = int(data.text()[7:])
        routines = self.project.fontfeatures.routines
        self.beginInsertRows(QModelIndex(), destrow, destrow)
        routines.insert(destrow, routines[rowid])
        self.endInsertRows()
        return True

    def removeRow(self, index):
        """ Remove a row from the model. """
        self.beginRemoveRows(self.parent(index), index.row(), index.row())
        if self.indexIsRoutine(index):
            del self.project.fontfeatures.routines[index.row()]
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
