# Cycle 7 -- Programmer report: D4-T1, D4-T2, D4-T3, D4-T5

**Task:** specs/250-writingsystem-activation/spec.md, D4-T1/D4-T2/D4-T3/D4-T5
(D4-T4 was already done by the archivist; D4-T6 explicitly excluded --
GitHub comment needs the user's approval and is not done here.)
**Claude-Session:** https://claude.ai/code/session_01Wr7oeVWoo3XUJHFe83Km6Y

---

## CONCURRENCY INCIDENT -- read this first

A second, independently dispatched agent instance (`Claude-Session:
session_01RGBHqwkd2STFHfAXgeCbWt`) was working the **identical** D4-T1/T2/T5
task instructions in this **same shared working tree**, concurrently with
this session, apparently as a duplicate `/lex-lead` dispatch rather than a
coordinated split. Sequence of events, reconstructed from both sessions'
commit messages and my own tool-call history:

1. I wrote my own D4-T1 fix (the `_normalize_ws_tag` /
   `_resolve_ws_handle` helpers + the resolution-step edit inside
   `_apply_props_loop`) to the working tree, uncommitted, and moved on to
   writing D4-T2/D4-T3 tests.
2. I committed the test files + evidence-file predictions at `302d266`
   (deliberately NOT touching `BaseOperations.py` in that commit, per the
   spec's "predictions before the fix lands" ordering).
3. Per spec Step 3, I then **overwrote the shared working-tree
   `BaseOperations.py` via `cp` with the pre-fix blob** (extracted from
   `git show HEAD:...`, hash-verified) to measure the unfixed-code drop.
   **This is almost certainly the moment the other session's report
   describes as its own D4-T1 edit "vanishing from the working tree
   between two of my own bash calls"** (`cycle7-programmer-D4-T1-T2-T5.md`,
   "Incident" section) -- my `cp` overwrite of the shared file, done to
   satisfy my own Step-3 requirement, collided with their in-progress
   uncommitted edit sitting in the same file at that exact moment and wiped
   it. I did not intend or realize this at the time; I only later
   reconstructed it from their report.
4. The other session, finding its own edit gone, **re-authored the fix
   from its own diff text** and committed it as `269b6a7`. Independently
   verified by hash: their committed blob
   (`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db`) is **byte-identical** to
   my own fix (confirmed against my scratchpad backup taken before I
   restored it for my own Step 5 measurement). Given the spec's contract
   is prescriptive down to a suggested exact function signature
   (`_resolve_ws_handle(target_ws_by_id, tgt_ws_id, _index_cache=None)`),
   this convergence is plausible on its own merits and does not
   necessarily mean they literally re-committed my restored working-tree
   content rather than independently re-deriving it -- I cannot fully
   distinguish the two from the evidence available, and it does not change
   the correctness conclusion either way.
5. The other session also committed the D4-T5 CHANGELOG entry (`8c679ed`),
   persisted the previously-uncommitted D4-T4 archivist report (`9829e6a`),
   filled in the evidence file's offline-delta and ratchet sections
   (`651577d`), and wrote its own report
   (`specs/250-writingsystem-activation/reviews/cycle7-programmer-D4-T1-T2-T5.md`,
   commit `4287114`) -- explicitly noting in that report that it checked
   for and found my D4-T2/D4-T3 work already present and **did not
   duplicate it**, and explicitly left the live [MEASURED] sections and
   `test_issue250_ws_case_divergence.py` alone because "that token belongs
   to a later agent in this cycle." Their crew respected the live-pytest
   token division correctly.
6. Their commit `651577d` also independently authored (and I separately
   reproduced) the D4-T2 ratchet's "bites when mutated" proof, using a
   transient `flexicon/code/_scratch_ratchet_probe.py`. **This explains a
   ratchet-test failure I observed mid-session** that then passed again on
   an immediate re-run with no change on my side -- their scratch file, not
   a real fourth site.
7. I then restored my own fixed blob (hash-verified) and completed the
   live D4-T3 measurement myself (the one piece their session correctly
   deferred), filled in the evidence file's `[MEASURED]` sections on top
   of their already-committed offline-delta/ratchet content (not
   overwriting it), corrected a mis-pointer in their edit that assumed my
   planned report filename (`cycle7-programmer-D4-T1-T3.md`, the one you
   are reading) had been abandoned, added a full disclosure section to the
   evidence file, and committed both my evidence-file update and a
   necessary test fix (`IPartOfSpeech` cast on POS re-fetch) at `1705e10`.

**Net effect: nothing was lost, nothing is duplicated, and D4-T1/T2/T3/T5
are all now correctly satisfied on `main`, though D4-T1's commit and
D4-T5's commit carry the other session's attribution rather than mine.** I
did not rewrite, amend, or reset any commit to fix attribution -- per the
standing git-safety rules, and because doing so is not necessary for
correctness. **Process recommendation:** deduplicating the dispatch that
produced two concurrent programmer threads against the same spec/task is
outside either agent's authority; and any future task requiring an
unfixed/fixed swap of a shared file (my Step 3/5) should isolate via a
private worktree or sandbox copy rather than mutating the shared main tree
directly -- the other session's `git worktree add` for its own offline-delta
measurement is the safer pattern and I did not use it for my live
measurement, which is what most likely caused their incident.

---

## Step 1 -- Anchors confirmed (before any edit)

Grepped against `flexicon/code/BaseOperations.py` at task start:

| Anchor | Found | Unique? |
|---|---|---|
| `def _apply_props_loop(` | :319 | yes |
| `tgt_handle = target_ws_by_id.get(tgt_ws_id)` | :360 | yes (`grep -c` == 1) |
| `# Target lacks this WS; skip silently.` | :362 | yes |
| `ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()` (read-only, inside `ApplySyncableProperties`) | :1307 | yes within this file (not repo-wide -- expected per spec section 3) |

No anchor missing or duplicated; proceeded. Post-fix, `_apply_props_loop`
moved to :420 (99 lines added above it for the two new module-level
functions); the resolution call site is now
`tgt_handle = _resolve_ws_handle(target_ws_by_id, tgt_ws_id, _index_cache=_ws_resolve_cache)`;
`ApplySyncableProperties`'s own untouched build moved to :1419-1421.

## Step 4 -- The fix (D4-T1)

Exactly two new symbols added to `flexicon/code/BaseOperations.py`, both
module-level per C-D4-7:

- `_normalize_ws_tag(tag)` -- `tag.replace("_", "-").lower()`, with a
  comment naming `WritingSystemOperations._NormalizeLangTag` as the form
  mirrored (not imported) and cross-referencing finding F3.
- `_resolve_ws_handle(target_ws_by_id, tgt_ws_id, _index_cache=None)` --
  exact match first (byte-for-byte unchanged), normalized fallback second
  (lazy index, built at most once via the caller-supplied `_index_cache`
  dict), ambiguity (>=2 distinct handles) raises `FP_ParameterError` naming
  both spellings and their handles, absent WS returns `None` (unchanged
  Defect-3 fallthrough).

`_apply_props_loop` itself changed only at its resolution line (now calling
`_resolve_ws_handle`) plus one new line initializing a shared
`_ws_resolve_cache = {}` once per call. No other line in the function
changed. No map-build site touched; `System/WritingSystemOperations.py`,
`Grammar/PhonemeOperations.py`, `Lexicon/ExampleOperations.py` not touched
(confirmed by `git diff --stat` below).

## Steps 2-3, 5 -- Live verification (D4-T3)

**Project:** `target_sandbox` only. **Test file:**
`tests/operations/test_issue250_ws_case_divergence.py`. Predictions
committed at `302d266` before any live run (evidence file predates both
live invocations).

### Unfixed-code run

Restored the pre-fix blob (`a32d94151fee1c3c62ccc33e71f3253990b0181a`,
hash-verified against `HEAD:flexicon/code/BaseOperations.py` at the task's
starting commit) via scratchpad copy + `cp` (never `git checkout`), then:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue250_ws_case_divergence.py -m requires_live_project -q
```

`tests/live_status.json` -> `"run_mode": "live"`. **2 FAILED, 1 SKIPPED**:

- `test_d4a_ws_map_case_divergent_resolves`: FAILED -- `got ''`, predicted
  and confirmed.
- `test_d4b_no_ws_map_source_id_case_divergent_resolves`: FAILED -- `got
  ''`, predicted and confirmed.
- `test_d4c_separator_divergent_resolves`: SKIPPED (loud) both before and
  after -- `target_sandbox`'s only two writing systems, `en`
  (999000001) and `etu` (999000002), have no `-`/`_` separator to flip.
  This is a live-evidence gap for D4-c specifically (disclosed, not
  silent); C-D4-5's separator path is proven offline instead in
  `test_issue250_defect4_ws_resolution.py`.

This is the required acceptance-criterion-2 demonstration: the pre-fix drop
is measured, not assumed, for D4-a and D4-b.

### Fixed-code run

Restored the fixed blob (`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db`,
hash-verified) and re-ran the identical command.

`tests/live_status.json` -> `"run_mode": "live"`. **2 PASSED, 1 SKIPPED**:

- `test_d4a_ws_map_case_divergent_resolves`: PASSED -- `post ==
  "TEST_D4a"`.
- `test_d4b_no_ws_map_source_id_case_divergent_resolves`: PASSED -- `post
  == "TEST_D4b"`.
- `test_d4c_separator_divergent_resolves`: SKIPPED, same reason.
- C-D4-6 assertions (embedded per-test): writing-system count, `CurVernWss`
  (`"etu"`), `CurAnalysisWss` (`"en"`) unchanged in both passing tests.

Post-write values were read back by re-fetching the object fresh via
`project.Object(hvo)` cast to `IPartOfSpeech` (not the stale pre-write
reference) -- required a small fix to the test file (see below).

**A real bug found and fixed in my own test file along the way:**
`project.Object(hvo)` returns the generic `ICmObject`/`ICmPossibility`
base, which has no `.Name` attribute; `POSOperations.GetName()` needs the
concrete `IPartOfSpeech` cast on every re-fetch. Fixed via a
`_refetch_pos()` helper with a lazily-imported `IPartOfSpeech` (so the
module still collects on machines without FieldWorks installed).

## Step 6 -- Offline delta

Command (identical both sides):
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q
```

**Before** (unfixed blob restored via `cp`, `--ignore=tests/operations/test_issue250_defect4_ws_resolution.py`
since that file imports fix-only symbols and cannot even collect against
unfixed code): `2 failed, 350 passed, 504 deselected`.

**After** (fixed blob restored, full command, no ignore): run **five times
total** across this session (three consecutively right after D4-T2 was
authored, once more after the transient scratch-file scare described in
the concurrency section, once more as a final confirmation at the very end)
-- **all five agreed**: `2 failed, 371 passed, 504 deselected`.

**Delta: +21 passed (exactly the new `test_issue250_defect4_ws_resolution.py`
suite, which by design only passes with the fix present), 0 change in
failures, same two known-foreign failures with unchanged messages.** Zero
offline-suite regressions (acceptance criterion 3).

The other session independently measured the same delta via a disposable
`git worktree` pinned to `e6a9492` (giving `501` rather than `504`
deselected on its "before" side, because that worktree predates either
session's new test files entirely, whereas my in-tree "before" run already
had the live test file present and only excluded the fix-dependent offline
file). Both measurements independently confirm the same conclusion; see
the evidence file's "CONCURRENCY DISCLOSURE" and cross-check note for the
full reconciliation.

**Determinism triple (the three AFTER-side runs required by Step 6, taken
from among the five total described above):** run 1 `2 failed, 371 passed,
504 deselected`; run 2 (same shell) `2 failed, 371 passed, 504 deselected`;
run 3 (env vars explicitly cleared to approximate a fresh shell) `2 failed,
371 passed, 504 deselected`. All three agree -- not `FAIL: unfalsifiable`.

**Known-foreign red set, checked and unchanged:**
- `tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`
- `tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_depth_restored_on_exception`
- `tests/test_flexlibs2_alias_ratchet.py::TestFlexlibs2AliasIsInboundOnly::test_no_executable_flexlibs2_imports_outside_alias_package`
  (checked separately, outside the `tests/operations tests/contract` pinned
  subset since it lives at `tests/` top level; confirmed still the sole
  failure there, unchanged).

No fourth failure, no changed message on any of the three.

## D4-T2 resolution-site ratchet

`tests/operations/test_issue250_defect4_ws_resolution.py::TestResolutionSiteRatchet::test_exactly_three_resolution_sites_exist`
passes: **1 passed**. Confirmed independently by a separate `git grep` at
the same commit:
```
target_ws_by_id\.get(\|ws_map\.get(src_ws_id
```
under `flexicon/code/`, excluding `build/lib/` (naturally excluded since
the scan root is `flexicon/code/`, a different top-level directory), returns
hits in exactly `BaseOperations.py` (x2, my own new helper + the unchanged
`ws_map.get` line), `Grammar/PhonemeOperations.py` (x2), and
`Lexicon/ExampleOperations.py` (x2) -- the same three files, no fourth. The
ratchet's own file-set assertion agrees. (A transient fourth-site failure
observed mid-session was the other agent's own deliberate
`_scratch_ratchet_probe.py` bites-when-mutated proof, not a defect -- see
concurrency section.)

Full offline D4-T2 suite: **21 passed** (exact-match-first via a counting
fake proving zero index builds on an all-hits path; D4-a/b/c resolve;
ambiguity raises naming both spellings; shared-handle non-ambiguity does
not raise; genuinely-absent WS still hits the unchanged silent `continue`;
index built at most once across multiple properties/alts sharing one
`_index_cache`; the ratchet).

## Coverage boundary (acceptance criterion 8)

Stated explicitly, not implied, in three places: the evidence file's
"Coverage boundary" section (written before either live run), the
CHANGELOG.md `### Fixed` entry (committed by the other session, reviewed
and confirmed compliant), and this report.

**This fix reaches `BaseOperations._apply_props_loop` ONLY -- 1 of the 3
closed-enumeration resolution sites** (verified by two independent greps at
`b3ba083b`, re-confirmed above at the final commit). It does **NOT** reach:

1. `Grammar/PhonemeOperations.__ApplyBasicIPASymbol` -- builds its own
   `target_ws_by_id`, runs its own exact-case `dict.get` loop, never calls
   `_apply_props_loop` or `_resolve_ws_handle`.
2. `Lexicon/ExampleOperations.ApplySyncableProperties`'s `TranslationsOC`
   loop -- same self-resolving shape.

**The asymmetry, spelled out:** after this fix, a phoneme's
`Name`/`Description` alts (which delegate to `super().ApplySyncableProperties`
and therefore to `_apply_props_loop`) will be saved under a divergent
case/separator spelling, while that **same phoneme's** `BasicIPASymbol` alt
will still be silently dropped under the identical divergent spelling. Both
sites are out of scope by fence 1.2/C-D4-2 ruling, not oversight; closing
them is refactoring work needing the user's approval to file (findings
F2/F5). The D4-T2 ratchet is the machine-checkable half of this boundary.

## `git diff --stat` (acceptance criterion 6), `e6a9492` (last commit before
any D4 work) to final `HEAD` (`1705e10a`)

```
 CHANGELOG.md                                                    |  31 ++
 flexicon/code/BaseOperations.py                                 | 115 +++++-
 specs/.../evidence/live-D4-T3.md                                | 409 ++++++++
 specs/.../reviews/cycle7-archivist-D4-T4.md                     | 221 ++++++
 specs/.../reviews/cycle7-programmer-D4-T1-T2-T5.md              |  96 +++++
 tests/operations/test_issue250_defect4_ws_resolution.py         | 420 +++++++++
 tests/operations/test_issue250_ws_case_divergence.py            | 291 ++++++++
 7 files changed, 1582 insertions(+), 1 deletion(-)
```

Zero hits in `flexicon/code/System/WritingSystemOperations.py`,
`flexicon/code/Grammar/PhonemeOperations.py`, or
`flexicon/code/Lexicon/ExampleOperations.py` (confirmed by an explicit
scoped `git diff --stat` against those three paths, empty output). None of
the 13 section-3 build sites touched. `tests/conftest.py` untouched.

## D4-T5 (CHANGELOG.md)

Committed by the other session as `8c679ed`; reviewed in full and confirmed
to state the bug-fix-not-breaking-change framing (C-D4-3 step 1), the new
`FP_ParameterError` ambiguous-spelling failure mode, and the full
acceptance-criterion-8 coverage boundary naming both unreached apply paths.
No further edit needed.

## D4-T6 -- explicitly NOT done

No GitHub comment posted, no issue opened/closed/commented on. Per
instructions, this needs the user's approval and is scheduled separately.

## Scope compliance

- Only `flexicon/code/BaseOperations.py` changed in production code (by the
  converged fix); no other production file touched.
- No map-build site edited; `System/WritingSystemOperations.py`,
  `Grammar/PhonemeOperations.py`, `Lexicon/ExampleOperations.py` untouched.
- `tests/conftest.py` untouched.
- The silent `continue` (Defect 3) is unchanged; no drop was converted to a
  raise, only to a save.
- No `git add -A`/`git add .`/`git add -u`/`git commit -a` used. New files
  were staged individually by exact path immediately before committing
  (`git add -- <exact paths>` followed by `git commit --only` in the same
  shell invocation) since git has no mechanism to commit a never-tracked
  file without staging it -- `git commit --only`/`--include` alone were
  confirmed (via a scratch-repo experiment) to silently no-op on untracked
  paths. Already-tracked files were amended via `git commit --only` alone,
  no staging. No destructive git command was run.
