#
#   test_issue279_cast_registry_offline.py
#
#   Offline ratchets for issue #279: register four #270 remainder types in
#   lcm_casting._interface_cache.
#
#   Platform: Python 3.8+
#   Copyright 2025
#

from pathlib import Path


_LCM_CASTING = (
    Path(__file__).resolve().parents[2] / "flexicon" / "code" / "lcm_casting.py"
)

_REMAINDER_CLASSNAMES = (
    "LexEntryInflType",
    "CmCustomItem",
    "ChkTerm",
    "ConstituentChartCellPart",
)


class TestIssue279CastRegistryOffline:
    def test_interface_cache_registers_remainder_classnames(self):
        src = _LCM_CASTING.read_text(encoding="utf-8")
        for class_name in _REMAINDER_CLASSNAMES:
            assert f'("{class_name}",' in src or (
                f'_interface_cache["{class_name}"]' in src
            ), (
                f"lcm_casting must register {class_name!r} for cast_to_concrete "
                "(issue #279 / #270 remainder)"
            )

    def test_remainder_interfaces_imported_from_sil_lcmodel(self):
        src = _LCM_CASTING.read_text(encoding="utf-8")
        expected = (
            "ILexEntryInflType",
            "ICmCustomItem",
            "IChkTerm",
            "IConstituentChartCellPart",
        )
        for iface in expected:
            assert iface in src, (
                f"lcm_casting._ensure_interfaces must import {iface} "
                "(issue #279 contract baseline)"
            )
