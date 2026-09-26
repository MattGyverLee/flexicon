#
#   test_issue542_affix_slot_readers_offline.py
#
#   Source ratchets for issue #542: affix-slot readers on POSOperations,
#   plus the AffixSlot wrapper.
#
#   The real SIL.LCModel assemblies are loaded for this test session
#   whenever FieldWorks is installed on the runner (see flex_plugin.py),
#   which means a plain Python Mock cannot stand in for an
#   IMoInflAffixSlot -- pythonnet's interface cast rejects it outright,
#   the same shape #543's offline suite avoids. These tests therefore
#   pin the source shape (patterns, not runtime behaviour); the runtime
#   behaviour is proven by the paired live-gate module against a real
#   LCM cache.
#
#   Copyright 2026
#

import pathlib
import re

_POS_OPS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "flexicon"
    / "code"
    / "Grammar"
    / "POSOperations.py"
)
_AFFIX_SLOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "flexicon"
    / "code"
    / "Grammar"
    / "affix_slot.py"
)
_AFFIX_TEMPLATE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "flexicon"
    / "code"
    / "Grammar"
    / "affix_template.py"
)
_LIVE_GATE = (
    pathlib.Path(__file__).resolve().parent
    / "test_issue542_affix_slot_readers_live.py"
)


def _method_source(text, method_name):
    pattern = (
        r"(def " + re.escape(method_name) + r"\(self.*?)"
        r"(?=\n    @OperationsMethod|\n    def |\Z)"
    )
    match = re.search(pattern, text, re.DOTALL)
    assert match, f"{method_name} not found"
    return match.group(0)


class TestPOSOperationsSlotReadersOffline:
    def test_all_five_methods_exist(self):
        text = _POS_OPS.read_text(encoding="utf-8")
        for name in (
            "GetSlotName",
            "SetSlotName",
            "IsSlotOptional",
            "SetSlotOptional",
            "GetAffixesInSlot",
        ):
            assert f"def {name}(" in text, f"missing {name}"

    def test_resolve_slot_helper_really_casts(self):
        """
        __ResolveSlot must perform an actual pythonnet cast to
        IMoInflAffixSlot and raise FP_ParameterError on failure -- not the
        never-raising hasattr/ClassName-string-compare shape used by
        __ResolveObject (the 4.10.0 live-gate finding, commit 9218b3c).
        """
        text = _POS_OPS.read_text(encoding="utf-8")
        src = _method_source(text, "__ResolveSlot")
        assert "IMoInflAffixSlot(obj)" in src
        assert "FP_ParameterError" in src

    def test_get_slot_name_normalizes_and_reads_no_write_guard(self):
        text = _POS_OPS.read_text(encoding="utf-8")
        src = _method_source(text, "GetSlotName")
        assert "normalize_text" in src
        assert "_EnsureWriteEnabled" not in src
        assert "__ResolveSlot" in src

    def test_set_slot_name_and_optional_guard_writes(self):
        text = _POS_OPS.read_text(encoding="utf-8")
        for name in ("SetSlotName", "SetSlotOptional"):
            src = _method_source(text, name)
            assert "_EnsureWriteEnabled" in src, f"{name} missing write guard"
            assert "_TransactionCM" in src, f"{name} missing transaction"

    def test_is_slot_optional_no_write_guard(self):
        text = _POS_OPS.read_text(encoding="utf-8")
        src = _method_source(text, "IsSlotOptional")
        assert "_EnsureWriteEnabled" not in src
        assert "Optional" in src

    def test_get_affixes_in_slot_uses_direct_back_reference(self):
        """
        GetAffixesInSlot must read IMoInflAffixSlot.Affixes directly --
        the confirmed-by-live-reflection back-reference to every
        IMoInflAffMsa whose SlotsRC contains the slot -- rather than
        scanning a repository or walking every entry's
        MorphoSyntaxAnalysesOC.
        """
        text = _POS_OPS.read_text(encoding="utf-8")
        src = _method_source(text, "GetAffixesInSlot")
        assert "Affixes" in src
        assert "MorphoSyntaxAnalysesOC" not in src
        assert "_EnsureWriteEnabled" not in src

    def test_get_affix_slots_returns_affixslot_wrapper(self):
        text = _POS_OPS.read_text(encoding="utf-8")
        src = _method_source(text, "GetAffixSlots")
        assert "AffixSlot(slot)" in src
        # The docstring example must use the readable-text property, not
        # the raw IMultiUnicode field (the bug reported in #542).
        assert "print(slot.Name)" not in src
        assert "print(slot.name)" in src

    def test_import_affix_slot_wrapper(self):
        text = _POS_OPS.read_text(encoding="utf-8")
        assert "from .affix_slot import AffixSlot" in text


class TestAffixSlotWrapperOffline:
    def test_module_exists_with_expected_properties(self):
        assert _AFFIX_SLOT.is_file(), "missing flexicon/code/Grammar/affix_slot.py"
        text = _AFFIX_SLOT.read_text(encoding="utf-8")
        assert "class AffixSlot(LCMObjectWrapper):" in text
        for prop in ("def name(", "def optional(", "def affixes(", "def owner_pos("):
            assert prop in text, f"AffixSlot missing property: {prop}"
        assert "def __repr__" in text
        assert "def __str__" in text

    def test_name_property_normalizes_null_marker(self):
        text = _AFFIX_SLOT.read_text(encoding="utf-8")
        match = re.search(
            r"(def name\(self.*?)(?=\n    @property|\n    def |\Z)",
            text,
            re.DOTALL,
        )
        assert match
        assert "normalize_text" in match.group(0)

    def test_affixes_property_reads_back_reference(self):
        text = _AFFIX_SLOT.read_text(encoding="utf-8")
        match = re.search(
            r"(def affixes\(self.*?)(?=\n    @property|\n    def |\Z)",
            text,
            re.DOTALL,
        )
        assert match
        assert "Affixes" in match.group(0)


class TestAffixTemplateSlotPropertiesOffline:
    def test_all_four_slot_properties_wrap_affixslot(self):
        text = _AFFIX_TEMPLATE.read_text(encoding="utf-8")
        assert "from .affix_slot import AffixSlot" in text
        for prop_name, rs_name in (
            ("prefix_slots", "PrefixSlotsRS"),
            ("suffix_slots", "SuffixSlotsRS"),
            ("proclitic_slots", "ProcliticSlotsRS"),
            ("enclitic_slots", "EncliticSlotsRS"),
        ):
            match = re.search(
                r"(def " + prop_name + r"\(self.*?)(?=\n    @property|\n    def |\Z)",
                text,
                re.DOTALL,
            )
            assert match, f"missing {prop_name}"
            src = match.group(0)
            assert "AffixSlot(s)" in src
            assert rs_name in src

    def test_docstring_examples_fixed(self):
        """
        The reported bug (#542): print(f"Prefix slot: {slot.Name}") prints
        an IMultiUnicode, not text. All four *_slots docstring examples
        must use the wrapper's .name property instead.
        """
        text = _AFFIX_TEMPLATE.read_text(encoding="utf-8")
        assert "slot.Name" not in text
        for label in ("Prefix", "Suffix", "Proclitic", "Enclitic"):
            assert f'print(f"{label} slot: {{slot.name}}")' in text


class TestIssue542LiveGateExists:
    def test_live_gate_module_exists(self):
        assert _LIVE_GATE.is_file(), "missing live gate module for #542"
        body = _LIVE_GATE.read_text(encoding="utf-8")
        assert "requires_live_project" in body
        assert "GetSlotName" in body
        assert "GetAffixesInSlot" in body
