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


def test_issue740_remove_phoneenv_after_hvo_refetch(target_sandbox):
    """RemovePhoneEnv detaches environment when caller holds Object(hvo) view."""
    project = target_sandbox
    ops = project.Allomorphs
    envs = list(project.Environments.GetAll())
    if not envs:
        pytest.skip("Target has no phonological environments")

    env = envs[0]
    entries = list(project.LexiconAllEntries())
    if not entries:
        pytest.skip("Target has no lexical entries")

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


def test_issue740_remove_inflection_class_after_hvo_refetch(target_sandbox):
    """RemoveInflectionClass detaches class when caller holds Object(hvo) view."""
    project = target_sandbox
    ops = project.Allomorphs
    pos_list = list(project.POS.GetAll())
    verb = next((p for p in pos_list if project.POS.GetName(p) == "Verb"), None)
    if verb is None:
        pytest.skip("Target has no Verb POS")

    infl_classes = project.POS.GetInflectionClasses(verb)
    if not infl_classes:
        pytest.skip("Verb POS has no inflection classes")

    infl_class = infl_classes[0]
    entry = project.LexEntry.Create(f"{TEST_PREFIX}infl")
    try:
        project.LexEntry.SetPOS(entry, verb)
        allomorphs = list(ops.GetAll(entry))
        if not allomorphs:
            pytest.skip("Could not obtain stem allomorph")
        allomorph = allomorphs[0]
        if getattr(allomorph, "ClassName", None) != "MoStemAllomorph":
            pytest.skip("Allomorph is not MoStemAllomorph")

        ops.AddInflectionClass(allomorph, infl_class)
        assert len(ops.GetInflectionClasses(allomorph)) == 1

        bare_class = project.Object(infl_class.Hvo)
        ops.RemoveInflectionClass(allomorph, bare_class)
        assert len(ops.GetInflectionClasses(allomorph)) == 0
    finally:
        project.LexEntry.Delete(entry)
