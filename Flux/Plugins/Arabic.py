from PyQt5.QtWidgets import (
    QLabel,
    QDialog,
    QLineEdit,
    QGroupBox,
    QCompleter,
    QFormLayout,
    QComboBox,
    QMessageBox,
    QCheckBox
)
from PyQt5.QtGui import QValidator
from Flux.Plugins import FluxPlugin
import re
import fontFeatures


plugin_name = "Arabic Positionals"


class REValidator(QValidator):
    def __init__(self):
        super().__init__()

    def validate(self, s, pos):
        try:
            re.compile(s)
        except Exception as e:
            return (QValidator.Invalid, s, pos)
        return (QValidator.Acceptable, s, pos)

    def fixup(self, s):
        # Trim multiple spaces?
        pass


class Dialog(FluxPlugin):
    def createForm(self):
        form = QGroupBox("IMatra parameters")
        layout = QFormLayout()
        naming, regexps = self.detect_naming_scheme()
        if naming:
            message = f"It looks like you're using the {naming} naming scheme. "
            message = message + "If that's not correct, p"
        else:
            message = "P"
            regexps = {"isol": "", "init": "", "medi": "", "fina": ""}
        message = (
            message
            + "lease enter regular expressions below which will match the appropriate glyph classes"
        )
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addRow(label)

        self.isol_re = QLineEdit()
        self.isol_re.setText(regexps["isol"])
        self.isol_re.setValidator(REValidator())

        self.init_re = QLineEdit()
        self.init_re.setText(regexps["init"])
        self.init_re.setValidator(REValidator())

        self.medi_re = QLineEdit()
        self.medi_re.setText(regexps["medi"])
        self.medi_re.setValidator(REValidator())

        self.fina_re = QLineEdit()
        self.fina_re.setText(regexps["fina"])
        self.fina_re.setValidator(REValidator())

        layout.addRow(QLabel("Base glyphs"), self.isol_re)
        layout.addRow(QLabel("Initial glyphs"), self.init_re)
        layout.addRow(QLabel("Medial glyphs"), self.medi_re)
        layout.addRow(QLabel("Final glyphs"), self.fina_re)

        self.doCursive = QCheckBox()
        self.doCursive.setChecked(True)

        layout.addRow(QLabel("Do cursive attachment?"), self.doCursive)
        form.setLayout(layout)
        return form

    def accept(self):
        glyphnames = self.project.font.keys()
        isol_re = self.isol_re.text()
        init_re = self.init_re.text()
        medi_re = self.medi_re.text()
        fina_re = self.fina_re.text()

        init_class = []
        medi_class = []
        fina_class = []
        init_rules = fontFeatures.Routine(name="Init")
        medi_rules = fontFeatures.Routine(name="Medi")
        fina_rules = fontFeatures.Routine(name="Fina")
        # We know these are valid REs
        arabic_glyphs = [
            g
            for g in glyphnames
            if re.search(init_re, g) or re.search(medi_re, g) or re.search(fina_re, g)
        ]
        for g in glyphnames:
            m = re.search(isol_re, g)
            if not m:
                continue
            if m.groups():
                base_name = g.replace(m[1], "")
            else:
                base_name = g
            for g2 in arabic_glyphs:
                m = re.search(init_re, g2)
                if not m or not m.groups():
                    continue
                base_init = g2.replace(m[1], "")
                if base_init == base_name:
                    init_class.append(g2)
                    init_rules.addRule(fontFeatures.Substitution([[g]], [[g2]]))
                    break

            for g2 in arabic_glyphs:
                m = re.search(medi_re, g2)
                if not m or not m.groups():
                    continue
                base_medi = g2.replace(m[1], "")
                if base_medi == base_name:
                    medi_class.append(g2)
                    medi_rules.addRule(fontFeatures.Substitution([[g]], [[g2]]))
                    break

            for g2 in arabic_glyphs:
                m = re.search(fina_re, g2)
                if not m or not m.groups():
                    continue
                base_fina = g2.replace(m[1], "")
                if base_fina == base_name:
                    fina_class.append(g2)
                    fina_rules.addRule(fontFeatures.Substitution([[g]], [[g2]]))
                    break

        warnings = []
        if len(init_class) < 10 or len(init_class) > len(glyphnames) / 2:
            warnings.append(
                f"Init regexp '{init_re} matched a surprising number of glyphs ({len(init_class)})"
            )
        if len(medi_class) < 10 or len(medi_class) > len(glyphnames) / 2:
            warnings.append(
                f"Medi regexp '{medi_re} matched a surprising number of glyphs ({len(medi_class)})"
            )
        if len(fina_class) < 10 or len(fina_class) > len(glyphnames) / 2:
            warnings.append(
                f"Fina regexp '{fina_re} matched a surprising number of glyphs ({len(fina_class)})"
            )

        if len(warnings) and self.show_warnings(warnings) == QMessageBox.Cancel:
            return

        self.project.fontfeatures.routines.extend([init_rules, medi_rules, fina_rules])
        self.project.fontfeatures.addFeature("init", [init_rules])
        self.project.fontfeatures.addFeature("medi", [medi_rules])
        self.project.fontfeatures.addFeature("fina", [fina_rules])
        if not "init" in self.project.glyphclasses:
            self.project.glyphclasses["init"] = {
                "type": "automatic",
                "predicates": [
                    {"type": "name", "comparator": "matches", "value": init_re}
                ],
            }
        if not "medi" in self.project.glyphclasses:
            self.project.glyphclasses["medi"] = {
                "type": "automatic",
                "predicates": [
                    {"type": "name", "comparator": "matches", "value": medi_re}
                ],
            }
        if not "fina" in self.project.glyphclasses:
            self.project.glyphclasses["fina"] = {
                "type": "automatic",
                "predicates": [
                    {"type": "name", "comparator": "matches", "value": fina_re}
                ],
            }

        if self.doCursive.isChecked():
            exitdict = {}
            entrydict = {}
            for g in glyphnames:
                anchors = self.project.font[g].anchors
                if not anchors:
                    continue
                entry = [a for a in anchors if a.name == "entry"]
                exit = [a for a in anchors if a.name == "exit"]
                if len(entry):
                    entrydict[g] = (entry[0].x, entry[0].y)
                if len(exit):
                    exitdict[g] = (exit[0].x, exit[0].y)
            s = fontFeatures.Attachment(
                base_name="entry",
                mark_name="exit",
                bases=entrydict,
                marks=exitdict,
            )
            r = fontFeatures.Routine(name="CursiveAttachment", rules=[s])
            self.project.fontfeatures.routines.extend([r])
            self.project.fontfeatures.addFeature("curs", [r])

        return super().accept()

    def detect_naming_scheme(self):
        glyphnames = self.project.font.keys()
        schemas = {
            "Glyphs": {
                "isol": "-ar$",
                "init": "-ar(.init)$",
                "medi": "-ar(.medi)$",
                "fina": "-ar(.fina)",
            },
            "Qalmi": {
                "isol": "(u1)$",
                "init": "(i1)$",
                "medi": "(m1)$",
                "fina": "(f1)$",
            },
        }
        for schema_name, res in schemas.items():
            match_isols = len([g for g in glyphnames if re.search(res["isol"], g)])
            match_inits = len([g for g in glyphnames if re.search(res["init"], g)])
            match_medis = len([g for g in glyphnames if re.search(res["medi"], g)])
            match_finas = len([g for g in glyphnames if re.search(res["fina"], g)])
            if (
                match_isols > 1
                and match_inits > 1
                and match_medis > 1
                and match_finas > 1
            ):
                return schema_name, res
        return None, None

    def show_warnings(self, warnings):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)

        msg.setText("\n".join(warnings))
        msg.setWindowTitle("Arabic Positionals")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        return msg.exec_()
