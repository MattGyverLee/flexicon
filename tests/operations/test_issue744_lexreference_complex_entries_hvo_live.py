#
#   test_issue744_lexreference_complex_entries_hvo_live.py
#
#   Live verification for issue #744 LexReferenceOperations complex-form getters.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_744_"


def _unique_entry_hvos(entries):
    return {e.Hvo for e in entries}


def test_issue744_get_complex_form_entries_unique_hvos(target_sandbox):
    """GetComplexFormEntries returns at most one row per entry HVO."""
    project = target_sandbox
    entries = list(project.LexEntry.GetAll())
    assert len(entries) >= 3, "Target needs at least 3 lex entries"
    component = entries[0]
    complex_a = entries[1]
    complex_b = entries[2]
    ref_type = project.LexReferences.FindType("Complex Forms")
    if ref_type is None:
        ref_type = project.LexReferences.CreateType(
            f"{TEST_PREFIX}ComplexForms", "Tree", reverse_name="Components"
        )
    ref = project.LexReferences.Create(ref_type, [complex_a, component, complex_b])
    try:
        results = project.LexReferences.GetComplexFormEntries(component)
        assert len(results) == len(_unique_entry_hvos(results))
        bare_component = project.Object(component.Hvo)
        results2 = project.LexReferences.GetComplexFormEntries(bare_component)
        assert len(results2) == len(_unique_entry_hvos(results2))
    finally:
        project.LexReferences.Delete(ref)


def test_issue744_get_component_entries_unique_hvos(target_sandbox):
    """GetComponentEntries returns at most one row per entry HVO."""
    project = target_sandbox
    entries = list(project.LexEntry.GetAll())
    assert len(entries) >= 3, "Target needs at least 3 lex entries"
    component_a = entries[0]
    component_b = entries[1]
    complex_entry = entries[2]
    ref_type = project.LexReferences.FindType("Complex Forms")
    if ref_type is None:
        ref_type = project.LexReferences.CreateType(
            f"{TEST_PREFIX}ComplexForms2", "Tree", reverse_name="Components"
        )
    ref = project.LexReferences.Create(
        ref_type, [complex_entry, component_a, component_b]
    )
    try:
        results = project.LexReferences.GetComponentEntries(complex_entry)
        assert len(results) == len(_unique_entry_hvos(results))
        bare_complex = project.Object(complex_entry.Hvo)
        results2 = project.LexReferences.GetComponentEntries(bare_complex)
        assert len(results2) == len(_unique_entry_hvos(results2))
    finally:
        project.LexReferences.Delete(ref)
