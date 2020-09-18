from collections import namedtuple
from fontFeatures.ttLib import unparse
from vharfbuzz import Vharfbuzz
import fontFeatures
from fontTools.ttLib import TTFont
from fontFeatures.feaLib.Chaining import suborpos

LookupInfo = namedtuple("LookupInfo", ["name", "language", "feature", "address"])


class TTFontInfo:
    def __init__(self, filename):
        self.filename = filename
        self.font = TTFont(filename)
        self.vharfbuzz = Vharfbuzz(filename)
        self.fontfeatures = unparse(self.font)
        self.setup_lookups()

    def setup_lookups(self):
        self._all_lookups = []
        self._lookup_info = {}
        self._features = self.fontfeatures.features
        for routine in self.fontfeatures.routines:
            table, lid = routine.address[0:2]
            extra = routine.address[2:]
            self._lookup_info[(table, int(lid))] = LookupInfo(
                routine.name, None, None, extra
            )
            self._all_lookups.append(routine)
        for key, routines in self._features.items():
            for routine in routines:
                table, lid = routine.address[0:2]
                extra = routine.address[2:]
                print(key, routine, lid)
                self._lookup_info[(table, int(lid))] = LookupInfo(
                    routine.name, None, key, extra
                )
                if routine not in self._all_lookups:
                    self._all_lookups.append(routine)
        for chain in self.fontfeatures.allRules(fontFeatures.Chaining):
            for routinelist in chain.lookups:
                if not routinelist:
                    continue
                for routine in routinelist:
                    table, lid = routine.address[0:2]
                    extra = routine.address[2:]
                    self._lookup_info[(table, int(lid))] = LookupInfo(
                        routine.name, None, key, None
                    )
                    if routine not in self._all_lookups:
                        self._all_lookups.append(routine)

    @property
    def glyph_classes(self):
        return self.fontfeatures.namedClasses

    @property
    def all_lookups(self):
        return self._all_lookups

    def lookup_info(self, table, lid):  # name, language, feature, address
        return self._lookup_info[(table, lid)]

    @property
    def features(self):
        return self._features
