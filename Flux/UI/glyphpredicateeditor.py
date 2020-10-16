from PyQt5.QtCore import Qt, pyqtSlot, QModelIndex, QAbstractTableModel, QItemSelectionModel, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QTreeView, QMenu,QComboBox, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QLabel, QDialog, QTextEdit, QDialogButtonBox
import qtawesome as qta
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

class GlyphClassPredicate(QHBoxLayout):
    changed = pyqtSignal()

    def __init__(self, editor, arguments = {}):
        super(QHBoxLayout, self).__init__()
        # print("Initializing with ", arguments)
        self.editor = editor
        self.project = editor.project
        self.matches = []
        self.allGlyphs = self.project.font.glyphs
        self.metrics = { g: get_glyph_metrics(self.project.font.font, g) for g in self.allGlyphs }
        self.arguments = arguments
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
      if self.predicateType.currentText() != self.arguments["type"]:
        self.arguments["type"] = self.predicateType.currentText()
        self.reset()


    def reset(self): # Call this when the type changes
        for i in reversed(range(3,self.count())): # We keep the combo boxes
          if self.itemAt(i).widget():
            self.itemAt(i).widget().setParent(None)

        typeIx = self.predicateType.findText(self.arguments["type"])
        if typeIx != 1:
          self.predicateType.setCurrentIndex(typeIx)
        # print(self.arguments["type"])
        if self.arguments["type"] == "Name":
          self.nameCB = QComboBox()
          self.nameCB.addItems(["begins","ends","matches"])
          if "comparator" in self.arguments:
            ix = self.nameCB.findText(self.arguments["comparator"])
            if ix != 1:
              self.nameCB.setCurrentIndex(ix)
          self.addWidget(self.nameCB)
          self.nameCB.currentIndexChanged.connect(self.changed.emit)

        if self.arguments["type"] == "Is category":
          self.categoryCB = QComboBox()
          self.categoryCB.addItems(["base","ligature","mark","component"])
          if "category" in self.arguments:
            ix = self.categoryCB.findText(self.arguments["category"])
            if ix != 1:
              self.categoryCB.setCurrentIndex(ix)

          self.addWidget(self.categoryCB)
          self.categoryCB.currentIndexChanged.connect(self.changed.emit)

        if PREDICATE_TYPES[self.arguments["type"]]["comparator"]:
          self.comparator = QComboBox()
          self.comparator.addItems(["<","<=","=", ">=", ">"])
          if "comparator" in self.arguments:
            ix = self.comparator.findText(self.arguments["comparator"])
            if ix != 1:
              self.comparator.setCurrentIndex(ix)
          self.comparator.currentIndexChanged.connect(self.changed.emit)
          self.addWidget(self.comparator)

        if PREDICATE_TYPES[self.arguments["type"]]["textbox"]:
          self.textBox = QLineEdit()
          if "value" in self.arguments:
            self.textBox.setText(self.arguments["value"])
          elif PREDICATE_TYPES[self.arguments["type"]]["comparator"]:
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
        self.arguments = {}
        self.arguments["type"] = self.predicateType.currentText()
        self.arguments["combiner"] = self.combiner.currentText()
        if PREDICATE_TYPES[self.arguments["type"]]["textbox"]:
          self.arguments["value"] = self.textBox.text()
        if self.arguments["type"] == "Name":
          self.arguments["comparator"] = self.nameCB.currentText()
        elif self.arguments["type"] == "Is member of":
          #self.arguments["class"] = self.classCB.currentText()
          pass
        elif self.arguments["type"] == "Has anchor":
          #self.arguments["anchor"] = self.anchorCB.currentText()
          pass
        elif self.arguments["type"] == "Is category":
          self.arguments["category"] = self.categoryCB.currentText()
          pass

        if PREDICATE_TYPES[self.arguments["type"]]["comparator"]:
          self.arguments["predicate"] = self.arguments["type"]
          self.arguments["comparator"] = self.comparator.currentText()
        # print(self.arguments)

    def test(self):
        a = self.arguments
        if a["type"] == "Name":
          # print(a["comparator"], a["value"])
          if a["comparator"] == "begins":
            self.matches = [x for x in self.allGlyphs if x.startswith(a["value"])]
          elif a["comparator"] == "ends":
            self.matches = [x for x in self.allGlyphs if x.endswith(a["value"])]
          elif a["comparator"] == "matches":
            self.matches = [x for x in self.allGlyphs if re.search(a["value"],x)]
        if "predicate" in a:
          self.matches = []
          try:
            for g in self.allGlyphs:
              got = self.metrics[g][a["predicate"]]
              expected, comp = int(a["value"]), a["comparator"]
              if (comp == ">" and got > expected) or (comp == "<" and got < expected) or (comp == "=" and got == expected) or (comp == "<=" and got <= expected) or (comp == ">=" and got >= expected):
                  self.matches.append(g)
          except Exception as e:
            print(e)
            pass
        # print(a)
        # print(self.matches)

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

  def getPredicates(self):
    return self.gpe.predicates

  @staticmethod
  def editDefinition(project, predicates = []):
      dialog = AutomatedGlyphClassDialog(project, predicates)
      result = dialog.exec_()
      predicates = dialog.getPredicates()
      for x in predicates:
        x.serialize()
      predicates = [ x.arguments for x in predicates ]
      return (predicates, result == QDialog.Accepted)

class GlyphClassPredicateEditor(QVBoxLayout):
    changed = pyqtSignal()

    def __init__(self, project, existingpredicates = []):
        super(QVBoxLayout, self).__init__()
        self.project = project
        predicateItems = []
        if len(existingpredicates) == 0:
          predicateItems.append(GlyphClassPredicate(self, {"type": "Name"}))
        for p in existingpredicates:
          predicateItems.append(GlyphClassPredicate(self, p))
        for p in predicateItems:
          self.addLayout(p)
        predicateItems[-1].minus.setEnabled(False)
        predicateItems[0].combiner.hide()
        self.matches = []
        self.changed.connect(self.testAll)
        self.testAll()

    def addRow(self):
        self.addLayout(GlyphClassPredicate(self, {"type": "Name"}))

    def testAll(self):
        self.matches = []
        for i in range(self.count()):
          p = self.itemAt(i)
          p.test()
          if i > 0:
            if p.arguments["combiner"] == "and":
              self.matches = set(self.matches) & set(p.matches)
            else:
              self.matches = set(self.matches) | set(p.matches)
          else:
            self.matches = p.matches

    @property
    def predicates(self):
      return [self.itemAt(i) for i in range(self.count())]
