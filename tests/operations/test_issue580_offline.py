#
#   test_issue580_offline.py
#
#   Offline ratchet for issue #580: POSOperations / AllomorphOperations /
#   MorphRuleOperations / InflectionFeatureOperations wrappers for stem
#   names, inflection-class subclasses, affix-template reordering, and
#   inflection-class abbreviations.
#
#   Source-text assertions only -- no SIL/clr import, so these run in any
#   environment (pattern: test_issue467_morphrule_owner_cast_offline.py).
#   The behavioral logic is additionally smoke-tested against the real
#   module files with stubbed LCM dependencies (see the issue #580 PR).
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
POS_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "POSOperations.py"
ALLO_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "AllomorphOperations.py"
RULE_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "MorphRuleOperations.py"
INFL_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "InflectionFeatureOperations.py"
POS_PYI = REPO_ROOT / "flexicon" / "code" / "Grammar" / "POSOperations.pyi"
ALLO_PYI = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "AllomorphOperations.pyi"
RULE_PYI = REPO_ROOT / "flexicon" / "code" / "Grammar" / "MorphRuleOperations.pyi"
INFL_PYI = REPO_ROOT / "flexicon" / "code" / "Grammar" / "InflectionFeatureOperations.pyi"


def _block(path, start_marker, end_marker):
    text = path.read_text(encoding="utf-8")
    start = text.index(start_marker)
    return text[start : text.index(end_marker, start)]


# ---------- POSOperations: stem names ----------

def test_580_get_stem_names_reads_stem_names_oc():
    block = _block(POS_OPS, "def GetStemNames(", "def GetStemNameText(")
    assert "StemNamesOC" in block
    assert "@OperationsMethod" in block
    assert "Example:" in block


def test_580_get_stem_name_text_normalizes_placeholder():
    block = _block(POS_OPS, "def GetStemNameText(", "def GetStemNameAbbreviation(")
    assert "get_String(wsHandle)" in block
    assert "_NormalizeMultiString" in block
    assert '"***"' in block  # docstring promises never "***"


def test_580_get_stem_name_region_count_zero_when_absent():
    block = _block(POS_OPS, "def GetStemNameRegionCount(", "def __ResolveStemName(")
    assert "RegionsOC" in block
    assert "return regions.Count if regions else 0" in block


def test_580_get_inflection_classes_recursive_walks_subclasses():
    block = _block(POS_OPS, "def GetInflectionClasses(", "def GetStemNames(")
    assert "recursive" in block
    assert "SubclassesOC" in block
    assert "__CollectInflectionClassesRecursive" in block
    # default stays non-recursive (existing behavior preserved)
    assert "recursive=False" in block


# ---------- AllomorphOperations: stem name read/write ----------

def test_580_allo_get_stem_name_never_raises_wrong_class():
    block = _block(ALLO_OPS, "def GetStemName(", "def SetStemName(")
    assert "StemNameRA" in block
    assert 'getattr(allomorph, "ClassName", None) != "MoStemAllomorph"' in block
    assert "return None" in block


def test_580_allo_set_stem_name_validates_pos_ownership():
    block = _block(ALLO_OPS, "def SetStemName(", "# --- Private Helper Methods ---")
    assert "FP_ParameterError" in block
    assert "__GetAllomorphPos" in block
    assert "__GetStemNamePos" in block
    assert "__PosMatchesOrIsAncestor" in block
    assert "_EnsureWriteEnabled()" in block
    assert "_TransactionCM" in block
    # None clears without a POS check
    assert "stem_name_or_hvo_or_None is not None" in block
    # ancestor walk exists
    helper = _block(ALLO_OPS, "def __PosMatchesOrIsAncestor(", "def __WSHandle(")
    assert '"Owner"' in helper or "'Owner'" in helper or "Owner" in helper


def test_580_allo_set_stem_name_rejects_affix_allomorph():
    block = _block(ALLO_OPS, "def SetStemName(", "# --- Private Helper Methods ---")
    assert "requires a MoStemAllomorph" in block


# ---------- MorphRuleOperations: template reordering ----------

def test_580_move_affix_template_uses_moveto_not_clear():
    block = _block(RULE_OPS, "def MoveAffixTemplate(", "def ReorderAffixTemplates(")
    assert "MoveTo(" in block
    assert ".Clear(" not in block
    assert "_EnsureWriteEnabled()" in block
    assert "_TransactionCM" in block
    assert "FP_ParameterError" in block


def test_580_reorder_affix_templates_uses_apply_sequence_order():
    block = _block(RULE_OPS, "def ReorderAffixTemplates(", "# ========== DELETION ==========")
    assert "_ApplySequenceOrder" in block
    assert "_TransactionCM" in block


# ---------- InflectionFeatureOperations: abbreviation ----------

def test_580_infl_class_abbreviation_get_set():
    get_block = _block(INFL_OPS, "def InflectionClassGetAbbreviation(",
                       "def InflectionClassSetAbbreviation(")
    assert "Abbreviation" in get_block
    assert "_NormalizeMultiString" in get_block
    set_block = _block(INFL_OPS, "def InflectionClassSetAbbreviation(",
                       "# ========================================================================")
    assert "Abbreviation.set_String" in set_block
    assert "_EnsureWriteEnabled()" in set_block


# ---------- .pyi stubs ----------

def test_580_pyi_stubs_cover_new_methods():
    pos_pyi = POS_PYI.read_text(encoding="utf-8")
    for name in ("GetInflectionClasses", "GetStemNames", "GetStemNameText",
                 "GetStemNameAbbreviation", "GetStemNameRegionCount"):
        assert f"def {name}(" in pos_pyi, name
    assert "recursive" in pos_pyi

    allo_pyi = ALLO_PYI.read_text(encoding="utf-8")
    assert "def GetStemName(" in allo_pyi
    assert "def SetStemName(" in allo_pyi

    rule_pyi = RULE_PYI.read_text(encoding="utf-8")
    assert "def MoveAffixTemplate(" in rule_pyi
    assert "def ReorderAffixTemplates(" in rule_pyi

    infl_pyi = INFL_PYI.read_text(encoding="utf-8")
    assert "def InflectionClassGetAbbreviation(" in infl_pyi
    assert "def InflectionClassSetAbbreviation(" in infl_pyi
