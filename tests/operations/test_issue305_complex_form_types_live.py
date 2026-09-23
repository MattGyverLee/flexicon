#
#   test_issue305_complex_form_types_live.py
#
#   Live read-only coverage for issue #305 on Sena 3.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def test_get_all_complex_form_types_non_empty(sena3_sandbox):
    project = sena3_sandbox
    types = list(project.LexEntry.GetAllComplexFormTypes())
    assert len(types) >= 1


def test_find_complex_form_type_composto(sena3_sandbox):
    project = sena3_sandbox
    cf_type = project.LexEntry.FindComplexFormType("Composto")
    assert cf_type is not None
    name = project.PossibilityLists.GetItemName(cf_type)
    assert name
