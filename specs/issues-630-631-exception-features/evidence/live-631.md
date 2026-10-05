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
