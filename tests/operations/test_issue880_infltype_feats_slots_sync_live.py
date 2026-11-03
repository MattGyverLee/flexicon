#
#   test_issue880_infltype_feats_slots_sync_live.py
#
#   Issue #880: VariantOperations LexEntryInflType InflFeatsOA / SlotsRC sync.
#   Verified on target_sandbox (tempdir copy only).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

TEST_PREFIX = "TEST_880_"


def _infl_types(project):
    from flexicon.code.lcm_casting import cast_to_concrete

    found = []
    for raw in project.Variants.GetAllTypes():
        t = cast_to_concrete(raw)
        if getattr(t, "ClassName", None) == "LexEntryInflType":
            found.append(t)
    return found


@pytest.mark.requires_live_project
class TestIssue880InflTypeFeatsSlotsSyncLive:

    def test_lex_entry_infl_type_slots_rc_roundtrip(self, target_sandbox):
        p = target_sandbox
        types = _infl_types(p)
        if len(types) < 2:
            pytest.skip("need two LexEntryInflType rows in VariantEntryTypesOA")

        src, dst = types[0], types[1]
        src_slots = list(src.SlotsRC)
        if not src_slots:
            pytest.skip("source LexEntryInflType has empty SlotsRC")

        props = p.Variants.GetTypeSyncableProperties(src)
        assert props.get("slots_rc") == [str(s.Guid) for s in src_slots], props

        p.Variants.ApplyTypeSyncableProperties(dst, {"slots_rc": props["slots_rc"]})
        dst_guids = [str(s.Guid) for s in dst.SlotsRC]
        assert dst_guids == props["slots_rc"], dst_guids

    def test_lex_entry_infl_type_infl_feats_guid_roundtrip(self, target_sandbox):
        p = target_sandbox
        types = _infl_types(p)
        with_feats = [t for t in types if t.InflFeatsOA is not None]
        if len(with_feats) < 2:
            pytest.skip("need two LexEntryInflType rows with InflFeatsOA")

        src, dst = with_feats[0], with_feats[1]
        props = p.Variants.GetTypeSyncableProperties(src)
        if "InflFeatsGuid" not in props:
            pytest.skip("source LexEntryInflType has no InflFeatsOA payload")

        guid_key = props["InflFeatsGuid"]
        p.Variants.ApplyTypeSyncableProperties(
            dst,
            {
                "InflFeats": props.get("InflFeats") or {},
                "InflFeatsGuid": guid_key,
            },
        )
        assert dst.InflFeatsOA is not None
        assert str(dst.InflFeatsOA.Guid) == guid_key
