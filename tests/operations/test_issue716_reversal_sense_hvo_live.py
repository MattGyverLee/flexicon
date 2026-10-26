#
#   test_issue716_reversal_sense_hvo_live.py
#
#   Live verification for issue #716 ReversalIndexEntry SensesRS HVO membership.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_716_"


def _first_analysis(project):
    ops = project.WritingSystems
    ws = next(iter(ops.GetAnalysis()))
    return int(ws.Handle), ops.GetLanguageTag(ws)


def _free_up_index(project, tag):
    rev = project.ReversalIndexes
    existing = rev.FindByWritingSystem(tag)
    if existing is not None:
        rev.Delete(existing)


def test_issue716_remove_sense_after_hvo_refetch(target_sandbox):
    """RemoveSense unlinks sense when caller holds Object(hvo) view."""
    project = target_sandbox
    handle, tag = _first_analysis(project)
    _free_up_index(project, tag)
    index = project.ReversalIndexes.Create(f"{TEST_PREFIX}idx", handle)
    entry = project.ReversalEntries.Create(index, f"{TEST_PREFIX}form")
    lex_entry = project.LexEntry.GetAll()[0]
    sense = list(lex_entry.SensesOS)[0]
    try:
        project.ReversalEntries.AddSense(entry, sense)
        bare_sense = project.Object(sense.Hvo)
        project.ReversalEntries.RemoveSense(entry, bare_sense)
        linked = list(project.ReversalEntries.GetSenses(entry))
        assert all(s.Hvo != sense.Hvo for s in linked)
    finally:
        project.ReversalEntries.Delete(entry)
        project.ReversalIndexes.Delete(index)
