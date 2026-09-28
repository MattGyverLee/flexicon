# Name-field whitespace identity -- matcher harness, cycle 2

Scope of THIS cycle: Appendix B Checkpoint 2 T1/T2/T3 (the `normalize_match_key`
matcher measurement harness for #274). **No line under `flexicon/` was changed
by this cycle.** T4-T7 (the matcher FIX) were explicitly NOT attempted -- see
the BLOCKER section below for why they cannot proceed as written.

The frozen cycle-1 file `evidence/live-probe-cycle1.md` (predictions PN1-PN8,
committed `bdbce02`) was **NOT edited** by this cycle. Its predictions and its
already-filled RESULTS section are left byte-for-byte intact per the C28
forward rule and the task's "do not touch the predictions" constraint. This is
a separate, appended record.

## Run mode

`tests/live_status.json` after the live run:

```
run_mode:      live
run_timestamp: 2026-09-08T20:42:51Z
probe tests recorded: 20   (all status "pass")
```

LIVE verification was POSSIBLE and was performed (`FLEXLIBS_REQUIRE_LIVE=1`,
`target_sandbox` only). This is a genuine live result, not a mock pass.

## Commands run, in order, with pass/fail lines

```
# T3 + T2 offline (pure Python, no LCM)
$ python -m pytest tests/test_normalize_match_key.py -q -rxX
11 passed, 4 xfailed in 0.61s
    -> the 4 xfailed are the NEW #274 whitespace-identity cases (below);
       they XFAIL against the UNFIXED matcher exactly as intended.

# T2 live -- collect-only count (derive the count, never trust the filename)
$ python -m pytest tests/operations/test_name_field_identity_probe.py \
      --collect-only -q -m requires_live_project
20 tests collected in 0.06s        # non-zero; not "no tests collected"

# T2 live -- the measuring run
$ export FLEXLIBS_REQUIRE_LIVE=1
$ python -m pytest tests/operations/test_name_field_identity_probe.py \
      -m requires_live_project -q
20 passed in 6.78s
```

## What actually exists at HEAD (48df4f8) -- the task premise is STALE

The task brief was written from Appendix B's worldview ("the probe file does
not exist; implementation has not started; measure PN1-PN8 against the UNFIXED
code"). That worldview reflects a branch that was ~120 commits behind. On
`main` at HEAD it is false in three load-bearing ways:

1. **The probe file already exists** with **20** tests (PN1-PN20), not 8.
   PN1-PN8 are cycle 1; PN9-PN20 were added by the C1-C13 crew's T1-T4.
2. **The C1-C13 implementation already LANDED.** The three comparison sites
   carry the inline both-sides strip (verified at HEAD):
   - `TextOperations.py:474/:477`
   - `AnthropologyOperations.py:600/:603`
   - `CheckOperations.py:374/:380`
   and the 8 writer sites persist raw bytes (commits `3eac4a0`, `db95230`,
   `ab638aa`, `0ab9c60`, all ancestors of HEAD).
3. Consequently the probe's PN2/PN3/PN4/PN8 were already **flipped** to assert
   the C1-C13 *fixed* behaviour (see each test's docstring, e.g. PN2 at
   `:148-171`). They no longer assert the cycle-1 "haystack never stripped"
   prediction; they assert its opposite, and they PASS at HEAD.

**Therefore "measure PN1-PN8 against the UNFIXED code" is not achievable at
HEAD for the Text/Anthropology/Check families -- that code is fixed.** Mapping
each frozen (unfixed) prediction to HEAD:

| Frozen PN (unfixed prediction) | Holds at HEAD? | Why |
|---|---|---|
| PN1 control: `Exists(padded)` -> True | CONFIRMED | control; true pre- and post-fix; PN1 passes |
| PN2: padded haystack invisible to `Exists` | REFUTED at HEAD | `TextOperations.Exists` now strips BOTH sides (C1-C13 T2); padded haystack IS found; PN2 passes asserting True |
| PN3: padded haystack invisible to `Find` | REFUTED at HEAD | `AnthropologyOperations.Find` fixed (C1-C13 T3) |
| PN4: `FindCheckType` misses padded haystack | REFUTED at HEAD | `CheckOperations.FindCheckType` fixed (C1-C13 T4) |
| PN5/PN6: `CreateCheckType` silently persists empty name | REFUTED at HEAD | now RAISES loudly (C1-C13 T4 / Q-242B) |
| PN7: three-way non-str split | CONFIRMED | Shape-B sites still `AttributeError`; typed sites still `TypeError`; PN7 passes |
| PN8: duplicate explosion (Create succeeds twice) | REFUTED at HEAD | second `Texts.Create` now RAISES "already exists" (C1-C13 T2) |

The refutations above are **NOT** a matcher measurement and **NOT** a cycle-1
error. They are the expected consequence of a *different* crew fixing those
four families via a *different* locus (inline strips + persist-raw) than the
NF5 matcher approach this task belongs to. The cycle-1 frozen predictions were
correct against the code as it stood at `bdbce02`; they are simply no longer
what HEAD does.

## The NF5 matcher itself is genuinely UNFIXED -- measured directly

`normalize_match_key` (`Shared/string_utils.py:50-83`) contains **no `.strip()`
anywhere** at HEAD (grep-confirmed). Pure-Python measurement, 2026-09-08:

```
normalize_match_key(" x ")   == " x "     (NF5 wants "x")
normalize_match_key("x ")    == "x "      (NF5 wants "x")
normalize_match_key(" x")    == " x"      (NF5 wants "x")
normalize_match_key("   ")   == "   "     (NF5/H6 wants "")
normalize_match_key(" *** ") == " *** "   (NF7 H4 wants "***")
normalize_match_key("***")   == ""        (correct; unchanged)
normalize_match_key("")      == ""        (correct; unchanged)
```

This is the matcher defect the four NEW xfail unit cases lock down (T3):
`tests/test_normalize_match_key.py::TestNormalizeMatchKeyWhitespaceIdentity`
-- `" x "`, `"   "`, `" *** "`, in both needle and haystack directions, each
marked `xfail(strict=True)` citing #274 / NF5 / NF7 H7. They XFAIL now and will
XPASS (forcing marker removal, `strict=True`) the moment the matcher fix lands.

## BLOCKER for T4-T7 (needs_human)

The NF5 matcher fix (T4: add `text = normalize_text(text).strip(" \t\r\n")`
INSIDE `normalize_match_key`) **directly contradicts this feature's own frozen
contract C4**, which reads: *"Do NOT add `.strip()` to `normalize_match_key`
... `Shared/string_utils.py` ... is NOT edited by this feature. If an
implementer concludes either must change: STOP, needs_human."* The C1-C13 crew
implemented C4 as written -- inline strips at the call sites -- and that work is
on `main`.

Both C1-C13 (C4) and Appendix B (NF5) are marked FROZEN, and they mandate
mutually exclusive fix loci for the same helper. `tasks.md` hard constraint 13
and constraint C13 require STOP + `needs_human` on exactly this class of
conflict. Proceeding to T4 would either (a) violate frozen C4, or (b) be
redundant for the three families C1-C13 already fixed while still needed for
the ~6 bucket-A families C1-C13 did NOT touch (`LocationOperations`,
`AgentOperations`, `PossibilityListOperations`, `SemanticDomainOperations`,
`possibility_item_base`, `FilterOperations`). This is a human decision about
which frozen locus governs and is escalated, not resolved here.

## WHAT WAS NOT EXERCISED

- **NF2 both halves, live through the still-unfixed bucket-A sites**
  (`LocationOperations.Create`/`Find`, `AgentOperations`,
  `PossibilityListOperations.CreateList`/`CreateItem`, `possibility_item_base`):
  NOT added as live probe tests this cycle. Reason: the matcher fix that would
  make them findable/dedup-firing is BLOCKED (above); adding live scaffolding
  for a fix that cannot land as written is premature. The defect at those sites
  is established statically by NF2 and, at the unit level, by the new xfail
  cases. Recorded as a gap, not exercised.
- **The frozen PN1-PN8 predictions against UNFIXED code:** cannot be exercised
  at HEAD for Text/Anthropology/Check -- those families are fixed by C1-C13.
  Confirmed by inspection (grep of the comparison sites) and by the flipped
  probe tests passing, not by reverting the fix (which is out of scope and
  would touch another crew's landed work).
- **`CheckOperations._GetCheckList` bug:** unchanged; PN4/PN5/PN6 continue to
  rely on the cycle-1 `_seed_valid_check_list()` test-instance monkeypatch
  (C9-authorised single seam). Not fixed, per section 3 of `spec.md`.
