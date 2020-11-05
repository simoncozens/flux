import sys, os

if "RESOURCEPATH" in os.environ:
    sys.path = [os.path.join(os.environ['RESOURCEPATH'], 'lib', 'python3.8', 'lib-dynload')] + sys.path

import Flux.ucd

from Flux.project import FluxProject
from Flux.editor import FluxEditor
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
app.setApplicationName("Flux")
app.setOrganizationDomain("corvelsoftware.co.uk")
app.setOrganizationName("Corvel Software")
proj = None
if len(sys.argv) > 1:
    if sys.argv[1].endswith(".fluxml"):
        proj = FluxProject(sys.argv[1])
    else:
        proj = FluxProject.new(sys.argv[1])
f = FluxEditor(proj)
f.show()
sys.exit(app.exec_())
