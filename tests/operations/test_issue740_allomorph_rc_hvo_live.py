#
#   test_issue740_allomorph_rc_hvo_live.py
#
#   Live verification for issue #740 Allomorph RC HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_740_"


def _make_stem_allomorph(project, form_text):
    entry = project.LexEntry.Create(f"{TEST_PREFIX}{form_text}")
    try:
        allomorphs = list(project.Allomorphs.GetAll(entry))
        if not allomorphs:
            pytest.skip("Entry has no allomorph")
        return entry, allomorphs[0]
    except Exception:
        project.LexEntry.Delete(entry)
        raise


def test_issue740_remove_phoneenv_after_hvo_refetch(sena3_sandbox):
    """RemovePhoneEnv detaches environment when caller holds Object(hvo) view."""
    project = sena3_sandbox
    ops = project.Allomorphs
    envs = list(project.Environments.GetAll())
    if not envs:
        pytest.skip("Sena 3 has no phonological environments")

    env = envs[0]
    entries = list(project.LexiconAllEntries())
    if not entries:
        pytest.skip("Sena 3 has no lexical entries")

    entry = entries[0]
    allomorphs = list(ops.GetAll(entry))
    if not allomorphs:
        pytest.skip("Entry has no allomorph")

    allomorph = allomorphs[0]
    ops.AddPhoneEnv(allomorph, env)
    try:
        assert len(ops.GetPhoneEnv(allomorph)) >= 1

        bare_env = project.Object(env.Hvo)
        ops.RemovePhoneEnv(allomorph, bare_env)
        remaining = [e.Hvo for e in ops.GetPhoneEnv(allomorph)]
        assert env.Hvo not in remaining
    finally:
        try:
            ops.RemovePhoneEnv(allomorph, env)
        except Exception:
            pass


def test_issue740_remove_inflection_class_after_hvo_refetch(sena3_sandbox):
    """RemoveInflectionClass detaches class when caller holds Object(hvo) view.

    Issue #830: the RC lives on affix allomorphs (IMoAffixForm), so this uses
    a MoAffixAllomorph from the Sena 3 sandbox copy.
    """
    project = sena3_sandbox
    ops = project.Allomorphs

    affix = None
    for entry in project.LexiconAllEntries():
        for allo in ops.GetAll(entry):
            if getattr(allo, "ClassName", None) == "MoAffixAllomorph":
                affix = allo
                break
        if affix is not None:
            break
    assert affix is not None, "sena3_sandbox has no MoAffixAllomorph"

    infl_class = project.InflectionFeatures.InflectionClassCreate(
        f"{TEST_PREFIX}infl_class", pos=project.POS.GetAll()[0]
    )

    ops.AddInflectionClass(affix, infl_class)
    assert len(ops.GetInflectionClasses(affix)) == 1

    bare_class = project.Object(infl_class.Hvo)
    ops.RemoveInflectionClass(affix, bare_class)
    assert len(ops.GetInflectionClasses(affix)) == 0
