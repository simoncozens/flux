
# Adapted from https://gist.github.com/Cysu/7461066
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QPushButton,
    QCompleter,
    QLabel,
    QSizePolicy,
    QDialog,
    QDialogButtonBox,
    QLayout,
    QGridLayout,
     QStyle
)
class QFlowGridLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(QFlowGridLayout, self).__init__(parent)
        self.margin = margin

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(QFlowGridLayout, self).setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.margin, 2 * self.margin)
        return size

    def _doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        # SC hacks. I am assuming we are a grid, and all spaceX/spaceY is
        # the same. So we only do this once.

        # Find first visible item
        item = None
        for i in self.itemList:
            if i.widget().isVisible():
                item = i
                break
        if not item:
            return 0
        wid = item.widget()
        spaceX = self.spacing() + wid.style().layoutSpacing(
            QSizePolicy.PushButton,
            QSizePolicy.PushButton,
            QtCore.Qt.Horizontal)

        spaceY = self.spacing() + wid.style().layoutSpacing(
            QSizePolicy.PushButton,
            QSizePolicy.PushButton,
            QtCore.Qt.Vertical)

        itemSize = item.sizeHint()
        itemWidth = itemSize.width()
        itemHeight = itemSize.height()

        for item in self.itemList:
            if not item.widget().isVisible():
                continue

            nextX = x + itemWidth + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + itemWidth + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(
                    QtCore.QRect(QtCore.QPoint(x, y), itemSize))

            x = nextX
            lineHeight = max(lineHeight, itemHeight)

        return y + lineHeight - rect.y()


if __name__ == '__main__':

    import sys

    class Window(QWidget):
        def __init__(self):
            super(Window, self).__init__()

            flowLayout = QFlowGridLayout()
            flowLayout.addWidget(QPushButton("Short"))
            flowLayout.addWidget(QPushButton("Longer"))
            flowLayout.addWidget(QPushButton("Different text"))
            flowLayout.addWidget(QPushButton("More text"))
            flowLayout.addWidget(QPushButton("Even longer button text"))
            self.setLayout(flowLayout)

            self.setWindowTitle("Flow Layout")

    app = QApplication(sys.argv)
    mainWin = Window()
    mainWin.show()
    sys.exit(app.exec_())
