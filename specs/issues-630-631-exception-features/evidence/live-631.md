# Live evidence: issue 631 (inflection class store)

Command:

    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest tests/operations/test_issue631_inflection_class_store_live.py -m requires_live_project -q

run_mode (tests/live_status.json): "live"
Project: sena3_sandbox (tempdir copy of Sena 3 2026-06-09 fwbackup)

Note: the shipped Sena 3 backup has ZERO IMoInflClass objects (IMoInflClassRepository.AllInstances() == 0;
no POS, including "Nome", owns any). The brief's "7 on Nome" does not hold for this fixture, so the
test seeds its own classes under Nome.

Read-back values (re-queried from the LCM owner collections, one-off probe run, same sandbox flow):

    PRE          nome_classes=0 all_classes=0 prodrestrict=0 exc_features=0
    POST-CREATE  nome_classes=1 top.owner_is_nome=True top_subclasses=['TEST_kid'] all_classes=2
                 prodrestrict=1 exc_features=1 find_abbr=te1
    POST-DELETE  nome_classes=0 all_classes=0

(prodrestrict stays equal to the number of exception features: classes never land in ProdRestrictOA.)

Result: 4 passed. PASS.

## Cycle 3 re-run (review findings)

Command:

    FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue630_affix_msa_exception_features_live.py tests/operations/test_issue631_inflection_class_store_live.py -m requires_live_project -q

run_mode (tests/live_status.json): "live". Fixture: sena3_sandbox.

New case: InflectionClassCreate(name, pos=<other POS>, parent=<class under Nome>).
- Pre: other.InflectionClassesOC.Count = N; top (under Nome) has no subclasses.
- Post (re-read): kid.Owner.Hvo == top.Hvo; top.SubclassesOC == [kid]; other.InflectionClassesOC.Count == N;
  a WARNING naming pos=<other.Hvo> and parent=<top.Hvo> was logged (parent wins).
- Name-only create: raises FP_ParameterError whose message names both "pos=" and "parent=".

Result: PASS -- 15 passed (both live files). Offline run: 3719 passed, 1174 deselected.
