#
#   test_issue619_reversal_ws_tag_live.py
#
#   Live write-path verification for issue #619: ReversalIndexOperations
#   .Create must store the language TAG in IReversalIndex.WritingSystem
#   whether the caller passes a handle (int) or a tag (str), and
#   FindByWritingSystem must find the index by either form. Every value
#   is re-read from the LCM after the write. Uses target_sandbox only.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def _first_analysis(project):
    ops = project.WritingSystems
    ws = next(iter(ops.GetAnalysis()))
    return int(ws.Handle), ops.GetLanguageTag(ws)


def _free_up(project, tag):
    """Delete any existing index for `tag` (sandbox copy only)."""
    rev = project.ReversalIndexes
    existing = rev.FindByWritingSystem(tag)
    if existing is not None:
        rev.Delete(existing)
    assert rev.FindByWritingSystem(tag) is None


def _reread_index(project, guid):
    """Re-query the index from the LCM repository by GUID (typed)."""
    for idx in project.ReversalIndexes.GetAll():
        if str(idx.Guid).lower() == str(guid).lower():
            return idx
    return None


def _stored_tags(project):
    return [str(i.WritingSystem) for i in project.ReversalIndexes.GetAll()]


class TestReversalCreateStoresTag:
    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_create_with_handle_stores_tag(self, target_sandbox):
        rev = target_sandbox.ReversalIndexes
        handle, tag = _first_analysis(target_sandbox)
        _free_up(target_sandbox, tag)
        pre = _stored_tags(target_sandbox)
        print(f"[PRE] handle={handle} tag={tag!r} stored={pre}")

        created = rev.Create(f"{TEST_PREFIX}by_handle", handle)
        guid = str(created.Guid)

        # Re-query from the LCM rather than trusting the returned object.
        reread = _reread_index(target_sandbox, guid)
        assert reread is not None
        stored = str(reread.WritingSystem)
        print(f"[POST] stored={stored!r} all={_stored_tags(target_sandbox)}")
        assert stored == tag
        assert stored != str(handle)
        assert not stored.isdigit()

        assert rev.FindByWritingSystem(tag) is not None
        assert rev.FindByWritingSystem(handle) is not None
        assert str(rev.FindByWritingSystem(handle).Guid) == guid
        assert rev.GetWritingSystem(reread) == tag

    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_create_with_tag_stores_tag(self, target_sandbox):
        rev = target_sandbox.ReversalIndexes
        handle, tag = _first_analysis(target_sandbox)
        _free_up(target_sandbox, tag)
        pre = _stored_tags(target_sandbox)
        print(f"[PRE] handle={handle} tag={tag!r} stored={pre}")

        created = rev.Create(f"{TEST_PREFIX}by_tag", tag)
        reread = _reread_index(target_sandbox, created.Guid)
        assert reread is not None
        stored = str(reread.WritingSystem)
        print(f"[POST] stored={stored!r} all={_stored_tags(target_sandbox)}")
        assert stored == tag

        assert str(rev.FindByWritingSystem(tag).Guid) == str(created.Guid)
        assert str(rev.FindByWritingSystem(handle).Guid) == str(created.Guid)

    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_duplicate_rejected_across_forms(self, target_sandbox):
        rev = target_sandbox.ReversalIndexes
        handle, tag = _first_analysis(target_sandbox)
        _free_up(target_sandbox, tag)
        rev.Create(f"{TEST_PREFIX}dup_first", handle)
        before = _stored_tags(target_sandbox)
        for arg in (tag, handle):
            with pytest.raises(FP_ParameterError):
                rev.Create(f"{TEST_PREFIX}dup_second", arg)
        assert _stored_tags(target_sandbox) == before

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "add")
    def test_entry_create_resolves_ws_from_index_without_explicit_ws(self, target_sandbox):
        """Downstream proof: with a tag stored, ReversalIndexEntryOperations
        .Create's own WSHandle(index.WritingSystem) fallback now resolves."""
        rev = target_sandbox.ReversalIndexes
        handle, tag = _first_analysis(target_sandbox)
        _free_up(target_sandbox, tag)
        index = rev.Create(f"{TEST_PREFIX}for_entry", handle)

        entry = target_sandbox.ReversalEntries.Create(index, f"{TEST_PREFIX}form")
        reread = target_sandbox.Object(str(entry.Guid))
        assert reread is not None
        form = target_sandbox.ReversalEntries.GetForm(reread, handle)
        print(f"[POST] entry form read back: {form!r}")
        assert form == f"{TEST_PREFIX}form"
