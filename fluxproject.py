from lxml import etree
from fontFeatures import FontFeatures, Routine, Substitution
from fontFeatures.fontProxy import FontProxy

class FluxProject:
    def __init__(self, file):
        self.xml = etree.parse(file).getroot()
        self.fontfile = self.xml.find("source").get("file")
        self.font = FontProxy.opener(self.fontfile)
        self.fontfeatures = FontFeatures()
        self.xmlToFontFeatures()

        self.glyphclasses = {}  # Will sync to fontFeatures when building

        glyphclasses = self.xml.find("glyphclasses")
        if glyphclasses is not None:
            for c in glyphclasses:
                thisclass = self.glyphclasses[c.get("name")] = {}
                if c.get("automatic") == "true":
                    thisclass["type"] = "automatic"
                    thisclass["predicates"] = [ dict(p.items()) for p in c.findall("predicate") ]
                else:
                    thisclass["type"] = "manual"
                    thisclass["contents"] = [g.text for g in c]

    def _slotArray(self, el):
        return [[g.text for g in slot.findall("glyph")] for slot in list(el)]

    def xmlToFontFeatures(self):
        for xmlroutine in self.xml.find("routines"):
            r = Routine.fromXML(xmlroutine)
            self.fontfeatures.addRoutine(r)
