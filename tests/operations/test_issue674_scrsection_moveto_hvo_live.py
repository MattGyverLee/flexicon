#
#   test_issue674_scrsection_moveto_hvo_live.py
#
#   Live verification for issue #674 MoveTo same-book HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def _book_with_two_sections(sandbox):
    for book in sandbox.ScrBooks.GetAll():
        sections = list(sandbox.ScrSections.GetAll(book))
        if len(sections) >= 2:
            return book, sections
    return None, None


class TestIssue674ScrSectionMoveToHvoLive:
    """Same-book MoveTo must run when section is passed as raw Object(hvo)."""

    @pytest.mark.live_phase("ScrSectionOperations", "modify")
    def test_move_to_reorders_via_raw_section_hvo(self, sena3_sandbox):
        sandbox = sena3_sandbox
        book, sections = _book_with_two_sections(sandbox)
        if book is None:
            pytest.skip("sandbox has no Scripture book with two sections")

        first, second = sections[0], sections[1]
        before_hvos = [s.Hvo for s in sandbox.ScrSections.GetAll(book)]
        assert before_hvos.index(second.Hvo) == before_hvos.index(first.Hvo) + 1

        second_raw = sandbox.Object(second.Hvo)
        try:
            sandbox.ScrSections.MoveTo(second_raw, book, 0)
            after_hvos = [s.Hvo for s in sandbox.ScrSections.GetAll(book)]
            assert after_hvos.index(second.Hvo) == 0
            assert after_hvos.index(first.Hvo) == 1
        finally:
            sandbox.ScrSections.MoveTo(second, book, before_hvos.index(second.Hvo))
