from fontFeatures.feeLib.IMatra import IMatra as IMatra_FF
from PyQt5.QtWidgets import QLabel, QDialog, QLineEdit, QGroupBox, QCompleter, QFormLayout, QComboBox
from Flux.Plugins import FluxPlugin
from Flux.UI.qglyphname import QGlyphName


plugin_name = "IMatra Substitution"

class Dialog(FluxPlugin):
    def createForm(self):
        form = QGroupBox("IMatra parameters")
        layout = QFormLayout()

        self.consonant_edit = QGlyphName(self.project, multiple=True, allow_classes=True)
        self.base_matra = QGlyphName(self.project)
        self.variants_edit = QGlyphName(self.project, multiple=True, allow_classes=True)

        layout.addRow(QLabel("Consonants"), self.consonant_edit)
        layout.addRow(QLabel("Base I-matra glyph"), self.base_matra)
        layout.addRow(QLabel("I-matra variants"), self.variants_edit)
        form.setLayout(layout)
        return form

    def accept(self):
        consonants = self.glyphSelector(self.consonant_edit.text())
        base_matra = self.glyphSelector(self.base_matra.text())
        variants = self.glyphSelector(self.variants_edit.text())
        # Ideally we would serialize this routine as an automatic
        # one, but for now let's reify it and return.
        routines = IMatra_FF.action(self.feeparser, consonants, base_matra, variants)
        self.project.fontfeatures.routines.extend(routines)
        routines[0].name = "IMatra"
        print(routines)
        return super().accept()
