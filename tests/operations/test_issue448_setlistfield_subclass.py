#
#   test_issue448_setlistfield_subclass.py
#
#   Follow-up to #448: LexiconSetListFieldSingle rejected every
#   CmPossibility subclass because it compared ClassName to
#   "CmPossibility". It now casts via ICmPossibility.
#
#   Copyright 2026
#

import pytest
from unittest.mock import Mock

# Capture at collection time: test_issue357_clause_marker_getwordgroup_offline
# permanently poisons sys.modules["flexicon.code.FLExProject"] (see #476).
import flexicon.code.FLExProject as _fp_module

FLExProject = _fp_module.FLExProject
FP_ParameterError = _fp_module.FP_ParameterError


class _FakePossibility:
    def __init__(self, hvo, class_name):
        self.Hvo = hvo
        self.ClassName = class_name


def _fake_cast(obj):
    if isinstance(obj, _FakePossibility):
        return obj
    raise TypeError("not an ICmPossibility")


@pytest.fixture
def project(monkeypatch):
    p = FLExProject.__new__(FLExProject)
    p.writeEnabled = True
    p.project = Mock()
    monkeypatch.setattr(_fp_module, "ICmPossibility", _fake_cast)
    return p


@pytest.mark.parametrize(
    "cls", ["PartOfSpeech", "CmSemanticDomain", "CmAnthroItem",
            "CmLocation", "CmPerson", "CmCustomItem", "CmPossibility"]
)
def test_possibility_subclass_is_accepted(project, cls):
    poss = _FakePossibility(11, cls)
    project.LexiconSetListFieldSingle(Mock(Hvo=5), 7, poss)
    project.project.DomainDataByFlid.SetObjProp.assert_called_once_with(5, 7, 11)


def test_non_possibility_object_still_rejected(project):
    with pytest.raises(FP_ParameterError):
        project.LexiconSetListFieldSingle(Mock(Hvo=5), 7, object())
    project.project.DomainDataByFlid.SetObjProp.assert_not_called()


# ---------------------------------------------------------------------------
# Live
# ---------------------------------------------------------------------------

TEST_PREFIX = "TEST_448F_"


@pytest.mark.requires_live_project
@pytest.mark.live_phase("FLExProject", "modify")
def test_set_list_field_single_partofspeech_live(target_sandbox):
    from SIL.LCModel import IMoStemMsa, IMoStemMsaFactory

    project = target_sandbox
    pos = project.POS.Create(f"{TEST_PREFIX}Noun", f"{TEST_PREFIX}n")
    entry = project.LexEntry.Create(lexeme_form=f"{TEST_PREFIX}lex")
    factory = project.project.ServiceLocator.GetService(IMoStemMsaFactory)
    with project._TransactionCM("448f: add MSA"):
        msa = factory.Create()
        entry.MorphoSyntaxAnalysesOC.Add(msa)
    msa_guid = str(msa.Guid)
    field_id = project.GetFieldID("MoStemMsa", "PartOfSpeech")

    pre = IMoStemMsa(project.Object(msa_guid)).PartOfSpeechRA
    assert pre is None or str(pre.Guid) != str(pos.Guid)
    print(f"[448f] pre PartOfSpeechRA={pre}")

    project.LexiconSetListFieldSingle(msa, field_id, pos)
    post = IMoStemMsa(project.Object(msa_guid)).PartOfSpeechRA
    print(f"[448f] post (object) PartOfSpeechRA={post.Guid}")
    assert str(post.Guid) == str(pos.Guid)

    # Clear, then set via a bare ICmObject reference.
    project.LexiconClearListFieldSingle(msa, field_id)
    assert IMoStemMsa(project.Object(msa_guid)).PartOfSpeechRA is None
    bare = project.Object(pos.Hvo)
    project.LexiconSetListFieldSingle(msa, field_id, bare)
    post2 = IMoStemMsa(project.Object(msa_guid)).PartOfSpeechRA
    print(f"[448f] post (bare ICmObject) PartOfSpeechRA={post2.Guid}")
    assert str(post2.Guid) == str(pos.Guid)


@pytest.mark.requires_live_project
@pytest.mark.live_phase("FLExProject", "modify")
def test_set_list_field_single_rejects_non_possibility_live(target_sandbox):
    from SIL.LCModel import IMoStemMsaFactory

    project = target_sandbox
    entry = project.LexEntry.Create(lexeme_form=f"{TEST_PREFIX}rej")
    factory = project.project.ServiceLocator.GetService(IMoStemMsaFactory)
    with project._TransactionCM("448f: add MSA reject"):
        msa = factory.Create()
        entry.MorphoSyntaxAnalysesOC.Add(msa)
    field_id = project.GetFieldID("MoStemMsa", "PartOfSpeech")
    with pytest.raises(FP_ParameterError):
        project.LexiconSetListFieldSingle(msa, field_id, entry)
