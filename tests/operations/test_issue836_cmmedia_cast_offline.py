#
#   test_issue836_cmmedia_cast_offline.py
#
#   Offline ratchet for issue #836: CmMedia must register in lcm_casting.
#
#   Copyright 2026
#

from pathlib import Path

_LCM_CASTING = (
    Path(__file__).resolve().parents[2] / "flexicon" / "code" / "lcm_casting.py"
)
_LIVE_GATE = (
    Path(__file__).resolve().parent / "test_issue836_cmmedia_cast_live.py"
)


class TestIssue836CmMediaCastOffline:
    def test_interface_cache_registers_cmmedia(self):
        src = _LCM_CASTING.read_text(encoding="utf-8")
        assert '("CmMedia", ICmMedia)' in src or (
            '_interface_cache["CmMedia"]' in src
        ), (
            "lcm_casting must register CmMedia -> ICmMedia for cast_to_concrete "
            "(issue #836)"
        )
        assert "issue #836" in src

    def test_icmmedia_imported_in_hvo_resolver_block(self):
        src = _LCM_CASTING.read_text(encoding="utf-8")
        assert "ICmMedia" in src, (
            "lcm_casting HVO-resolver imports must include ICmMedia (issue #836)"
        )

    def test_live_gate_module_exists(self):
        assert _LIVE_GATE.is_file(), "missing live gate module for #836"
        body = _LIVE_GATE.read_text(encoding="utf-8")
        assert "requires_live_project" in body
        assert "cast_to_concrete" in body
        assert "MediaFileRA" in body
