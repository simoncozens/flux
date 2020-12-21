from lxml import etree
from fontFeatures import FontFeatures, Routine, Substitution
from babelfont import Babelfont
from fontFeatures.feaLib import FeaUnparser
from fontTools.ttLib import TTFont
from fontFeatures.ttLib import unparse
from Flux.computedroutine import ComputedRoutine

class FluxProject:

    @classmethod
    def new(klass, fontfile):
        self = FluxProject()
        self.fontfile = fontfile
        self.font = Babelfont.open(self.fontfile)
        self.fontfeatures = FontFeatures()
        self.glyphclasses = {}
        self.filename = None

        if self.fontfile.endswith(".ttf") or self.fontfile.endswith(".otf"):
            self._load_features_binary()
        else:
            self._load_features_source()

        for groupname, contents in self.font.groups.items():
            self.glyphclasses[groupname] = {
                "type": "manual",
                "contents": contents
            }
            self.fontfeatures.namedClasses[groupname] = tuple(contents)
        # Load up the anchors too
        self._load_anchors()
        return self

    def __init__(self, file=None):
        if not file:
            return
        self.filename = file
        self.xml = etree.parse(file).getroot()
        self.fontfile = self.xml.find("source").get("file")
        self.font = Babelfont.open(self.fontfile)
        self.fontfeatures = FontFeatures()
        self.xmlToFontFeatures()

        self.glyphclasses = {}  # Will sync to fontFeatures when building
        # XXX will it?

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
                    self.fontfeatures.namedClasses[c.get("name")] = tuple([g.text for g in c])

        # The font file is the authoritative source of the anchors, so load them
        # from the font file on load, in case they have changed.
        self._load_anchors()

    def _load_anchors(self):
        for g in self.font:
            for a in g.anchors:
                if not a.name in self.fontfeatures.anchors:
                    self.fontfeatures.anchors[a.name] = {}
                self.fontfeatures.anchors[a.name][g.name] = (a.x, a.y)

    def _slotArray(self, el):
        return [[g.text for g in slot.findall("glyph")] for slot in list(el)]

    def xmlToFontFeatures(self):
        routines = {}
        for xmlroutine in self.xml.find("routines"):
            if "computed" in xmlroutine.attrib:
                r = ComputedRoutine.fromXML(xmlroutine)
                r.project = self
            else:
                r = Routine.fromXML(xmlroutine)
            routines[r.name] = r
            self.fontfeatures.addRoutine(r)
        for xmlfeature in self.xml.find("features"):
            # Temporary until we refactor fontfeatures
            featurename = xmlfeature.get("name")
            self.fontfeatures.features[featurename] = []
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
            f.set("name", k)
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

    def saveFEA(self, filename):
        try:
            asfea = self.fontfeatures.asFea()
            with open(filename, "w") as out:
                out.write(asfea)
            return None
        except Exception as e:
            return str(e)

    def loadFEA(self, filename):
        unparsed = FeaUnparser(open(filename,"r"))
        self.fontfeatures = unparsed.ff

    def _load_features_binary(self):
        tt = TTFont(self.fontfile)
        self.fontfeatures = unparse(tt)
        print(self.fontfeatures.features)

    def _load_features_source(self):
        if self.font.features and self.font.features.text:
            try:
                unparsed = FeaUnparser(self.font.features.text)
                self.fontfeatures = unparsed.ff
            except Exception as e:
                print("Could not load feature file: %s" % e)
