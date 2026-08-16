#
#   test_capabilities.py
#
#   Class: TestCapabilities
#          Guard for task B4 (specs/write-path-transactions/tasks.md):
#          `flexicon.CAPABILITIES` is the frozenset FlexToolsMCP probes to
#          decide which write-path surface it is talking to.
#
#          Two properties matter and neither is self-evident from the
#          constant itself:
#
#          1. The token set is exactly the four agreed in
#             docs/FLEXTOOLSMCP_WRITE_CONTRACT.md section 3. A token added
#             here without a landed capability behind it is a constitution V
#             violation (an API implying a guarantee it does not deliver),
#             and a token removed silently breaks a downstream `in` probe.
#          2. The documented probe -- getattr(flexicon, "CAPABILITIES",
#             frozenset()) -- works, and the object supports `in` without
#             raising on an unknown token.
#
#          Pure import-level checks: no FieldWorks, no pythonnet, no live
#          project. Nothing here writes to the LCM.
#
#   Platform: Python 3.8+
#   Copyright 2026
#

"""Contract tests for the `flexicon.CAPABILITIES` frozenset (task B4)."""

import flexicon


#: The four tokens agreed in docs/FLEXTOOLSMCP_WRITE_CONTRACT.md section 3.
#: Kept as a literal rather than imported from flexicon so the test actually
#: pins the value instead of comparing the constant to itself.
EXPECTED_TOKENS = {
    "ui-injection",
    "refresh-from-disk",
    "per-operation-uow",
    "transaction-rollback",
}


class TestCapabilities:
    """B4: the capability set FlexToolsMCP probes."""

    def test_capabilities_is_a_frozenset(self):
        """Immutable, so a consumer cannot mutate another module's view of it."""
        assert isinstance(flexicon.CAPABILITIES, frozenset)

    def test_token_set_is_exactly_the_four_agreed_tokens(self):
        """No token may appear before its capability is real (constitution V),
        and none may vanish without breaking a downstream `in` probe."""
        assert set(flexicon.CAPABILITIES) == EXPECTED_TOKENS

    def test_documented_probe_form_works(self):
        """The getattr(..., frozenset()) form the contract mandates.

        This is the probe FlexToolsMCP ships; it must keep working here so a
        rename of the attribute cannot pass unnoticed.
        """
        caps = getattr(flexicon, "CAPABILITIES", frozenset())

        assert "per-operation-uow" in caps
        assert "transaction-rollback" in caps
        assert "ui-injection" in caps
        assert "refresh-from-disk" in caps

    def test_unknown_token_probes_false_without_raising(self):
        """A consumer probing a token this build does not implement must get
        False, not an exception -- that is what makes the set forward- and
        backward-compatible across versions."""
        assert "no-such-capability" not in flexicon.CAPABILITIES

    def test_probe_fallback_yields_empty_set_on_a_4_3_0_style_module(self):
        """On a pinned 4.3.0 install the attribute does not exist at all, and
        the documented probe must degrade to an empty frozenset rather than
        raising AttributeError."""

        class _NoCapabilitiesModule:
            pass

        caps = getattr(_NoCapabilitiesModule(), "CAPABILITIES", frozenset())

        assert caps == frozenset()
        assert "per-operation-uow" not in caps

    def test_capabilities_reachable_through_the_flexlibs2_alias(self):
        """`sys.modules["flexlibs2"]` is the flexicon module object itself, so
        the alias must expose the same set -- FlexTools scripts on disk still
        import under the old name."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import flexlibs2

        assert flexlibs2.CAPABILITIES is flexicon.CAPABILITIES
