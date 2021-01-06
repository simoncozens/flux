from fontFeatures import Routine
from lxml import etree


class DividerRoutine(Routine):
    def __init__(self, **kwargs):
        if "comment" in kwargs:
            self.comment = kwargs["comment"]
            del kwargs["comment"]
        super().__init__(**kwargs)

    @property
    def rules(self):
        return []

    @rules.setter
    def rules(self, value):
        pass

    def toXML(self):
        root = etree.Element("routine")
        root.attrib["divider"] = "true"
        root.attrib["comment"] = self.comment

    @classmethod
    def fromXML(klass, el):
        return klass(comment=el.get("comment"))
