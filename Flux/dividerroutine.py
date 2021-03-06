from fontFeatures import Routine
from lxml import etree


class DividerRoutine(Routine):
    def __init__(self, **kwargs):
        self.comment = None
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
        if self.comment:
            root.attrib["comment"] = self.comment
        return root

    @classmethod
    def fromXML(klass, el):
        return klass(comment=el.get("comment"))
