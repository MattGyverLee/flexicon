#
#   test_issue874_morph_adjacency_sync_live.py
#
#   Live gate for issue #874 Adjacency sync round-trip.
#
#   Copyright 2026
#

import pytest

from flexicon.code.lcm_casting import _get_factory_for_class

TEST_PREFIX = "TEST_"


@pytest.mark.requires_live_project
class TestIssue874Live:
    def test_adhoc_prohib_adjacency_roundtrip(self, target_sandbox):
        p = target_sandbox
        assert p.writeEnabled is True
        morph_data = p.lp.MorphologicalDataOA
        assert morph_data is not None, "Target has no MorphologicalDataOA"

        ops = p.MorphRules
        factory = _get_factory_for_class("MoAdhocProhibGr", p.project)
        assert factory is not None, "MoAdhocProhibGr factory missing on this LCM"

        p1 = p2 = None
        try:
            with ops._TransactionCM("TEST_874 seed adhoc prohibitions"):
                p1 = factory.Create()
                p2 = factory.Create()
                morph_data.AdhocCoProhibitionsOC.Add(p1)
                morph_data.AdhocCoProhibitionsOC.Add(p2)

            adj_val = 1
            p1.Adjacency = adj_val

            props = ops.GetSyncableProperties(p1)
            assert props.get("Adjacency") == adj_val, props

            assert int(p2.Adjacency) != adj_val
            ops.ApplySyncableProperties(p2, {"Adjacency": props["Adjacency"]})
            assert int(p2.Adjacency) == adj_val
        finally:
            try:
                with ops._TransactionCM("TEST_874 cleanup adhoc prohibitions"):
                    for prohib in (p1, p2):
                        if prohib is not None and prohib in morph_data.AdhocCoProhibitionsOC:
                            morph_data.AdhocCoProhibitionsOC.Remove(prohib)
            except Exception:
                pass
