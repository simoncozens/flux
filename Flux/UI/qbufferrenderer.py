from PyQt5.QtCore import QPoint, QMargins, Qt, QRectF
from PyQt5.QtGui import QGlyphRun, QPainter, QRawFont, QColor, QTransform, QPainterPath, QPen
from PyQt5.QtWidgets import QWidget, QGraphicsScene, QGraphicsPathItem, QGraphicsView
import glyphsLib
import darkdetect

inkcolor = (0,0,0)
if darkdetect.isDark():
    inkcolor = (255,255,255)

class QBufferRenderer(QGraphicsView):
    def __init__(self, project, buf=None):
        super(QBufferRenderer, self).__init__()

        self.project = project
        self.buf = buf
        self.margins = QMargins(25, 25, 25, 25)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.HighQualityAntialiasing)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.set_scene_from_buf()

    def set_scene_from_buf(self):
        self.scene.clear()
        xcursor = 0
        if self.buf and len(self.buf) > 0:
            items = self.buf.items
            if self.buf.direction == "RTL":
                items = list(reversed(items))
            for g in items:
                color = inkcolor
                if hasattr(g, "color"):
                    color = g.color
                self.drawGlyph_glyphs(self.scene, g, xcursor + (g.position.xPlacement or 0), (g.position.yPlacement or 0), color)
                if hasattr(g, "anchor"):
                    self.drawCross(self.scene, g.anchor[0], g.anchor[1], color)
                else:
                    xcursor = xcursor + g.position.xAdvance
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def decomposedPaths(self, layer, item=None):
        paths = layer.paths
        for c in layer.components:
            t = c.transform
            componentPaths = self.decomposedPaths(c.layer)
            for c in componentPaths:
                g = glyphsLib.GSPath()
                g.nodes = [glyphsLib.GSNode((n.position.x, n.position.y), n.type) for n in c.nodes]
                if not item or not hasattr(item, "anchor"):
                    g.applyTransform(t)
                paths.append(g)
        return paths

    def drawCross(self, scene, x, y, color):
        path = QPainterPath()
        path.moveTo(x-50, y)
        path.lineTo(x+50, y)
        path.moveTo(x, y-50)
        path.lineTo(x, y+50)
        line = QGraphicsPathItem()
        p = QPen( QColor(*color) )
        p.setWidth(5)
        line.setPen(p )
        line.setPath(path)
        reflect = QTransform(1,0,0,-1,0,0)
        line.setTransform(reflect)
        scene.addItem(line)

    def drawGlyph_glyphs(self, scene, item, offsetX=0, offsetY=0, color=(255,255,255)):
        glyph = item.glyph
        font = self.project.font.font
        if not glyph in font.font.glyphs:
            print("No glyph "+glyph)
            return
        layer = font.font.glyphs[glyph].layers[font.id]
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        for gsPath in self.decomposedPaths(layer, item):
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
        line.setBrush( QColor(*color) )
        p = QPen()
        p.setStyle(Qt.NoPen)
        line.setPen(p)
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
