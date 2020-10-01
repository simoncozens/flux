from lxml import etree
from fontFeatures import FontFeatures, Routine, Substitution
from fontFeatures.fontProxy import FontProxy

class FluxProject:

    @classmethod
    def new(klass, fontfile):
        self = FluxProject()
        self.fontfile = fontfile
        self.font = FontProxy.opener(self.fontfile)
        self.fontfeatures = FontFeatures()
        self.glyphclasses = {}

        ## XXX Glyphs specific code here
        for glyphclass in self.font.font.font.classes:
            self.glyphclasses[glyphclass.name] = {
                "type": "manual",
                "contents": glyphclass.code.split()
            }

        return self

    def __init__(self, file=None):
        if not file:
            return
        self.filename = file
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
        routines = {}
        for xmlroutine in self.xml.find("routines"):
            r = Routine.fromXML(xmlroutine)
            routines[r.name] = r
            self.fontfeatures.addRoutine(r)
        for xmlfeature in self.xml.find("features"):
            # Temporary until we refactor fontfeatures
            featurename = xmlfeature.get("name")
            for r in xmlfeature:
                self.fontfeatures.addFeature(featurename, [routines[r.get("name")]])

    def save(self, filename=None):
        if not filename:
            filename = self.filename
        flux = etree.Element("flux")
        etree.SubElement(flux, "source").set("file", self.fontfile)
        glyphclasses = etree.SubElement(flux, "glyphclasses")
        for k,v in self.glyphclasses.items():
            self.serializeGlyphClass(glyphclasses, k, v)
        # Plugins

        # Features
        features = etree.SubElement(flux, "features")
        for k,v in self.fontfeatures.features.items():
            f = etree.SubElement(features, "feature")
            for routine in v:
                etree.SubElement(f, "routine").set("name", routine.name)
        # Routines
        routines = etree.SubElement(flux, "routines")
        for r in self.fontfeatures.routines:
            routines.append(r.toXML())
        et = etree.ElementTree(flux)
        with open(filename, "wb") as out:
            et.write(out, pretty_print=True)


    def serializeGlyphClass(self, element, name, value):
        c = etree.SubElement(element, "class")
        c.set("name", name)
        if value["type"] == "automatic":
            c.set("automatic", "true")
            for pred in value["predicates"]:
                pred_xml = etree.SubElement(c, "predicate")
                for k, v in pred.items():
                    pred_xml.set(k, v)
        else:
            c.set("automatic", "false")
            for glyph in value["contents"]:
                etree.SubElement(c, "glyph").text = glyph
        return c


