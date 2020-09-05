from fontFeatures.ttLib import unparse

from vharfbuzz import Vharfbuzz


class TTFontInfo:
    def __init__(self, filename):
        self.filename = filename
        self.vharfbuzz = Vharfbuzz(filename)
        self.fontfeatures = unparse(filename)
        self.setup_lookups()

    def setup_lookups(self):
        self._all_lookups = []
        self._lookup_info = {}
        self._features = self.fontfeatures.features
        for routine in self.fontfeatures.routines:
            lid = None
            for r in routine.rules:
                lid = r.address or lid
            self._lookup_info[lid] = routine.name, None, None, None
            self._all_lookups.append(routine)
        # Add non-free routines here
        for key, routines in self._features.items():
            for routine in routines:
                lid = None
                for r in routine.rules:
                    lid = r.address or lid
                self._lookup_info[lid] = routine.name, None, key, None
                self._all_lookups.append(routine)

    @property
    def glyph_classes(self):
        return self.fontfeatures.namedClasses

    @property
    def all_lookups(self):
        return self._all_lookups

    def lookup_info(self, lid):  # name, script, language, feature, address
        return self._lookup_info[lid]

    @property
    def features(self):
        return self._features
