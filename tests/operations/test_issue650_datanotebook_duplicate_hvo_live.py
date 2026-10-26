#
#   test_issue650_datanotebook_duplicate_hvo_live.py
#
#   Live verification for issue #650 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

from tests.operations.test_datanotebook_duplicate import (
    TEST_PREFIX,
    _make_subrecord,
    _make_toplevel_record,
)

pytestmark = pytest.mark.requires_live_project


class TestIssue650DataNotebookDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("DataNotebookOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        notebook = target_sandbox.DataNotebook

        parent = _make_toplevel_record(
            target_sandbox, f"{TEST_PREFIX}650_parent"
        )
        s1 = _make_subrecord(target_sandbox, parent, f"{TEST_PREFIX}650_sub1")
        s2 = _make_subrecord(target_sandbox, parent, f"{TEST_PREFIX}650_sub2")

        before_toplevel = {
            r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
        }

        try:
            raw_mid = target_sandbox.Object(s1.Hvo)
            dup = notebook.Duplicate(raw_mid, insert_after=True)

            order = [r.Hvo for r in parent.SubRecordsOS]
            assert order.index(dup.Hvo) == order.index(s1.Hvo) + 1
            assert order.index(s2.Hvo) == order.index(dup.Hvo) + 1

            after_toplevel = {
                r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
            }
            assert len(after_toplevel - before_toplevel) == 0

            notebook.Delete(dup)
        finally:
            after_toplevel = {
                r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
            }
            stray_toplevel = after_toplevel - before_toplevel
            for hvo in stray_toplevel:
                try:
                    notebook.Delete(hvo)
                except Exception:
                    pass
            for sub in list(parent.SubRecordsOS):
                try:
                    notebook.Delete(sub)
                except Exception:
                    pass
            try:
                notebook.Delete(parent)
            except Exception:
                pass
