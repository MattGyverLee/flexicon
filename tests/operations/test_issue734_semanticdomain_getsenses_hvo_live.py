#
#   test_issue734_semanticdomain_getsenses_hvo_live.py
#
#   Live gate for issue #734 GetSensesInDomain HVO membership.
#
#   Copyright 2026
#

import sys

import pytest

pytestmark = pytest.mark.requires_live_project


def _open_sena3_readonly():
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception:
        return None
    project = FLExProject()
    try:
        project.OpenProject("Sena 3", writeEnabled=False)
        return project
    except Exception:
        return None


@pytest.fixture(scope="module")
def sena3_project():
    if "SIL.LCModel" not in sys.modules:
        pytest.importorskip("SIL.LCModel")
    project = _open_sena3_readonly()
    if project is None:
        pytest.skip("Sena 3 not available for live #734 gate")
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


class TestIssue734GetSensesInDomainHvo:
    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_getsenses_matches_getsensecount_with_refetched_domain(self, sena3_project):
        """Re-fetch domain by HVO; list length must match GetSenseCount."""
        project = sena3_project
        checked = 0
        for domain in project.SemanticDomains.GetAll():
            count = project.SemanticDomains.GetSenseCount(domain)
            if count == 0:
                continue
            refetched = project.Object(domain.Hvo)
            senses = project.SemanticDomains.GetSensesInDomain(refetched)
            assert len(senses) == count, (
                f"GetSensesInDomain(HVO {domain.Hvo}) returned {len(senses)} "
                f"senses but GetSenseCount returned {count}"
            )
            checked += 1
            if checked >= 5:
                break
        if checked == 0:
            pytest.skip("No populated semantic domains in Sena 3 sample")
