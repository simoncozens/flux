from PyQt5.QtCore import QPoint, QMargins, Qt, QRectF
from PyQt5.QtGui import QGlyphRun, QPainter, QRawFont, QColor, QTransform, QPainterPath
from PyQt5.QtWidgets import QWidget, QGraphicsScene, QGraphicsPathItem, QGraphicsView


class QBufferRenderer(QGraphicsView):
    def __init__(self, project, buf=None):
        super(QBufferRenderer, self).__init__()

        self.project = project
        self.buf = buf
        self.margins = QMargins(25, 25, 25, 25)
        self.set_scene_from_buf()

    def set_scene_from_buf(self):
        self.scene = QGraphicsScene(self)
        xcursor = 0
        if self.buf and len(self.buf) > 0:
            items = self.buf.items
            if self.buf.direction == "RTL":
                items = list(reversed(items))
            for g in items:
                self.drawGlyph_glyphs(self.scene, g.glyph, xcursor + (g.position.xPlacement or 0), (g.position.yPlacement or 0))
                xcursor = xcursor + g.position.xAdvance
        self.setScene(self.scene)


    def drawGlyph_glyphs(self, scene, glyph, offsetX=0, offsetY=0):
        font = self.project.font.font
        layer = font.font.glyphs[glyph].layers[font.id]
        path = QPainterPath()
        for gsPath in layer.paths:
            segs = gsPath.segments
            path.moveTo(segs[0][0].x, segs[0][0].y)
            for seg in segs:
                tuples = [(a.x, a.y) for a in seg[1:]]
                flattuples = list(sum(tuples,()))
                if len(tuples) == 3:
                    path.cubicTo(*flattuples)
                else:
                    path.lineTo(*flattuples)

        line = QGraphicsPathItem()
        line.setBrush( QColor(255, 255, 255) )
        line.setPath(path)
        reflect = QTransform(1,0,0,-1,0,0)
        reflect.translate(offsetX, offsetY)
        line.setTransform(reflect)
        scene.addItem(line)

    def set_buf(self, buf):
        self.buf = buf
        self.set_scene_from_buf()

    def resizeEvent(self, e):
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
