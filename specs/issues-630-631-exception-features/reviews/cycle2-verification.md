# Cycle 2 verification (#630, #631)

- Offline `pytest -m "not requires_live_project" -q`: PASS, 3710 passed, 1168 deselected, 0 failed.
- Live (FLEXLIBS_REQUIRE_LIVE=1, #631 + #630 live files, -m requires_live_project): PASS, 9 passed (4 + 5). tests/live_status.json run_mode = "live". Target present; tests ran on sena3_sandbox copies.

## Read-back quality: good
- #630: re-fetches MSA via project.Object(hvo), casts to concrete type, reads From/To/ProdRestrictRC directly from the LCM, not the wrapper getter. Covers Stem, InflAff (to-side raises FP_ParameterError), DerivAff from/to, and side="both" error.
- #631: asserts on nome.InflectionClassesOC / top.SubclassesOC / ProdRestrictOA counts and membership after create and delete (owner collections, not return values). Confirms classes never land in ProdRestrictOA.

## Gaps
- Shipped Sena 3 backup has zero IMoInflClass objects, so #631 tests seed their own classes. It does not exercise pre-existing data.
- live-631.md values come from a one-off probe, not the pytest run itself. The tests assert equivalent things. Minor.
- Evidence cites a 574 file as "deselected" in the live run; the live-630 command line lists it, but only the 5 live tests ran. Cosmetic.
- No persistence (close/reopen) check.

Verdict: PASS. APPROVE.
