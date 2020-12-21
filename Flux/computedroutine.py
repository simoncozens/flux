from fontFeatures import Routine
from lxml import etree


class ComputedRoutine(Routine):
    def __init__(self, **kwargs):
        self.parameters = {}
        self.plugin = ""
        self._rules = []
        if "parameters" in kwargs:
            self.parameters = kwargs["parameters"]
            del kwargs["parameters"]
        super().__init__(**kwargs)

    @property
    def okay(self):
        if hasattr(self, "module"):
            return True
        assert self.editor
        return self.plugin in self.editor.plugins

    @property
    def rules(self):
        if not self._rules:
            assert self.project
            if not self.okay:
                return []
            if not hasattr(self, "module"):
                mod = self.editor.plugins[self.plugin]
            else:
                mod = self.module
            rules = mod.rulesFromComputedRoutine(self)
            for r in rules:
                r.computed = True
            self._rules = rules
        return self._rules

    @rules.setter
    def rules(self, value):
        pass

    def toXML(self):
        root = etree.Element("routine")
        root.attrib["computed"] = "true"
        root.attrib["plugin"] = self.plugin
        if self.flags:
            root.attrib["flags"] = str(self.flags)
        if self.address:
            root.attrib["address"] = str(self.address)
        if self.name:
            root.attrib["name"] = self.name
        for k, v in self.parameters.items():
            param = etree.Element("parameter")
            param.attrib["key"] = k
            param.attrib["value"] = v
            root.append(param)

        return root

    @classmethod
    def fromXML(klass, el):
        routine = klass(
            address=el.get("address"),
            name=el.get("name"),
            flags=(int(el.get("flags") or 0)),
        )
        routine.plugin = el.get("plugin")
        for p in el:
            routine.parameters[p.attrib["key"]] = p.attrib["value"]
        return routine
