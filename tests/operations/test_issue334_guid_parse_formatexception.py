#
#   test_issue334_guid_parse_formatexception.py
#
#   Class: TestPhonFeatureCreateValueWithGuid,
#          TestPhonFeatureCreateValueFromEntry,
#          TestInflectionFeatureCreateValueFromEntry,
#          TestCatalogBackedCreateFromEntry
#          Offline regression coverage for issue #334: four unguarded
#          System.Guid(...) parses leaked a bare CLR
#          System.FormatException (or System.ArgumentNullException) out
#          of a public method instead of an FP_* exception -- the same
#          shape as #262's object-lookup boundary, applied to Guid
#          parsing instead of object lookup.
#
#          Two of the four sites parse a caller-supplied Guid string
#          (PhonFeatureOperations.__CreateValueWithGuid, reached from
#          the public ApplySyncableProperties) and must frame the error
#          as a caller/argument problem. The other two parse a Guid
#          pulled from the shipped MGA catalog XML
#          (PhonFeatureOperations._CreateValueFromEntry,
#          InflectionFeatureOperations._CreateValueFromEntry, and
#          CatalogBackedMixin._create_from_entry) and must frame the
#          error as a malformed-catalog-data problem, with the raise
#          happening *before* the transaction is opened (an existing,
#          documented ordering invariant -- BaseOperations.py:3057-3060
#          -- so a caller/data error never marks the undo stack).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import sys
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.FLExProject import FP_ParameterError  # noqa: E402

import System  # noqa: E402  (only importable after the flexicon import above
# has run clr.AddReference for the LCM assemblies; see
# test_issue262_object_stale_id.py for the same ordering constraint.)


MALFORMED_GUIDS = ["not-a-guid", "", "   ", "d7f713e8-1234"]

# Issue #336: explicit "" is rejected before parse/mint (unlike a missing key),
# so it raises FP_ParameterError with no CLR exception behind it. Only the
# other malformed values reach System.Guid parsing and carry a __cause__.
MALFORMED_GUIDS_CLR_PARSED = ["not-a-guid", "   ", "d7f713e8-1234"]

VALID_GUID_STR = "d7f713e8-1234-4d1a-9a3d-000000000001"


@contextmanager
def _recording_transaction(calls, label):
    calls.append(label)
    yield


def _no_transaction_should_not_be_called(*_args, **_kwargs):
    raise AssertionError(
        "Transaction was opened; the Guid parse must raise before any "
        "undo task is created."
    )


# ---------------------------------------------------------------------------
# Site 1: PhonFeatureOperations.__CreateValueWithGuid (caller-supplied Guid,
# reached from the public ApplySyncableProperties). Guard is in place,
# inside the already-open transaction.
# ---------------------------------------------------------------------------


class TestPhonFeatureCreateValueWithGuid:
    def _ops(self, monkeypatch):
        from flexicon.code.Grammar import PhonFeatureOperations as mod

        ops = mod.PhonFeatureOperations.__new__(mod.PhonFeatureOperations)

        class _Factory:
            def __init__(self):
                self.create_calls = []

            def Create(self, *args):
                self.create_calls.append(args)
                return SimpleNamespace(Guid=args[0] if args else None)

        factory = _Factory()
        service_locator = SimpleNamespace(
            GetService=lambda iface: factory
        )
        ops.project = SimpleNamespace(
            project=SimpleNamespace(ServiceLocator=service_locator)
        )
        return ops, mod, factory

    @pytest.mark.parametrize("bad_guid", MALFORMED_GUIDS)
    def test_malformed_guid_raises_fp_parameter_error(self, monkeypatch, bad_guid):
        ops, mod, _factory = self._ops(monkeypatch)

        transaction_calls = []
        monkeypatch.setattr(
            ops,
            "_TransactionCM",
            lambda label: _recording_transaction(transaction_calls, label),
        )

        feature = SimpleNamespace(ValuesOC=SimpleNamespace(Add=lambda v: None))

        with pytest.raises(FP_ParameterError, match=r"Guid"):
            ops._PhonFeatureOperations__CreateValueWithGuid(feature, bad_guid)

        # This site's guard sits inside the already-open transaction (no
        # ordering invariant to preserve here), so the transaction is
        # opened exactly once.
        assert transaction_calls == ["Create feature value"]

    def test_empty_guid_rejected_before_parse(self, monkeypatch):
        ops, mod, factory = self._ops(monkeypatch)
        monkeypatch.setattr(
            ops, "_TransactionCM", lambda label: _recording_transaction([], label)
        )
        feature = SimpleNamespace(ValuesOC=SimpleNamespace(Add=lambda v: None))

        with pytest.raises(FP_ParameterError, match="Empty 'Guid'") as excinfo:
            ops._PhonFeatureOperations__CreateValueWithGuid(feature, "")

        # #336 guard fires before any CLR parse, so nothing is chained.
        assert excinfo.value.__cause__ is None
        assert not factory.create_calls

    @pytest.mark.parametrize("bad_guid", MALFORMED_GUIDS_CLR_PARSED)
    def test_malformed_guid_preserves_clr_exception_as_cause(
        self, monkeypatch, bad_guid
    ):
        ops, mod, _factory = self._ops(monkeypatch)
        monkeypatch.setattr(
            ops, "_TransactionCM", lambda label: _recording_transaction([], label)
        )
        feature = SimpleNamespace(ValuesOC=SimpleNamespace(Add=lambda v: None))

        with pytest.raises(FP_ParameterError) as excinfo:
            ops._PhonFeatureOperations__CreateValueWithGuid(feature, bad_guid)

        assert excinfo.value.__cause__ is not None
        assert isinstance(
            excinfo.value.__cause__,
            (System.FormatException, System.ArgumentNullException),
        )

    def test_valid_guid_still_creates_value(self, monkeypatch):
        ops, mod, factory = self._ops(monkeypatch)
        monkeypatch.setattr(
            ops, "_TransactionCM", lambda label: _recording_transaction([], label)
        )
        monkeypatch.setattr(mod, "IFsSymFeatVal", lambda obj: obj)
        added = []
        feature = SimpleNamespace(ValuesOC=SimpleNamespace(Add=added.append))

        result = ops._PhonFeatureOperations__CreateValueWithGuid(
            feature, VALID_GUID_STR
        )

        assert result is not None
        # Path A (factory.Create(guid, feature)) succeeded, so ValuesOC.Add
        # (Path B) was never invoked.
        assert factory.create_calls
        assert factory.create_calls[0][0] == System.Guid(VALID_GUID_STR)

    def test_apply_values_rejects_empty_guid_key(self, monkeypatch):
        """Public ApplySyncableProperties path via __ApplyValues (issue #336)."""
        ops, mod, _factory = self._ops(monkeypatch)
        monkeypatch.setattr(
            ops,
            "_TransactionCM",
            lambda label: _recording_transaction([], label),
        )
        monkeypatch.setattr(
            mod,
            "IFsClosedFeature",
            lambda obj: obj,
        )
        feature = SimpleNamespace(ValuesOC=[])

        with pytest.raises(FP_ParameterError, match="Empty 'Guid'"):
            ops._PhonFeatureOperations__ApplyValues(
                feature,
                [{"Guid": "", "Name": {}}],
                ws_map=None,
                fill_gaps=False,
            )


# ---------------------------------------------------------------------------
# Site 2: PhonFeatureOperations._CreateValueFromEntry (catalog-sourced Guid).
# Guard must sit before the transaction is opened.
# ---------------------------------------------------------------------------


class TestPhonFeatureCreateValueFromEntry:
    def _ops(self):
        from flexicon.code.Grammar import PhonFeatureOperations as mod

        ops = mod.PhonFeatureOperations.__new__(mod.PhonFeatureOperations)

        class _Factory:
            def Create(self, *args):
                return SimpleNamespace(
                    Guid=args[0] if args else None,
                    Name=SimpleNamespace(),
                    Abbreviation=SimpleNamespace(),
                )

        service_locator = SimpleNamespace(GetService=lambda iface: _Factory())
        ops.project = SimpleNamespace(
            project=SimpleNamespace(ServiceLocator=service_locator)
        )
        return ops, mod

    @pytest.mark.parametrize("bad_guid", MALFORMED_GUIDS)
    def test_malformed_catalog_guid_raises_before_transaction(
        self, monkeypatch, bad_guid
    ):
        ops, _mod = self._ops()
        monkeypatch.setattr(
            ops, "_TransactionCM", _no_transaction_should_not_be_called
        )
        value_entry = SimpleNamespace(guid=bad_guid, id="fPAConsonantal")

        with pytest.raises(FP_ParameterError, match=r"catalog"):
            ops.__class__._CreateValueFromEntry(
                ops, value_entry, SimpleNamespace(), set(), []
            )

    def test_malformed_catalog_guid_preserves_clr_exception_as_cause(
        self, monkeypatch
    ):
        ops, _mod = self._ops()
        monkeypatch.setattr(
            ops, "_TransactionCM", _no_transaction_should_not_be_called
        )
        value_entry = SimpleNamespace(guid="not-a-guid", id="fPAConsonantal")

        with pytest.raises(FP_ParameterError) as excinfo:
            ops.__class__._CreateValueFromEntry(
                ops, value_entry, SimpleNamespace(), set(), []
            )

        assert excinfo.value.__cause__ is not None
        assert isinstance(excinfo.value.__cause__, System.FormatException)

    def test_valid_catalog_guid_reaches_transaction(self, monkeypatch):
        ops, mod = self._ops()
        transaction_calls = []
        monkeypatch.setattr(
            ops,
            "_TransactionCM",
            lambda label: _recording_transaction(transaction_calls, label),
        )
        # Casting / multistring writes are exercised elsewhere; here we only
        # need to prove the Guid parse itself does not raise for a
        # well-formed value and that the transaction gets opened.
        monkeypatch.setattr(mod, "IFsSymFeatVal", lambda obj: obj)
        monkeypatch.setattr(
            ops,
            "_set_multistring",
            lambda multistring, ws_to_text, missing_ws_seen, warnings: None,
        )
        value_entry = SimpleNamespace(
            guid=VALID_GUID_STR, id="fPAConsonantal", term={}, abbrev={}, def_={}
        )

        result = ops.__class__._CreateValueFromEntry(
            ops, value_entry, SimpleNamespace(), set(), []
        )

        assert result is not None
        assert transaction_calls  # transaction was opened this time


# ---------------------------------------------------------------------------
# Site 3: InflectionFeatureOperations._CreateValueFromEntry (near-duplicate
# of site 2; must be covered independently per the ruling).
# ---------------------------------------------------------------------------


class TestInflectionFeatureCreateValueFromEntry:
    def _ops(self):
        from flexicon.code.Grammar import InflectionFeatureOperations as mod

        ops = mod.InflectionFeatureOperations.__new__(
            mod.InflectionFeatureOperations
        )

        class _Factory:
            def Create(self, *args):
                return SimpleNamespace(
                    Guid=args[0] if args else None,
                    Name=SimpleNamespace(),
                    Abbreviation=SimpleNamespace(),
                )

        service_locator = SimpleNamespace(GetService=lambda iface: _Factory())
        ops.project = SimpleNamespace(
            project=SimpleNamespace(ServiceLocator=service_locator)
        )
        return ops, mod

    @pytest.mark.parametrize("bad_guid", MALFORMED_GUIDS)
    def test_malformed_catalog_guid_raises_before_transaction(
        self, monkeypatch, bad_guid
    ):
        ops, _mod = self._ops()
        monkeypatch.setattr(
            ops, "_TransactionCM", _no_transaction_should_not_be_called
        )
        value_entry = SimpleNamespace(guid=bad_guid, id="fGender")

        with pytest.raises(FP_ParameterError, match=r"catalog"):
            ops.__class__._CreateValueFromEntry(
                ops, value_entry, SimpleNamespace(), set(), []
            )

    def test_malformed_catalog_guid_preserves_clr_exception_as_cause(
        self, monkeypatch
    ):
        ops, _mod = self._ops()
        monkeypatch.setattr(
            ops, "_TransactionCM", _no_transaction_should_not_be_called
        )
        value_entry = SimpleNamespace(guid="", id="fGender")

        with pytest.raises(FP_ParameterError) as excinfo:
            ops.__class__._CreateValueFromEntry(
                ops, value_entry, SimpleNamespace(), set(), []
            )

        assert excinfo.value.__cause__ is not None
        assert isinstance(excinfo.value.__cause__, System.FormatException)

    def test_valid_catalog_guid_reaches_transaction(self, monkeypatch):
        ops, mod = self._ops()
        transaction_calls = []
        monkeypatch.setattr(
            ops,
            "_TransactionCM",
            lambda label: _recording_transaction(transaction_calls, label),
        )
        monkeypatch.setattr(mod, "IFsSymFeatVal", lambda obj: obj)
        monkeypatch.setattr(
            ops,
            "_set_multistring",
            lambda multistring, ws_to_text, missing_ws_seen, warnings: None,
        )
        value_entry = SimpleNamespace(
            guid=VALID_GUID_STR, id="fGender", term={}, abbrev={}, def_={}
        )

        result = ops.__class__._CreateValueFromEntry(
            ops, value_entry, SimpleNamespace(), set(), []
        )

        assert result is not None
        assert transaction_calls


# ---------------------------------------------------------------------------
# Site 4: CatalogBackedMixin._create_from_entry (shared by every
# catalog-backed Operations class, e.g. POS via GOLDEtic.xml).
# ---------------------------------------------------------------------------


class TestCatalogBackedCreateFromEntry:
    def _ops(self):
        from flexicon.code.Shared import catalog_backed as mod

        class _FakeCatalogOps(mod.CatalogBackedMixin):
            DOMAIN_LABEL = "test-domain"

            def _factory_create_attached(self, guid, parent):
                return SimpleNamespace(Guid=guid)

            def _path_b_attach(self, new_obj, parent_obj):
                pass

            def _cast_to_domain(self, raw_lcm_obj):
                return raw_lcm_obj

            def _set_localized(self, obj, term, abbrev, def_, missing_ws_seen, warnings):
                pass

            def _TransactionCM(self, label):
                raise NotImplementedError(
                    "test must monkeypatch _TransactionCM"
                )

        ops = _FakeCatalogOps()
        return ops, mod

    @pytest.mark.parametrize("bad_guid", MALFORMED_GUIDS)
    def test_malformed_catalog_guid_raises_before_transaction(
        self, monkeypatch, bad_guid
    ):
        ops, _mod = self._ops()
        monkeypatch.setattr(
            ops, "_TransactionCM", _no_transaction_should_not_be_called
        )
        entry = SimpleNamespace(guid=bad_guid, id="Noun")

        with pytest.raises(FP_ParameterError, match=r"catalog"):
            ops._create_from_entry(entry, None, set(), [])

    def test_malformed_catalog_guid_preserves_clr_exception_as_cause(
        self, monkeypatch
    ):
        ops, _mod = self._ops()
        monkeypatch.setattr(
            ops, "_TransactionCM", _no_transaction_should_not_be_called
        )
        entry = SimpleNamespace(guid="", id="Noun")

        with pytest.raises(FP_ParameterError) as excinfo:
            ops._create_from_entry(entry, None, set(), [])

        assert excinfo.value.__cause__ is not None
        assert isinstance(excinfo.value.__cause__, System.FormatException)

    def test_valid_catalog_guid_reaches_transaction(self, monkeypatch):
        ops, _mod = self._ops()
        transaction_calls = []
        monkeypatch.setattr(
            ops,
            "_TransactionCM",
            lambda label: _recording_transaction(transaction_calls, label),
        )
        entry = SimpleNamespace(
            guid=VALID_GUID_STR, id="Noun", term={}, abbrev={}, def_={}
        )

        result = ops._create_from_entry(entry, None, set(), [])

        assert result is not None
        assert transaction_calls
