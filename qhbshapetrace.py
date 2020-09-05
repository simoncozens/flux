from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
import uharfbuzz as hb


class QHBShapeTrace(QTreeWidget):
    def __init__(self, vharfbuzz, text):
        self.vharfbuzz = vharfbuzz
        self.trace = []
        super(QHBShapeTrace, self).__init__()
        self.setColumnCount(2)
        self.set_text(text)

    def set_text(self, text):
        newtrace = []
        self.clear()
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        buf.set_message_func(self.process_msg)
        self.stack = [QTreeWidgetItem(["GSUB", ""])]
        self.addTopLevelItem(self.stack[0])
        hb.shape(self.vharfbuzz.hbfont, buf)

    def process_msg(self, msg, buf):
        buffernow = self.vharfbuzz.serialize_buf(buf)
        print(msg, buffernow)
        if msg.startswith("start table GPOS"):
            self.stack = [QTreeWidgetItem(["GPOS", ""])]
            self.addTopLevelItem(self.stack[0])
        elif msg.startswith("start lookup "):
            lu = int(msg[13:])
            c = QTreeWidgetItem([msg[6:], buffernow])
            self.stack[-1].addChild(c)
            self.stack.append(c)
        elif msg.startswith("end lookup "):
            if self.stack[-1].text(1) == buffernow:
                self.stack[-1].setForeground(0, QBrush(QColor(128,128,128,128)))
                self.stack[-1].setForeground(1, QBrush(QColor(128,128,128,128)))
            else:
                self.stack[-1].setText(1, buffernow)
            self.stack.pop()
        return True
