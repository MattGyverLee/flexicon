# Live verification: issue 603 (SemanticDomains.GetAll recursive=False)

Command:
    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest tests/operations/test_issue603_semdom_getall.py -m requires_live_project -q

run_mode (tests/live_status.json): "live"
Project: sena3_sandbox (tempdir copy of Sena 3 .fwbackup, read-only usage)

Pre-state read from LCM: lp.SemanticDomainListOA.PossibilitiesOS.Count = 9
Post-state (no writes; values read back via the API):
- GetAll(recursive=False): 9 items, all ICmSemanticDomain, none are lists
- GetAll(recursive=True): 1792 items, all ICmSemanticDomain;
  equals 9 + sum(len(GetSubdomains(d)) for top-level d)

Result: PASS (2 passed, 6 deselected)
Offline gate: python -m pytest -m "not requires_live_project" -q -> 2795 passed, 1112 deselected
