# Handoff -- #348 `SemanticDomainOperations` OcmCodes scalar/multistring

**Branch:** `fix/348-ocmcodes-none`
**Status:** implemented and mock-verified. **NOT QC-reviewed, NOT
live-verified, and NOT ready for a PR** -- see section 4, which describes
a blocker that makes part of the fix unreachable.
**Baseline:** `ce7b96c` (main)
**Written:** 2026-09-21

Work was stopped deliberately part-way, at the user's request, to move the
pattern-audit findings into the issue tracker rather than keep fixing.

---

## 1. The ruling

`ICmSemanticDomain.OcmCodes` is a **scalar `Unicode` / `System.String`** --
a plain Python `str` or `None` at the pythonnet boundary. It is **not** an
`IMultiString`/`MultiUnicode`.

This is ground truth, not inference:
`tests/contract/snapshots/liblcm_baseline.json:7118-7122` gives
`"OcmCodes": {"type": "String", ...}`, from a live reflection capture
against liblcm 11.0.0.0 dated 2026-09-08.

So `.get_String(ws)` on it is a **type-category error, not a missing null
guard**. It fails when the value is unset (`'NoneType' object has no
attribute 'get_String'` -- the reported symptom, 1792/1792 domains) and it
would fail just as surely when the value is set (`'str' object has no
attribute 'get_String'`). The `hasattr(item, "OcmCodes")` guard passes in
both cases: the property genuinely exists on every `CmSemanticDomain`. The
guard was the false safety net that let this ship.

The correct idiom for a scalar Unicode field is the already-shipped
`AgentOperations.py:339` -- `return agent.Version or ""`.

## 2. What changed (uncommitted -> committed on this branch)

`flexicon/code/Lexicon/SemanticDomainOperations.py`, three sites, one root
cause:

| Site | Was | Now |
|---|---|---|
| `GetSyncableProperties` ~1278 | `hasattr` guard + WS loop + `.get_String()` | `props["OcmCodes"] = item.OcmCodes or ""` |
| `GetOcmCodes()` ~611 | `ITsString(domain.OcmCodes.get_String(wsHandle)).Text` | `return domain.OcmCodes or ""` |
| `Duplicate()` ~1131 | `duplicate.OcmCodes.CopyAlternatives(source.OcmCodes)` | `duplicate.OcmCodes = source.OcmCodes or ""` |

The stale in-file comment claiming "OcmCodes is a MultiUnicode" is gone.
`wsHandle` in `GetOcmCodes` turned out to be a **local variable**, not a
parameter, so removing it was not a signature change.

**No `ApplySyncableProperties` override was added, and none is needed.**
`SemanticDomainOperations` has no override and inherits
`BaseOperations._apply_props_loop`, whose plain-`str` branch
(`BaseOperations.py:517-537`) already round-trips a scalar with a bare
`setattr`. This is also why the fix must emit `""` and never `None`: that
loop skips `None` values outright (`BaseOperations.py:456-458`), so a
`None` would silently drop the field on the apply side.

Tests: `tests/operations/test_semantic_domains.py` gains
`TestOcmCodesScalarType`, 7 mock tests, **7 passed**. The fakes model
`OcmCodes` as a bare `str`/`None`, deliberately *not* as a Mock offering
`get_String` -- a Mock would auto-vivify that method and pass against the
broken code, which is exactly how #318's mock suite went green against
production that raised on every real database.

A live test file exists but **has never been run**:
`tests/operations/test_issue348_ocmcodes_scalar_live.py`, 7 tests,
`requires_live_project`, `target_sandbox`, collects cleanly.

## 3. Live verification -- NOT DONE

Per CLAUDE.md this is `FAIL: unverified`. The probe list:

1. `type(domain.OcmCodes)` on a live unset domain is `NoneType`/`str`,
   never an LCM interface; patched `GetSyncableProperties` returns
   `""` without raising across every domain (report the count against the
   issue's 1792/1792).
2. Populate one domain's `OcmCodes` by direct assignment, re-read through
   both `GetSyncableProperties` and `GetOcmCodes`.
3. `Duplicate()` on an unset and a populated domain.
4. Round-trip `ApplySyncableProperties` then re-`GetSyncableProperties`,
   reading post-state back from the LCM.

Use `target_sandbox`: this clone's `tests/fixtures/` has a **Target**
backup and **no Sena 3** backup. Target's semantic domains are expected to
be unset, so the populated case comes from direct assignment -- which is a
materially different provenance from reading pre-existing data, and the
evidence file must say so rather than implying otherwise.

## 4. BLOCKER -- the fix is partly dead code until this is fixed

`SemanticDomainOperations.py:1125`, six lines above the `Duplicate()` fix:

    duplicate.Questions.CopyAlternatives(source.Questions)

`ICmSemanticDomain` has **no `Questions` member**. It has `QuestionsOS`, an
owning sequence (`liblcm_baseline.json:7133`). Unlike the `OcmCodes` line
below it, this one is **not** `hasattr`-guarded, so `Duplicate()` raises
`AttributeError` on **every** domain -- and it raises *before* reaching the
line this branch fixed. **The `Duplicate()` fix at :1131 cannot be
exercised, live or otherwise, until :1125 is also fixed.**

There is a second site in the same file, same member:
`GetSyncableProperties` ~1268 reads `item.Questions.get_String(...)` behind
`hasattr(item, "Questions")` at :1266. That guard is always `False`, so
`props["Questions"]` has been permanently `{}` -- a silent omission rather
than a crash.

Neither is #348's literal shape (#348 is scalar-as-multistring; these are
a member that does not exist at all), so they were **not** fixed here.
They are filed separately -- see section 6. Whoever resumes this must
decide whether to fold the `Questions` fix in or sequence it first;
without it, `Duplicate()` cannot be verified.

## 5. Pattern audit

Shape: *a scalar LCM field treated as an `IMultiString`* -- `.get_String`,
`.set_String`, `.CopyAlternatives`, or a writing-system loop against a
member with no per-WS alternatives. The audit reconciled against the
existing static sweep at
`specs/agent-version-hotfix/reviews/unicode-vs-multiunicode-sweep.md` and
classified every finding against the live-reflected snapshot.

**59 still-broken sites, 54 of them public-surface.** 26 fail hard on
first call; the other 33 fail **silently** behind a `hasattr` guard or a
swallowing `except` -- the worse class, because nothing ever gets filed.

Breakdown: 2 remaining in `SemanticDomainOperations.py` itself (the
`Questions` pair above), 16 genuine scalar-as-multistring elsewhere, 39
where the member does not exist at all, 2 inverse (a real multistring read
as a bare `ITsString`).

The audit also cleared ~40% of the old sweep doc's CONFIRMED table as
already fixed (`ConstChartRowOperations` Label/Notes,
`LexSenseOperations` example `Reference`, and these `OcmCodes` rows), and
found that the doc's "do not batch-fix, run live verification first"
caveat is now obsolete: the 2026-09-08 snapshot confirms every type it
hedged on. Its remaining real limitation is that the snapshot carries
**declared-only, not inherited** properties, which is why a handful of
findings stay at medium confidence.

Full inventory is in the tracker, not duplicated here -- see section 6.

## 6. Tracker state

- **#348** -- this branch. Commented with current state and the :1125
  blocker.
- **New issue** -- the full 59-site pattern-audit inventory, including the
  two `Questions` sites that block this branch.
- **#328** -- commented: the audit settles `IRnGenericRec.Title` as a bare
  `ITsString` via snapshot line 19163, which that issue asserts. The old
  sweep doc had explicitly refused to trust its own inference there.

## 7. Resuming

1. Decide the `Questions` sequencing (section 4). Nothing about
   `Duplicate()` can be verified until then.
2. lex-qc review -- not run.
3. Live verification -- not run (section 3).
4. CHANGELOG entry. `GetOcmCodes()`'s return changes shape for callers who
   somehow worked around the raise, and `GetSyncableProperties` now emits
   an `OcmCodes` key that was never previously reachable.
5. Upstream parity is moot: `SemanticDomainOperations` and the whole
   `GetSyncableProperties`/`ApplySyncableProperties` framework are
   flexicon-only. The fork parent `cdfarrow/flexlibs` has a flat,
   function-based wrapper with no Operations classes at all.
