#
#   test_issue262_object_stale_id.py
#
#   Class: TestObjectStaleId, TestSetPartOfSpeechStaleIds,
#          TestGetCustomFieldValueStaleIds
#          Offline regression coverage for issue #262:
#          FLExProject.Object(hvoOrGuid) used to leak the raw CLR
#          System.Collections.Generic.KeyNotFoundException when
#          hvoOrGuid was well-formed but stale (no longer resolves to
#          a live object). The lex-domain ruling on #262 explicitly
#          rejected returning None from Object() -- it is an
#          identity-resolution lookup, not a search, so a stale id is
#          a caller error. The fix catches the CLR exception (and the
#          sibling lookup-failure exceptions already used by the
#          existing template in
#          Notebook/DataNotebookOperations.py::__GetRecordObject) and
#          re-raises FP_ParameterError naming the offending id, with
#          the original CLR exception preserved as __cause__.
#
#          Six additional Tier-1 sites bypass Object() and call the
#          service locator directly, so the chokepoint fix does not
#          cover them on its own:
#              - FLExProject.GetCustomFieldValue(): ReferenceAtom and
#                ReferenceCollection branches.
#              - LexSenseOperations.SetPartOfSpeech(): the `pos`,
#                `from_pos`, and `to_pos` HVO-resolution sites (the
#                latter two fire inside an open _TransactionCM block).
#          These are covered here too.
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

from flexicon.code.FLExProject import FLExProject, FP_ParameterError  # noqa: E402

import System  # noqa: E402  (only importable after the flexicon import above
# has run clr.AddReference for the LCM assemblies; see test_issue272_
# service_locator_seam.py for the same ordering constraint.)


def _stale_lookup_error(id_):
    return System.Collections.Generic.KeyNotFoundException(
        f"Unable to find id {id_!r} in the object dictionary"
    )


class _Locator:
    """
    Stands in for ILcmServiceLocator.GetObject(hvoOrGuid): resolves a
    single known-good id and raises KeyNotFoundException for anything
    else, exactly reproducing the stale-reference shape from #262.
    """

    def __init__(self, valid_id, valid_obj):
        self._valid_id = valid_id
        self._valid_obj = valid_obj
        self.calls = []

    def GetObject(self, id_):
        self.calls.append(id_)
        if id_ == self._valid_id:
            return self._valid_obj
        raise _stale_lookup_error(id_)


class TestObjectStaleId:
    """
    Direct coverage of FLExProject.Object(), the primary chokepoint.
    """

    def _project(self, locator):
        project = FLExProject.__new__(FLExProject)
        project.project = SimpleNamespace(ServiceLocator=locator)
        return project

    def test_stale_hvo_raises_fp_parameter_error(self):
        sentinel = object()
        locator = _Locator(valid_id=42, valid_obj=sentinel)
        project = self._project(locator)

        with pytest.raises(FP_ParameterError, match="999"):
            project.Object(999)

    def test_stale_hvo_preserves_clr_exception_as_cause(self):
        """
        The ruling is explicit: __cause__ must retain the original CLR
        exception for debuggability (unlike the `from None` sibling
        pattern at GetFieldID). `raise ... from e` must NOT be swapped
        for a bare `raise ...` inside the except block.
        """
        sentinel = object()
        locator = _Locator(valid_id=42, valid_obj=sentinel)
        project = self._project(locator)

        with pytest.raises(FP_ParameterError) as excinfo:
            project.Object(999)

        assert excinfo.value.__cause__ is not None
        assert isinstance(
            excinfo.value.__cause__,
            System.Collections.Generic.KeyNotFoundException,
        )

    def test_stale_guid_raises_fp_parameter_error(self):
        sentinel = object()
        good_guid = System.Guid.NewGuid()
        locator = _Locator(valid_id=good_guid, valid_obj=sentinel)
        project = self._project(locator)

        stale_guid = System.Guid.NewGuid()
        with pytest.raises(FP_ParameterError):
            project.Object(stale_guid)

    def test_valid_hvo_returns_object_not_none(self):
        sentinel = object()
        locator = _Locator(valid_id=42, valid_obj=sentinel)
        project = self._project(locator)

        result = project.Object(42)

        assert result is sentinel
        assert result is not None

    def test_malformed_guid_string_still_raises_fp_parameter_error(self):
        """
        Out of scope for #262, but a guard that the pre-existing
        System.FormatException -> FP_ParameterError translation for
        malformed guid strings was not disturbed by this change.
        """
        sentinel = object()
        locator = _Locator(valid_id=42, valid_obj=sentinel)
        project = self._project(locator)

        with pytest.raises(FP_ParameterError):
            project.Object("not-a-real-guid")

    def test_wrong_type_still_raises_fp_parameter_error(self):
        sentinel = object()
        locator = _Locator(valid_id=42, valid_obj=sentinel)
        project = self._project(locator)

        with pytest.raises(FP_ParameterError):
            project.Object(3.14)


class TestSetPartOfSpeechStaleIds:
    """
    Coverage for the three HVO-resolution sites inside
    LexSenseOperations.SetPartOfSpeech() that bypass Object().
    """

    def _ops(self, monkeypatch, locator):
        from flexicon.code.Lexicon import LexSenseOperations as mod

        ops = mod.LexSenseOperations.__new__(mod.LexSenseOperations)
        ops.project = SimpleNamespace(
            project=SimpleNamespace(ServiceLocator=locator),
            writeEnabled=True,
        )
        monkeypatch.setattr(ops, "_EnsureWriteEnabled", lambda: None)
        monkeypatch.setattr(ops, "_ValidateParam", lambda value, name: None)
        return ops, mod

    def test_stale_pos_hvo_raises_fp_parameter_error(self, monkeypatch):
        locator = _Locator(valid_id=42, valid_obj=object())
        ops, _mod = self._ops(monkeypatch, locator)

        # Not an int -> __GetSenseObject returns it unchanged, so the
        # method reaches the `pos` resolution site without needing any
        # further mocking.
        sense = SimpleNamespace()

        with pytest.raises(FP_ParameterError, match="pos"):
            ops.SetPartOfSpeech(sense, 12345)

    def test_valid_pos_hvo_resolves_and_execution_continues(self, monkeypatch):
        """
        Proves the `pos` resolution succeeds (does not itself raise)
        for a valid id: the next line -- sense.OwnerOfClass() returning
        None -- raises a *different*, pre-existing FP_ParameterError
        ("no owning LexEntry"), which is only reachable if `pos`
        resolved cleanly first.
        """
        pos_obj = object()
        locator = _Locator(valid_id=777, valid_obj=pos_obj)
        ops, _mod = self._ops(monkeypatch, locator)

        sense = SimpleNamespace(OwnerOfClass=lambda class_id: None)

        with pytest.raises(FP_ParameterError, match="owning LexEntry"):
            ops.SetPartOfSpeech(sense, 777)

        assert locator.calls == [777]

    def _affix_entry_and_sense(self, mod):
        """
        Build the minimal object graph needed to reach the from_pos /
        to_pos resolution sites inside the deriv fresh-mint branch:
        an affix-morph-type entry with no pre-existing MSA.
        """
        morph_type = SimpleNamespace(Guid=object())  # not in the stem GUID set
        entry = SimpleNamespace(LexemeFormOA=SimpleNamespace(MorphTypeRA=morph_type))
        sense = SimpleNamespace(
            OwnerOfClass=lambda class_id: entry,
            MorphoSyntaxAnalysisRA=None,
        )
        return entry, sense

    def test_stale_from_pos_hvo_raises_fp_parameter_error_inside_transaction(
        self, monkeypatch
    ):
        from flexicon.code.Lexicon import LexSenseOperations as mod

        pos_obj = object()
        locator = _Locator(valid_id=1, valid_obj=pos_obj)
        ops, mod = self._ops(monkeypatch, locator)

        entry, sense = self._affix_entry_and_sense(mod)

        # ILexEntry(_owner) is a real pythonnet interface cast; identity
        # through for this offline test since `entry` is already the
        # object OwnerOfClass returned.
        monkeypatch.setattr(mod, "ILexEntry", lambda obj: obj)

        @contextmanager
        def _no_transaction(label):
            yield

        monkeypatch.setattr(ops, "_TransactionCM", _no_transaction)

        with pytest.raises(FP_ParameterError, match="from_pos"):
            ops.SetPartOfSpeech(
                sense, pos=1, msa_kind="deriv", from_pos=999999
            )

    def test_stale_to_pos_hvo_raises_fp_parameter_error_inside_transaction(
        self, monkeypatch
    ):
        from flexicon.code.Lexicon import LexSenseOperations as mod

        pos_obj = object()
        locator = _Locator(valid_id=1, valid_obj=pos_obj)
        ops, mod = self._ops(monkeypatch, locator)

        entry, sense = self._affix_entry_and_sense(mod)
        monkeypatch.setattr(mod, "ILexEntry", lambda obj: obj)

        @contextmanager
        def _no_transaction(label):
            yield

        monkeypatch.setattr(ops, "_TransactionCM", _no_transaction)

        with pytest.raises(FP_ParameterError, match="to_pos"):
            ops.SetPartOfSpeech(
                sense, pos=1, msa_kind="deriv", from_pos=1, to_pos=999999
            )

    def test_valid_from_and_to_pos_reach_create_deriv_aff(self, monkeypatch):
        """
        Positive-path proof: valid from_pos/to_pos ids resolve and the
        method reaches MSA.CreateDerivAff with the *resolved objects*,
        not the raw ids -- and no exception escapes the transaction.
        """
        from flexicon.code.Lexicon import LexSenseOperations as mod

        pos_obj = object()
        from_obj = object()
        to_obj = object()
        locator = _Locator(valid_id=1, valid_obj=pos_obj)
        # One id resolves to multiple distinct objects depending on the
        # value requested, so extend the simple _Locator here.
        resolved = {1: pos_obj, 2: from_obj, 3: to_obj}

        class _MultiLocator:
            def __init__(self):
                self.calls = []

            def GetObject(self, id_):
                self.calls.append(id_)
                if id_ in resolved:
                    return resolved[id_]
                raise _stale_lookup_error(id_)

        multi_locator = _MultiLocator()
        ops, mod = self._ops(monkeypatch, multi_locator)

        entry, sense = self._affix_entry_and_sense(mod)
        monkeypatch.setattr(mod, "ILexEntry", lambda obj: obj)

        @contextmanager
        def _no_transaction(label):
            yield

        monkeypatch.setattr(ops, "_TransactionCM", _no_transaction)

        captured = {}

        def _fake_create_deriv_aff(sense_arg, from_pos, to_pos):
            captured["sense"] = sense_arg
            captured["from_pos"] = from_pos
            captured["to_pos"] = to_pos

        ops.project.MSA = SimpleNamespace(CreateDerivAff=_fake_create_deriv_aff)

        ops.SetPartOfSpeech(sense, pos=1, msa_kind="deriv", from_pos=2, to_pos=3)

        assert captured["from_pos"] is from_obj
        assert captured["to_pos"] is to_obj
        assert multi_locator.calls == [1, 2, 3]


class TestGetCustomFieldValueStaleIds:
    """
    Coverage for the ReferenceAtom and ReferenceCollection branches of
    FLExProject.GetCustomFieldValue(), which resolve possibility items
    via ObjectRepository(...).GetObject(item) instead of Object().
    """

    def _project(self, monkeypatch, field_type, get_object_prop=None, get_vec=None):
        import flexicon.code.FLExProject as flexproject_mod
        from SIL.LCModel.Core.Cellar import CellarPropertyType

        # Isolate the SUT logic from the real IFwMetaDataCacheManaged
        # interface cast, which requires a genuine CLR object on the
        # other end; identity-through is a standard mock-cast
        # substitution, not a change to production behaviour.
        monkeypatch.setattr(
            flexproject_mod, "IFwMetaDataCacheManaged", lambda x: x
        )

        project = flexproject_mod.FLExProject.__new__(flexproject_mod.FLExProject)
        domain_data = SimpleNamespace()
        if get_object_prop is not None:
            domain_data.get_ObjectProp = get_object_prop
        if get_vec is not None:
            domain_data.get_VecSize = get_vec[0]
            domain_data.get_VecItem = get_vec[1]

        project.project = SimpleNamespace(
            MetaDataCacheAccessor=SimpleNamespace(
                GetFieldType=lambda field_id: int(field_type)
            ),
            DomainDataByFlid=domain_data,
        )
        return project, CellarPropertyType

    def test_reference_atom_stale_item_raises(self, monkeypatch):
        import flexicon.code.FLExProject as flexproject_mod
        from SIL.LCModel.Core.Cellar import CellarPropertyType

        stale_item = object()
        locator = _Locator(valid_id="ok", valid_obj=object())

        project, _ = self._project(
            monkeypatch,
            CellarPropertyType.ReferenceAtom,
            get_object_prop=lambda hvo, fid: stale_item,
        )
        project.project.ServiceLocator = SimpleNamespace(
            GetService=lambda repo: locator
        )

        with pytest.raises(FP_ParameterError, match="possibility item"):
            project.GetCustomFieldValue(1, 2)

    def test_reference_atom_valid_item_returns_short_name(self, monkeypatch):
        from SIL.LCModel.Core.Cellar import CellarPropertyType

        good_item = "the-item-key"
        poss = SimpleNamespace(ShortName="Domain X")
        locator = _Locator(valid_id=good_item, valid_obj=poss)

        project, _ = self._project(
            monkeypatch,
            CellarPropertyType.ReferenceAtom,
            get_object_prop=lambda hvo, fid: good_item,
        )
        project.project.ServiceLocator = SimpleNamespace(
            GetService=lambda repo: locator
        )

        assert project.GetCustomFieldValue(1, 2) == "Domain X"

    def test_reference_collection_stale_item_raises(self, monkeypatch):
        from SIL.LCModel.Core.Cellar import CellarPropertyType

        stale_item = object()
        locator = _Locator(valid_id="ok", valid_obj=object())

        project, _ = self._project(
            monkeypatch,
            CellarPropertyType.ReferenceCollection,
            get_vec=(lambda hvo, fid: 1, lambda hvo, fid, i: stale_item),
        )
        project.project.ServiceLocator = SimpleNamespace(
            GetService=lambda repo: locator
        )

        with pytest.raises(FP_ParameterError, match="possibility item"):
            project.GetCustomFieldValue(1, 2)

    def test_reference_collection_valid_items_return_short_names(self, monkeypatch):
        from SIL.LCModel.Core.Cellar import CellarPropertyType

        items = ["a", "b"]
        possibilities = {
            "a": SimpleNamespace(ShortName="Alpha"),
            "b": SimpleNamespace(ShortName="Beta"),
        }

        class _CollectionLocator:
            def GetObject(self, id_):
                return possibilities[id_]

        project, _ = self._project(
            monkeypatch,
            CellarPropertyType.ReferenceCollection,
            get_vec=(
                lambda hvo, fid: len(items),
                lambda hvo, fid, i: items[i],
            ),
        )
        project.project.ServiceLocator = SimpleNamespace(
            GetService=lambda repo: _CollectionLocator()
        )

        assert project.GetCustomFieldValue(1, 2) == ["Alpha", "Beta"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
