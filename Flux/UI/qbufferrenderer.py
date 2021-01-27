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
        self.location = None
        self.margins = QMargins(25, 25, 25, 25)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.HighQualityAntialiasing)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.set_scene_from_buf()

    def set_scene_from_buf(self):
        self.scene.clear()
        xcursor = 0
        if self.buf is not None and len(self.buf.items) > 0:
            items = self.buf.items
            if self.buf.direction == "RTL":
                items = list(reversed(items))
            for g in items:
                color = inkcolor
                if hasattr(g, "color"):
                    color = g.color
                glyph = g.glyph
                if hasattr(g, "anchor"):
                    self.drawCross(self.scene, xcursor + g.anchor[0], g.anchor[1], color)
                if not glyph in self.project.font:
                    continue
                self.drawGlyph(self.scene, glyph, xcursor + (g.position.xPlacement or 0), (g.position.yPlacement or 0), color)
                # else:
                xcursor = xcursor + g.position.xAdvance
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def getGlyphContours(self, glyphname):
        if self.location:
            vf = self.project.variations
            interpolated_glyph = self.interpolate(glyphname)
            paths = list(interpolated_glyph.contours)
        else:
            paths = list(self.project.font[glyphname].contours)
        return paths

    def decomposedPaths(self, glyphname, item=None):
        paths = self.getGlyphContours(glyphname)
        for ix, c in enumerate(self.project.font[glyphname].components):

            glyph = c.baseGlyph
            componentPaths = [x.copy() for x in self.getGlyphContours(glyph)]
            if self.location:
                transformation = self.interpolate_component_transformation(glyphname, ix)
            else:
                transformation = c.transformation
            for cp in componentPaths:
                cp.transformBy(transformation)
                paths.append(cp)
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

    def set_location(self, location):
        self.location = self.project.variations.normalize(location)
        self.set_scene_from_buf()

    def interpolate(self, glyphname):
        vf = self.project.variations
        glyphs = [vf.masters[master][glyphname] for master in vf.master_order]
        glyph = self.project.font[glyphname]
        for pid, paths in enumerate(zip(*[g.contours for g in glyphs])):
            for pointid,points in enumerate(zip(*[p.points for p in paths])):
                target_point = glyph.contours[pid].points[pointid]
                pointset = {vf.master_order[i]: (points[i].x,points[i].y) for i in range(len(vf.masters))}
                (interpolated) = vf.interpolate_tuples(pointset, self.location, normalized=True)
                target_point.x, target_point.y = interpolated
        return glyph

    def interpolate_component_transformation(self, glyphname, ix):
        vf = self.project.variations
        transformations = {
            master: vf.masters[master][glyphname].components[ix].transformation
            for master in vf.master_order
        }
        return vf.interpolate_tuples(transformations, self.location, normalized=True)

    def drawGlyph(self, scene, glyph, offsetX=0, offsetY=0, color=(255,255,255)):
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        for c in self.decomposedPaths(glyph):
            segs = c.segments
            path.moveTo(segs[-1].points[-1].x, segs[-1].points[-1].y)
            for seg in segs:
                tuples = [(a.x, a.y) for a in seg.points]
                flattuples = list(sum(tuples,()))
                if len(tuples) == 2:
                    path.quadTo(*flattuples)
                elif len(tuples) == 3:
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
        # print(f"Drawing {glyph} at offset {offsetX} {offsetY}")
        line.setTransform(reflect)
        scene.addItem(line)

    def set_buf(self, buf):
        self.buf = buf
        self.set_scene_from_buf()

    def resizeEvent(self, e):
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

if __name__ == "__main__":
    from Flux.project import FluxProject
    from PyQt5.QtWidgets import QApplication, QVBoxLayout
    from fontFeatures.shaperLib.Buffer import Buffer
    import sys

    app = 0
    if QApplication.instance():
        app = QApplication.instance()
    else:
        app = QApplication(sys.argv)

    w = QWidget()
    w.resize(510, 210)
    v_box_1 = QVBoxLayout()

    proj = FluxProject.new("Rajdhani.glyphs")
    buf = Buffer(proj.font, unicodes = "ABC")
    buf.map_to_glyphs()
    v_box_1.addWidget(QBufferRenderer(proj,buf))

    w.setLayout(v_box_1)

    w.show()
    sys.exit(app.exec_())
