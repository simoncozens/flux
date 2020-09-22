from lxml import etree
from fontFeatures import FontFeatures, Routine, Substitution


class FluxProject:
    def __init__(self, file):
        self.xml = etree.parse(file).getroot()
        self.fontfile = self.xml.find("source").get("file")
        self.fontfeatures = FontFeatures()
        self.xmlToFontFeatures()

        self.glyphclasses = {}  # Will sync to fontFeatures when building

        glyphclasses = self.xml.find("glyphclasses")
        if glyphclasses is not None:
            for c in glyphclasses:
                thisclass = self.glyphclasses[c.get("name")] = {}
                if c.get("automatic") == "true":
                    thisclass["type"] = "automatic"
                else:
                    thisclass["type"] = "manual"
                    thisclass["contents"] = [g.text for g in c]

    def _slotArray(self, el):
        return [[g.text for g in slot.findall("glyph")] for slot in list(el)]

    def xmlToFontFeatures(self):
        for xmlroutine in self.xml.find("routines"):
            r = Routine(name=xmlroutine.get("name"))
            for xmlrule in xmlroutine:
                if xmlrule.tag == "substitute":
                    rule = Substitution(
                        self._slotArray(xmlrule.find("from")),
                        self._slotArray(xmlrule.find("to")),
                    )
                    r.addRule(rule)
            self.fontfeatures.addRoutine(r)
