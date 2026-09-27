# STATUS -- 556-morphrule-duplicate-deep

**Updated:** 2026-09-26 (cycle 1 synthesis, /lex-lead)
**Decision:** CONDITIONAL APPROVAL of PR #560 (commit b22271f)

## What landed this spurt
- `tests/operations/test_morphrule_duplicate_deep.py`: the fake `AffixTemplatesOS` can now be iterated
  and carries the source's `Hvo`, matching the HVO scan added by the change from #537. Added an assertion that
  Insert is called at source index + 1. The #203 deep/shallow assertions are unchanged. Offline file result: 6 passed.
- `tests/operations/test_issue556_morphrule_duplicate_deep_live.py` (new, `sena3_sandbox`):
  deep=True copies slot-ref HVOs, deep=False copies none, and the copy is placed at index + 1.
  Both tests re-query from the LCM and both PASS live.
- Offline full suite: 2534 passed, 0 failed. Latest live_status.json at synthesis time:
  `"run_mode": "live"`, `"run_timestamp": "2026-09-27T00:25:29Z"`.
- No file under `flexicon/code/` changed. Live testing confirms test-mock drift, not a library regression from the
  change in #537. This supports downgrading #556 to P3; that is the user's call.
- Gates: verification PASS; QC 88/100 APPROVE; PR CI smoke (3.8/3.11/3.13) green.

## Open items
1. (P2, merge-optional) The evidence file gives pre/post state symbolically (`pre_prefix`, `dup_hvo`) instead of
   literal HVOs, and has no run_timestamp. Precedent (242 spec C16) requires literals plus a verbatim
   run_mode/run_timestamp. Fix: have the live test log the literal values, rerun it serially, and paste them in.
2. (P2) The `_FakeAffixTemplatesOS.IndexOf` stub is never used. Remove it.
3. (OUT OF SCOPE, needs an issue, USER APPROVAL to file) `MorphRuleOperations.__ResolveObject` only casts
   `PartOfSpeech`. An int HVO or a `project.Object(hvo)` view of MoInflAffixTemplate/MoEndoCompound/MoExoCompound
   stays a bare ICmObject, so `Duplicate(hvo)` raises AttributeError on `source.Name` on every call. The
   hasattr-guarded copies (Disabled/HeadLast/Final/slots) would also be skipped silently. This is the cause of the
   pre-existing failure in `test_issue537_morphrule_duplicate_hvo_live.py::...raw_object_view`, reproduced on
   unmodified origin/main. Proposed label: bug + P1 (a documented input path always raises; unsure between P1 and P2,
   so the higher is chosen). Likely fix: route through `cast_to_concrete()` as the 4.10.0 resolver series did.

## Next pickup
The user decides: (a) merge #560 now or after item 1/2 polish; (b) file the __ResolveObject issue; (c) relabel #556 to P3.
