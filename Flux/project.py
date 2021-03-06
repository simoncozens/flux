from lxml import etree
from fontFeatures import FontFeatures, Routine, Substitution
from babelfont import Babelfont
from fontFeatures.feaLib import FeaUnparser
from fontTools.feaLib.builder import Builder
from fontTools.ttLib import TTFont
from fontFeatures.ttLib import unparse
from Flux.computedroutine import ComputedRoutine
from Flux.dividerroutine import DividerRoutine
from io import StringIO as UnicodeIO
from Flux.UI.GlyphActions import GlyphAction
from Flux.UI.glyphpredicateeditor import GlyphClassPredicateTester, GlyphClassPredicate
from babelfont.variablefont import VariableFont
import os

class FluxProject:

    @classmethod
    def new(klass, fontfile, editor=None):
        self = FluxProject()
        self.fontfeatures = FontFeatures()
        self.fontfile = fontfile
        self.editor = editor
        if not self._load_fontfile():
            return
        self.glyphclasses = {}
        self.glyphactions = {}
        self.debuggingText = ""
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
            self.fontfeatures.namedClasses.forceput(groupname, tuple(contents))
        # Load up the anchors too
        self._load_anchors()
        return self

    def __init__(self, file=None):
        if not file:
            return
        self.filename = file
        self.xml = etree.parse(file).getroot()
        dirname = os.path.dirname(file)
        self.fontfile = os.path.join(dirname,self.xml.find("source").get("file"))
        self.fontfeatures = FontFeatures()
        if not self._load_fontfile():
            return
        self.glyphactions = {}
        self.xmlToFontFeatures()
        text = self.xml.find("debuggingText")
        if text is not None:
            self.debuggingText = text.text
        else:
            self.debuggingText = ""

        self.glyphclasses = {}  # Will sync to fontFeatures when building
        # XXX will it?

        glyphclasses = self.xml.find("glyphclasses")
        if glyphclasses is not None:
            for c in glyphclasses:
                thisclass = self.glyphclasses[c.get("name")] = {}
                if c.get("automatic") == "true":
                    thisclass["type"] = "automatic"
                    thisclass["predicates"] = [ dict(p.items()) for p in c.findall("predicate") ]
                    self.fontfeatures.namedClasses[c.get("name")] = tuple(GlyphClassPredicateTester(self).test_all([
                        GlyphClassPredicate(x) for x in thisclass["predicates"]
                    ]))
                else:
                    thisclass["type"] = "manual"
                    thisclass["contents"] = [g.text for g in c]
                    self.fontfeatures.namedClasses[c.get("name")] = tuple([g.text for g in c])

        # The font file is the authoritative source of the anchors, so load them
        # from the font file on load, in case they have changed.
        self._load_anchors()
        self._load_glyphactions()

    def _load_fontfile(self):
        try:
            if self.fontfile.endswith(".ufo") or self.fontfile.endswith("tf"):
                # Single master workflow
                self.font = Babelfont.open(self.fontfile)
                self.variations = None
            else:
                self.variations = VariableFont(self.fontfile)
                # We need a "scratch copy" because we will be trashing the
                # glyph data with our interpolations
                if len(self.variations.masters.keys()) == 1:
                    self.font = list(self.variations.masters.values())[0]
                    self.variations = None
                else:
                    firstmaster = self.variations.designspace.sources[0].path
                    if firstmaster:
                        self.font = Babelfont.open(firstmaster)
                    else: # Glyphs, fontlab?
                        self.font = Babelfont.open(self.fontfile)
        except Exception as e:
            if self.editor:
                self.editor.showError("Couldn't open %s: %s" % (self.fontfile, e))
            else:
                raise e
            return False
        return True

    def _load_anchors(self):
        for g in self.font:
            for a in g.anchors:
                if not a.name in self.fontfeatures.anchors:
                    self.fontfeatures.anchors[a.name] = {}
                self.fontfeatures.anchors[a.name][g.name] = (a.x, a.y)

    def _load_glyphactions(self):
        glyphactions = self.xml.find("glyphactions")
        if not glyphactions:
            return
        for xmlaction in glyphactions:
            g = GlyphAction.fromXML(xmlaction)
            self.glyphactions[g.glyph] = g
            g.perform(self.font)

    def _slotArray(self, el):
        return [[g.text for g in slot.findall("glyph")] for slot in list(el)]

    def xmlToFontFeatures(self):
        routines = {}
        warnings = []
        for xmlroutine in self.xml.find("routines"):
            if "computed" in xmlroutine.attrib:
                r = ComputedRoutine.fromXML(xmlroutine)
                r.project = self
            elif "divider" in xmlroutine.attrib:
                r = DividerRoutine.fromXML(xmlroutine)
            else:
                r = Routine.fromXML(xmlroutine)
            routines[r.name] = r
            self.fontfeatures.routines.append(r)
        for xmlfeature in self.xml.find("features"):
            # Temporary until we refactor fontfeatures
            featurename = xmlfeature.get("name")
            self.fontfeatures.features[featurename] = []
            for r in xmlfeature:
                routinename = r.get("name")
                if routinename in routines:
                    self.fontfeatures.addFeature(featurename, [routines[routinename]])
                else:
                    warnings.append("Lost routine %s referenced in feature %s" % (routinename, featurename))
        return warnings # We don't do anything with them yet

    def save(self, filename=None):
        if not filename:
            filename = self.filename
        flux = etree.Element("flux")
        etree.SubElement(flux, "source").set("file", self.fontfile)
        etree.SubElement(flux, "debuggingText").text = self.debuggingText
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

        # Glyph actions
        if self.glyphactions:
            f = etree.SubElement(flux, "glyphactions")
            for ga in self.glyphactions.values():
                f.append(ga.toXML())

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

    def saveOTF(self, filename):
        try:
            self.font.save(filename)
            ttfont = TTFont(filename)
            featurefile = UnicodeIO(self.fontfeatures.asFea())
            builder = Builder(ttfont, featurefile)
            catmap = { "base": 1, "ligature": 2, "mark": 3, "component": 4 }
            for g in self.font:
                if g.category in catmap:
                    builder.setGlyphClass_(None, g.name, catmap[g.category])
            builder.build()
            ttfont.save(filename)
        except Exception as e:
            print(e)
            return str(e)
