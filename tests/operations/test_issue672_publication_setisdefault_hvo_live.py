#
#   test_issue672_publication_setisdefault_hvo_live.py
#
#   Live verification for issue #672 SetIsDefault HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


class TestIssue672PublicationSetIsDefaultHvoLive:
    """SetIsDefault must reorder when publication_or_hvo is raw Object(hvo)."""

    @pytest.mark.live_phase("PublicationOperations", "write")
    def test_set_is_default_raw_object_view(self, sena3_sandbox):
        if len(list(sena3_sandbox.Publications.GetAll())) < 2:
            # Sena 3 ships with a single publication; add a TEST_ one.
            sena3_sandbox.Publications.Create("TEST_672_second_pub")
        pubs = list(sena3_sandbox.Publications.GetAll())
        assert len(pubs) >= 2

        default_before = next(
            (p for p in pubs if sena3_sandbox.Publications.GetIsDefault(p)),
            pubs[0],
        )
        non_default = next(
            (p for p in pubs if p.Hvo != default_before.Hvo),
            None,
        )
        assert non_default is not None

        try:
            raw = sena3_sandbox.Object(non_default.Hvo)
            sena3_sandbox.Publications.SetIsDefault(raw, True)
            order = [p.Hvo for p in sena3_sandbox.lexDB.PublicationTypesOA.PossibilitiesOS]
            assert order[0] == non_default.Hvo
        finally:
            sena3_sandbox.Publications.SetIsDefault(default_before, True)
