from Flux.UI.featurelist import FeatureListModel
from Flux.UI.lookuplist import LookupListModel
from Flux.project import FluxProject
from fontFeatures import FontFeatures, Routine, Substitution

pytest_plugins = ("pytest-qt",)

def test_featurelist(qtmodeltester):
    proj = FluxProject()
    proj.fontfeatures = FontFeatures()
    r1 = Routine(name="routine1")
    r2 = Routine(name="routine2")
    proj.fontfeatures.features["test"] = [r1, r2]

    proj  = FluxProject("Hind.fluxml")

    model = FeatureListModel(proj)

    root = model.index(-1,-1)
    assert(model.describeIndex(root) == "root of tree")
    feature1 = model.index(0,0)
    assert(model.describeIndex(feature1) == "feature at row 0")
    child1 = model.index(0,0,feature1)
    assert(child1.parent() == feature1)
    assert(model.index(0,0,feature1) == model.index(0,0,feature1))
    # import code; code.interact(local=locals())
    qtmodeltester.check(model, force_py=True)
    qtmodeltester.check(model)

def test_lookuplist(qtmodeltester):
    proj  = FluxProject("Hind.fluxml")
    # proj = FluxProject()
    # proj.fontfeatures = FontFeatures()
    # r1 = Routine(name="routine1")
    # r1.addRule(Substitution([["a"]], [["b"]]))
    # r1.addRule(Substitution([["c"]], [["d"]]))
    # r2 = Routine(name="routine2")
    # r2.addRule(Substitution([["e"]], [["f"]]))
    # proj.fontfeatures.routines = [r1, r2]

    model = LookupListModel(proj)
    qtmodeltester.check(model, force_py=True)
    qtmodeltester.check(model)
