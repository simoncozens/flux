from PyQt5.QtCore import Qt, pyqtSlot, QModelIndex, QAbstractTableModel, QItemSelectionModel, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QTreeView, QMenu,QComboBox, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QDialog, QTextEdit, QDialogButtonBox
import re
from glyphtools import get_glyph_metrics


PREDICATE_TYPES = {
  "Name": {"textbox": True, "comparator": False},
  "Is member of": {"textbox": False, "comparator": False},
  "Is category": {"textbox": False, "comparator": False},
  "width": {"textbox": True, "comparator": True},
  "height": {"textbox": True, "comparator": True},
  "depth": {"textbox": True, "comparator": True},
  "xMax": {"textbox": True, "comparator": True},
  "yMax": {"textbox": True, "comparator": True},
  "xMin": {"textbox": True, "comparator": True},
  "yMin": {"textbox": True, "comparator": True},
  "rise": {"textbox": True, "comparator": True},
  "Has anchor": {"textbox": True, "comparator": False}
}

class GlyphClassPredicate:
    def __init__(self, predicate_dict = {}):
        self.comparator = None
        self.combiner = None
        self.value = None
        self.metric = None
        if "type" in predicate_dict:
          self.type = predicate_dict["type"]
        if "comparator" in predicate_dict:
            self.comparator = predicate_dict["comparator"]
        if "value" in predicate_dict:
            self.value = predicate_dict["value"]
        if "metric" in predicate_dict: # Metric, really
            self.metric = predicate_dict["metric"]
        if "combiner" in predicate_dict:
            self.combiner = predicate_dict["combiner"]

    def test(self, glyphset, font, infocache):
        matches = []
        if self.type == "Name":
          # print(self.comparator, self.value)
          if self.comparator == "begins":
            matches = [x for x in glyphset if x.startswith(self.value)]
          elif self.comparator == "ends":
            matches = [x for x in glyphset if x.endswith(self.value)]
          elif self.comparator == "matches":
            try:
                matches = [x for x in glyphset if re.search(self.value,x)]
            except Exception as e:
                matches = []

        # XXX HasAnchor
        # XXX Is member of
        # XXX Is Category

        if self.metric:
          matches = []
          try:
            for g in glyphset:
              if g not in infocache:
                infocache[g] = { "metrics": get_glyph_metrics(font, g) }

              got = infocache[g]["metrics"][self.type]
              expected, comp = int(self.value), self.comparator
              if (comp == ">" and got > expected) or (comp == "<" and got < expected) or (comp == "=" and got == expected) or (comp == "<=" and got <= expected) or (comp == ">=" and got >= expected):
                  matches.append(g)
          except Exception as e:
            print(e)
            pass

        return matches

    def to_dict(self):
        d = { "type": self.type }
        if self.comparator:
          d["comparator"] = self.comparator
        if self.combiner:
          d["combiner"] = self.combiner
        if self.value is not None:
          d["value"] = self.value
        if self.metric:
          d["metric"] = self.metric
        return d

class GlyphClassPredicateTester:
    def __init__(self, project):
        self.project = project
        self.infocache = {}
        self.allGlyphs = self.project.font.keys()

    def test_all(self, predicates):
        matches = self.allGlyphs
        if len(predicates) > 0:
          matches = predicates[0].test(matches, self.project.font, self.infocache)
        for p in predicates[1:]:
          if p.combiner == "and":
            # Narrow down existing set
            matches = p.test(matches, self.project.font, self.infocache)
          else:
            thisPredicateMatches = p.test(self.allGlyphs, self.project.font, self.infocache)
            matches = set(matches) | set(thisPredicateMatches)
        return matches

class GlyphClassPredicateRow(QHBoxLayout):
    changed = pyqtSignal()

    def __init__(self, editor, predicate = None):
        super(QHBoxLayout, self).__init__()
        # print("Initializing with ", arguments)
        self.editor = editor
        self.project = editor.project
        self.matches = []
        self.predicate = predicate
        self.predicateType = QComboBox()
        for n in PREDICATE_TYPES.keys():
          self.predicateType.addItem(n)
        self.predicateType.currentIndexChanged.connect(self.maybeChangeType)
        self.combiner = QComboBox()
        self.combiner.addItem("and")
        self.combiner.addItem("or")
        self.combiner.currentIndexChanged.connect(self.changed.emit)
        self.addWidget(self.combiner)
        self.addWidget(QLabel("Glyph"))
        self.addWidget(self.predicateType)
        self.changed.connect(self.serialize)
        self.changed.connect(lambda :self.editor.changed.emit())
        self.reset()

    def maybeChangeType(self):
      if self.predicateType.currentText() != self.predicate.type:
        self.predicate.type = self.predicateType.currentText()
        self.reset()

    def reset(self): # Call this when the type changes
        for i in reversed(range(3,self.count())): # We keep the combo boxes
          if self.itemAt(i).widget():
            self.itemAt(i).widget().setParent(None)

        typeIx = self.predicateType.findText(self.predicate.type)
        if typeIx != 1:
          self.predicateType.setCurrentIndex(typeIx)
        # print(self.arguments["type"])
        if self.predicate.type == "Name":
          self.nameCB = QComboBox()
          self.nameCB.addItems(["begins","ends","matches"])
          if self.predicate.comparator:
            ix = self.nameCB.findText(self.predicate.comparator)
            if ix != 1:
              self.nameCB.setCurrentIndex(ix)
          self.addWidget(self.nameCB)
          self.nameCB.currentIndexChanged.connect(self.changed.emit)

        if self.predicate.type == "Is category":
          self.categoryCB = QComboBox()
          self.categoryCB.addItems(["base","ligature","mark","component"])
          if self.arguments.value:
            ix = self.categoryCB.findText(self.predicate.value)
            if ix != 1:
              self.categoryCB.setCurrentIndex(ix)

          self.addWidget(self.categoryCB)
          self.categoryCB.currentIndexChanged.connect(self.changed.emit)

        if PREDICATE_TYPES[self.predicate.type]["comparator"]:
          self.comparator = QComboBox()
          self.comparator.addItems(["<","<=","=", ">=", ">"])
          if self.predicate.comparator:
            ix = self.comparator.findText(self.predicate.comparator)
            if ix != 1:
              self.comparator.setCurrentIndex(ix)
          self.comparator.currentIndexChanged.connect(self.changed.emit)
          self.addWidget(self.comparator)

        if PREDICATE_TYPES[self.predicate.type]["textbox"]:
          self.textBox = QLineEdit()
          if self.predicate.value:
            self.textBox.setText(self.predicate.value)
          elif PREDICATE_TYPES[self.predicate.type]["comparator"]:
            self.textBox.setText("200")
          self.textBox.textChanged.connect(self.changed.emit)
          self.addWidget(self.textBox)
        self.addStretch(999)
        self.plus = QPushButton("+")
        self.addWidget(self.plus)
        self.plus.clicked.connect(self.editor.addRow)
        self.minus = QPushButton("-")
        self.addWidget(self.minus)
        self.changed.emit()

    def serialize(self):
        self.predicate = GlyphClassPredicate()
        self.predicate.type = self.predicateType.currentText()
        self.predicate.combiner = self.combiner.currentText()
        if PREDICATE_TYPES[self.predicate.type]["textbox"]:
          self.predicate.value = self.textBox.text()
        if self.predicate.type == "Name":
          self.predicate.comparator = self.nameCB.currentText()
        elif self.predicate.type == "Is member of":
          #self.predicate.class = self.classCB.currentText()
          pass
        elif self.predicate.type == "Has anchor":
          #self.predicate.anchor = self.anchorCB.currentText()
          pass
        elif self.predicate.type == "Is category":
          self.predicate.category = self.categoryCB.currentText()
          pass

        if PREDICATE_TYPES[self.predicate.type]["comparator"]:
          self.predicate.metric = self.predicate.type
          self.predicate.comparator = self.comparator.currentText()
        # print(self.arguments)

class AutomatedGlyphClassDialog(QDialog):
  def __init__(self, font, predicates = []):
    super(QDialog, self).__init__()
    self.font = font
    v_box_1 = QVBoxLayout()
    self.gpe = GlyphClassPredicateEditor(font, predicates)
    v_box_1.addLayout(self.gpe)
    self.qte = QTextEdit()
    v_box_1.addWidget(self.qte)
    buttons = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
        Qt.Horizontal, self)
    buttons.accepted.connect(self.accept)
    buttons.rejected.connect(self.reject)
    v_box_1.addWidget(buttons)
    self.setLayout(v_box_1)
    self.gpe.changed.connect(self.update)
    self.update()

  def update(self):
    self.qte.setText(" ".join(sorted(self.gpe.matches)))

  def getPredicateRows(self):
    return self.gpe.predicateRows

  @staticmethod
  def editDefinition(project, predicates = []):
      dialog = AutomatedGlyphClassDialog(project, [ GlyphClassPredicate(p) for p in predicates])
      result = dialog.exec_()
      predicaterows = dialog.getPredicateRows()
      for x in predicaterows:
        x.serialize()
      predicates = [ x.predicate.to_dict() for x in predicaterows ]
      print(predicates)
      return (predicates, result == QDialog.Accepted)

class GlyphClassPredicateEditor(QVBoxLayout):
    changed = pyqtSignal()

    def __init__(self, project, existingpredicates = []):
        super(QVBoxLayout, self).__init__()
        self.project = project
        predicateItems = []
        if len(existingpredicates) == 0:
          predicateItems.append(GlyphClassPredicateRow(self, GlyphClassPredicate({"type": "Name"})))
        for p in existingpredicates:
          predicateItems.append(GlyphClassPredicateRow(self, p))
        for p in predicateItems:
          self.addLayout(p)
        predicateItems[-1].minus.setEnabled(False)
        predicateItems[0].combiner.hide()
        self.matches = []
        self.tester = GlyphClassPredicateTester(self.project)
        self.changed.connect(self.testAll)
        self.testAll()

    def addRow(self):
        self.addLayout(GlyphClassPredicateRow(self, GlyphClassPredicate({"type": "Name"})))

    def testAll(self):
        self.matches = self.tester.test_all([x.predicate for x in self.predicateRows])

    @property
    def predicateRows(self):
      return [self.itemAt(i) for i in range(self.count())]
