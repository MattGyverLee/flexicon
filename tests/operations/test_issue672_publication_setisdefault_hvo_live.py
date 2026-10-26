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
    def test_set_is_default_raw_object_view(self, target_sandbox):
        pubs = list(target_sandbox.Publications.GetAll())
        if len(pubs) < 2:
            pytest.skip("Need at least two publications")

        default_before = next(
            (p for p in pubs if target_sandbox.Publications.GetIsDefault(p)),
            pubs[0],
        )
        non_default = next(
            (p for p in pubs if p.Hvo != default_before.Hvo),
            None,
        )
        if non_default is None:
            pytest.skip("Could not find a non-default publication")

        try:
            raw = target_sandbox.Object(non_default.Hvo)
            target_sandbox.Publications.SetIsDefault(raw, True)
            order = [p.Hvo for p in target_sandbox.lexDB.PublicationTypesOA.PossibilitiesOS]
            assert order[0] == non_default.Hvo
        finally:
            target_sandbox.Publications.SetIsDefault(default_before, True)
