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
    """RemoveInflectionClass detaches class when caller holds Object(hvo) view."""
    project = sena3_sandbox
    ops = project.Allomorphs
    # Sena 3 has no inflection classes and POps exposes no creator, so add a
    # TEST_ one through the raw LCM factory (sandbox copy; nothing leaks).
    from SIL.LCModel import IMoInflClassFactory

    verb = project.POS.GetAll()[0]
    with project.Transaction("create TEST_740 inflection class"):
        new_class = project.GetFactory(IMoInflClassFactory).Create()
        verb.InflectionClassesOC.Add(new_class)
        new_class.Name.set_String(
            project.project.DefaultAnalWs,
            f"{TEST_PREFIX}infl_class",
        )
    infl_class = project.POS.GetInflectionClasses(verb)[0]
    entry = project.LexEntry.Create(f"{TEST_PREFIX}infl")
    try:
        allomorphs = list(ops.GetAll(entry))
        assert allomorphs, "LexEntry.Create produced no stem allomorph"
        allomorph = allomorphs[0]
        assert getattr(allomorph, "ClassName", None) == "MoStemAllomorph"

        ops.AddInflectionClass(allomorph, infl_class)
        assert len(ops.GetInflectionClasses(allomorph)) == 1

        bare_class = project.Object(infl_class.Hvo)
        ops.RemoveInflectionClass(allomorph, bare_class)
        assert len(ops.GetInflectionClasses(allomorph)) == 0
    finally:
        project.LexEntry.Delete(entry)
