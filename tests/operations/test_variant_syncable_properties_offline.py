#
#   test_variant_syncable_properties_offline.py
#
#   Offline coverage for issue #358 without importing flexicon (no LCM on Linux CI).
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
VARIANT_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "VariantOperations.py"


def test_get_syncable_properties_emits_show_complex_forms_in_rs():
    source = VARIANT_OPS.read_text(encoding="utf-8")
    assert 'props["show_complex_forms_in_rs"]' in source
    assert "ShowComplexFormsInRS" in source
    gsp = re.search(
        r"def GetSyncableProperties\(.*?(?=\n    def |\nclass |\Z)",
        source,
        re.DOTALL,
    )
    assert gsp is not None
    body = gsp.group(0)
    assert 'hasattr(item, "ShowComplexFormsIn")' not in body
    assert 'props["ShowComplexFormsIn"]' not in body


def test_duplicate_copies_show_complex_forms_in_rs():
    source = VARIANT_OPS.read_text(encoding="utf-8")
    dup = re.search(
        r"def Duplicate\(.*?(?=\n    def |\n    # ==========|\Z)",
        source,
        re.DOTALL,
    )
    assert dup is not None
    body = dup.group(0)
    assert "ShowComplexFormsInRS.Add" in body
    assert 'hasattr(source, "ShowComplexFormsIn")' not in body
