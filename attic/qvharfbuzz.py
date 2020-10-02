from PyQt5.QtCore import QPoint, QMargins
from PyQt5.QtGui import QGlyphRun, QPainter, QRawFont
from PyQt5.QtWidgets import QWidget


class QVHarfbuzzWidget(QWidget):
    def __init__(self, vharfbuzz, size, buf):
        self.vharfbuzz = vharfbuzz
        self.size = size
        self.buf = buf
        self.setup_font()
        self.margins = QMargins(25, 25, 25, 25)
        super(QVHarfbuzzWidget, self).__init__()

    def set_buf(self, buf):
        self.buf = buf
        self.update()

    def setup_font(self):
        rf = QRawFont()
        rf.loadFromData(self.vharfbuzz.fontdata, self.size, 0)
        self.rf = rf

    def scale_point(self, x, y):
        return QPoint(
            x / self.vharfbuzz.upem * self.size, y / self.vharfbuzz.upem * self.size
        )

    def paintEvent(self, e):
        if not self.buf:
            return
        qp = QPainter()
        qp.begin(self)
        g = QGlyphRun()
        g.setRawFont(self.rf)
        g.setGlyphIndexes([x.codepoint for x in self.buf.glyph_infos])
        pos = (0, 0)
        poses = []
        for _p in self.buf.glyph_positions:
            p = _p.position
            # Y coordinates go down, not up.
            poses.append(self.scale_point(pos[0] + p[0], pos[1] - p[1]))
            pos = (pos[0] + p[2], pos[1] + p[3])

        g.setPositions(poses)
        qp.drawGlyphRun(e.rect().marginsRemoved(self.margins).bottomLeft(), g)
        qp.end()
