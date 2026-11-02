#
#   test_issue830_allomorph_inflection_class_live.py
#
#   Live verification (Sena 3 sandbox, tempdir copy) for issue #830:
#   Get/Add/RemoveInflectionClass act on IMoAffixForm.InflectionClassesRC
#   of affix allomorphs; stem allomorphs raise FP_ParameterError on the
#   mutators and read as []. Modeled on test_target_live_smoke.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_NAME = "TEST_830"


def _rc_hvos(project, allomorph_hvo):
    """Re-fetch by HVO and read the RC straight off the LCM object."""
    from SIL.LCModel import IMoAffixForm

    fresh = project.Object(allomorph_hvo)
    return [int(c.Hvo) for c in IMoAffixForm(fresh).InflectionClassesRC]


def _find_allomorph(project, class_name):
    """Return (entry, allomorph) for the first allomorph of class_name."""
    for entry in project.LexiconAllEntries():
        for allo in project.Allomorphs.GetAll(entry):
            if getattr(allo, "ClassName", None) == class_name:
                return entry, allo
    return None, None


def _pos_for(project, entry):
    """POS of the entry's affix MSA if it has one, else any POS."""
    for msa in entry.MorphoSyntaxAnalysesOC:
        pos = getattr(msa, "PartOfSpeechRA", None)
        if pos is not None:
            return pos
    return project.POS.GetAll()[0]


@pytest.mark.live_phase("AllomorphOperations", "add")
def test_issue830_affix_allomorph_inflection_class_round_trip(sena3_sandbox):
    project = sena3_sandbox
    assert project.writeEnabled is True
    ops = project.Allomorphs

    entry, allo = _find_allomorph(project, "MoAffixAllomorph")
    assert allo is not None, "sena3_sandbox has no MoAffixAllomorph"
    allo_hvo = int(allo.Hvo)
    pos = _pos_for(project, entry)
    infl = project.InflectionFeatures.InflectionClassCreate(TEST_NAME, pos=pos)
    class_hvo = int(infl.Hvo)

    before = _rc_hvos(project, allo_hvo)
    assert class_hvo not in before
    print(f"[EVIDENCE] affix allomorph hvo={allo_hvo} class hvo={class_hvo} "
          f"RC before={before}")

    # 1-2. Add, then verify on a re-fetched object (read back from the LCM).
    ops.AddInflectionClass(allo, infl)
    refetched = project.Object(allo_hvo)
    after_add = _rc_hvos(project, allo_hvo)
    print(f"[EVIDENCE] after add RC={after_add}")
    assert class_hvo in after_add
    assert class_hvo in [int(c.Hvo) for c in ops.GetInflectionClasses(refetched)]

    # 3. Idempotent add.
    ops.AddInflectionClass(refetched, class_hvo)
    after_again = _rc_hvos(project, allo_hvo)
    print(f"[EVIDENCE] after second add RC={after_again}")
    assert len(after_again) == len(after_add)
    assert after_again.count(class_hvo) == 1

    # 4. Remove (through a bare re-fetched class), re-fetch.
    ops.RemoveInflectionClass(allo_hvo, project.Object(class_hvo))
    after_remove = _rc_hvos(project, allo_hvo)
    print(f"[EVIDENCE] after remove RC={after_remove}")
    assert class_hvo not in after_remove
    assert ops.GetInflectionClasses(project.Object(allo_hvo)) == []


@pytest.mark.live_phase("AllomorphOperations", "add")
def test_issue830_stem_allomorph_add_remove_raise(sena3_sandbox):
    project = sena3_sandbox
    ops = project.Allomorphs

    entry, stem = _find_allomorph(project, "MoStemAllomorph")
    assert stem is not None, "sena3_sandbox has no MoStemAllomorph"
    infl = project.InflectionFeatures.InflectionClassCreate(
        TEST_NAME + "_stem", pos=project.POS.GetAll()[0]
    )
    print(f"[EVIDENCE] stem allomorph hvo={int(stem.Hvo)} class hvo={int(infl.Hvo)}")

    assert ops.GetInflectionClasses(stem) == []
    with pytest.raises(FP_ParameterError, match="SetInflectionClass"):
        ops.AddInflectionClass(stem, infl)
    with pytest.raises(FP_ParameterError, match="SetInflectionClass"):
        ops.RemoveInflectionClass(stem, infl)


@pytest.mark.live_phase("AllomorphOperations", "add")
def test_issue830_affix_process_round_trip_if_present(sena3_sandbox):
    """MoAffixProcess is UNTESTED live: Sena 3 has none.

    Prints presence and returns if none exists; runs the round trip only if
    a fixture ever gains one.
    """
    project = sena3_sandbox
    entry, proc = _find_allomorph(project, "MoAffixProcess")
    print(f"[EVIDENCE] MoAffixProcess present in sena3_sandbox: {proc is not None}")
    if proc is None:
        return  # offline coverage only; absence is reported, not skipped
    ops = project.Allomorphs
    infl = project.InflectionFeatures.InflectionClassCreate(
        TEST_NAME + "_proc", pos=_pos_for(project, entry)
    )
    hvo = int(proc.Hvo)
    ops.AddInflectionClass(proc, infl)
    assert int(infl.Hvo) in _rc_hvos(project, hvo)
    ops.RemoveInflectionClass(hvo, infl)
    assert int(infl.Hvo) not in _rc_hvos(project, hvo)
