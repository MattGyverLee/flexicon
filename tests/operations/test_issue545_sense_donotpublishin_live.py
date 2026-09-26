#
#   test_issue545_sense_donotpublishin_live.py
#
#   Live coverage for issue #545: LexSenseOperations.GetDoNotPublishIn /
#   AddDoNotPublishIn / RemoveDoNotPublishIn, and the default that new
#   senses are publishable in every publication.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError
from flexicon.code.Shared.string_utils import best_analysis_text


pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_issue545_"


def _excluded_guids(sense):
    return {str(pub.Guid) for pub in sense.DoNotPublishInRC}


def _publications(project):
    pubs = list(project.Publications.GetAll())
    if not pubs:
        pytest.skip("Target sandbox has no publications to verify")
    return pubs


def _reread_sense(project, lexeme):
    entry = project.LexEntry.Find(lexeme)
    assert entry is not None, "Created entry did not round-trip through Find()"
    senses = list(entry.SensesOS)
    assert len(senses) == 1
    return entry, senses[0]


class TestIssue545SenseDoNotPublishIn:
    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_add_and_remove_by_name_object_and_hvo_round_trip(self, target_sandbox):
        pubs = _publications(target_sandbox)
        pub = pubs[0]
        pub_name = best_analysis_text(pub.Name)
        pub_guid = str(pub.Guid)

        lexeme = f"{TEST_PREFIX}roundtrip"
        entry = target_sandbox.LexEntry.Create(lexeme, create_blank_sense=False)
        try:
            target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}gloss")
            _, sense = _reread_sense(target_sandbox, lexeme)

            # Pre-state: a new sense is excluded from nothing.
            assert _excluded_guids(sense) == set()
            assert target_sandbox.Senses.GetDoNotPublishIn(sense) == []

            # Add by name; re-read from the LCM.
            target_sandbox.Senses.AddDoNotPublishIn(sense, pub_name)
            _, sense = _reread_sense(target_sandbox, lexeme)
            assert _excluded_guids(sense) == {pub_guid}
            assert target_sandbox.Senses.GetDoNotPublishIn(sense.Hvo) == [pub_name]

            # Adding again by object is a no-op, not a duplicate.
            target_sandbox.Senses.AddDoNotPublishIn(sense, pub)
            _, sense = _reread_sense(target_sandbox, lexeme)
            assert _excluded_guids(sense) == {pub_guid}

            # Remove by HVO + object; re-read from the LCM.
            target_sandbox.Senses.RemoveDoNotPublishIn(sense.Hvo, pub)
            _, sense = _reread_sense(target_sandbox, lexeme)
            assert _excluded_guids(sense) == set()

            # Removing again by name is a no-op.
            target_sandbox.Senses.RemoveDoNotPublishIn(sense, pub_name)
            _, sense = _reread_sense(target_sandbox, lexeme)
            assert _excluded_guids(sense) == set()
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_unknown_publication_name_raises_parameter_error(self, target_sandbox):
        _publications(target_sandbox)
        lexeme = f"{TEST_PREFIX}unknown_pub"
        entry = target_sandbox.LexEntry.Create(lexeme, create_blank_sense=False)
        try:
            sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}gloss")
            with pytest.raises(FP_ParameterError):
                target_sandbox.Senses.AddDoNotPublishIn(sense, f"{TEST_PREFIX}no_such_pub")
            with pytest.raises(FP_ParameterError):
                target_sandbox.Senses.RemoveDoNotPublishIn(sense, f"{TEST_PREFIX}no_such_pub")
            _, sense = _reread_sense(target_sandbox, lexeme)
            assert _excluded_guids(sense) == set()
        finally:
            target_sandbox.LexEntry.Delete(entry)
