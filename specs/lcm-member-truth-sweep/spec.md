# SPEC -- lcm-member-truth-sweep

**Campaign:** `lcm-member-truth-sweep`
**Issues in scope:** #302, #261, #283, #259, #303, #309 (six)
**Opened:** 2026-09-18 (cycle 1) | **Baseline commit:** `598f41e` (v4.8.0)
**Theme:** the v4.8.0 "silent-failure sweep" continued -- production code
that names LCM members which **do not exist on the receiving type**, and
therefore either silently does nothing (a `hasattr` guard returns False) or
raises `AttributeError` that a bare `except` then mislabels.

Cycle 1 was investigation only. **Zero production files were modified**
(confirmed by the main session via `git status --porcelain`); the only
artifacts are this spec, `tasks.md`, the three cycle-1 reviews, the live
evidence file, and one new live test file.

---

## 1. Cycle-1 inputs (read these, do not re-derive)

| Artifact | Contents |
|---|---|
| `reviews/cycle1-verification.md` | Live reflection + Sena 3 read-path ground truth. `run_mode: live`. |
| `evidence/live-cycle1-reflection.md` | The raw surface dumps and sampled counts behind it. |
| `reviews/cycle1-domain.md` | Domain ruling on the `OverlayOperations` rewrite (#303/#309). |
| `reviews/cycle1-explore.md` | Catalogue 1 (blast radius, 62 executable sites) + Catalogue 2 (25 ranked sibling bugs). |
| `tests/operations/test_lcm_member_truth_sweep.py` | 9 live-passing reflection ratchets pinning the ground truth below. |

---

## 2. Ground truth established (machine-checked, cycle 1)

### #259 -- `InflClassRA` on `IWfiMorphBundle`
- `IWfiMorphBundle`'s full 7-property surface contains **no** member of
  this concept under any name. Verdict is **(ii): navigate**, not rename.
- The real home is `IMoStemMsa.InflectionClassRA`, reached as
  `bundle.MsaRA -> cast_to_concrete(...) -> .InflectionClassRA`.
  `IMoStemMsa` is the **only** MSA subtype carrying it; `IMoInflAffMsa`
  and the `IMoMorphSynAnalysis` base do not.
- **The guard is mandatory, not defensive decoration.** Over 1932 real
  Sena 3 bundles: 94 have a null `MsaRA`, and 1144 of the 1838 non-null
  bundles carry a non-stem MSA subtype that **raises `AttributeError`**
  (it does not return `None`) on unguarded `.InflectionClassRA`.
- 10 executable production sites: `WfiMorphBundleOperations.py:335,336,
  385,386,1261,1313`; `WfiAnalysisOperations.py:589,590`;
  `WordformOperations.py:878,879`. `:1261`/`:1313` are unguarded and fail
  **loudly on every call**; the other six are silent data loss on copy/sync.

### #283 -- `LeftContextOA`/`RightContextOA` on `IPhEnvironment`
- Real names are `LeftContextRA`/`RightContextRA`, **Reference** Atomic
  (`IPhPhonContext`). The `...OA` names do exist -- but on `IPhSegRuleRHS`,
  a different type. Those two are the only types in the 257-type snapshot
  carrying either name.
- Live seeded probe (in `sena3_sandbox`, restored in a `finally:`): after
  `Duplicate(deep=True)`, re-reading by HVO shows the source contexts
  populated (152223/152224) and the **duplicate both `None`**. The current
  code implements **neither** reference nor clone semantics -- it silently
  drops the field. 0 of 44 pre-existing Sena 3 environments had populated
  contexts, which is why this survived undetected.
- 10 executable production sites in `Grammar/EnvironmentOperations.py`:
  `:494,495,550,551,634,637,641,646,649,653`. The `Duplicate` blocks are
  additionally wrapped in bare `except Exception: pass`.

### #302 -- `repos.RecordsOC` on `IRnResearchNbkRepository`
- Repository surface is `{Count, Singleton}` plus `{AllInstances, GetObject,
  TryGetObject, ...}`. No `RecordsOC`. Records live on
  `IRnResearchNbk.RecordsOC`, reachable via `lp.ResearchNotebookOA` or
  `repos.Singleton`. `ILangProject.ResearchNotebookOA` and
  `ILangProject.OverlaysOC` are both confirmed present in the snapshot.
- 3 executable sites: `Notebook/DataNotebookOperations.py:313, 393, 2530`
  (the issue text's "~2533" is off by three). `:232` (`AllInstances()`) is
  **correct and must not be touched**.
- No other Operations class makes this mistake: all 11 other
  `GetService(I*Repository)` sites consume the service via `AllInstances()`.

### #261 -- `self.project.project.GetObject(hvo)` on the raw `LcmCache`
- `LcmCache` has no `GetObject`. The house path is `self.project.Object(hvo)`
  -> `ServiceLocator.GetObject(...)`; precedent at
  `Grammar/EnvironmentOperations.py:714`.
- **One** occurrence of the broken pattern repo-wide:
  `Notebook/DataNotebookOperations.py:187`, inside `__GetRecordObject`.
- **True blast radius is 38 public methods**, not the one (`SetTitle`) the
  issue names -- every method routing through `__GetRecordObject` is broken
  on the int-HVO entry path. Severity amplifier: the `except` at `:190-196`
  catches the `AttributeError` and re-raises it as
  `FP_ParameterError("Invalid notebook record object or HVO: ...")`, so all
  38 **lie about the cause**.
- `ServiceLocator.GetObject` at `Lexicon/LexSenseOperations.py:1376,1481,1488`
  is the correct shape. Do **not** sweep it into this fix.

### #303 / #309 -- `OverlayOperations`
- `ICmOverlay`'s complete own-declared surface is exactly
  **`Name` (plain `System.String`), `PossItemsRC`, `PossListRA`**.
  `ICmPossibility.IsAssignableFrom(ICmOverlay)` is `False`. Overlays are
  owned project-wide at `ILangProject.OverlaysOC`. `IDsConstChart` has no
  overlay member anywhere in its hierarchy.
- 38 executable broken production lines; 11 broken public methods plus
  `_get_list_object` hard-coded to `return None` (#309), which in turn
  breaks all 12 inherited `PossibilityItemOperations` methods.
- Only `GetPossItems` works (fixed under #277). Do not regress it.

---

## 3. Rulings

These are binding for the rest of the campaign. Do not relitigate them;
escalate with evidence if you believe one is wrong.

**C1 -- #302 adopts the OWNERSHIP form, not the repository form.**
Rewrite the three sites to `self.project.lp.ResearchNotebookOA.RecordsOC`
and **delete the now-unneeded `GetService(IRnResearchNbkRepository)`
lookups** at `:306`, `:376`, `:2529`. Rationale: `.Singleton` appears zero
times in `flexicon/`, so either choice sets the house precedent -- and the
`lp.<Thing>OA` shape is already the house idiom
(`EnvironmentOperations.Duplicate`'s `self.project.lp.PhonologicalDataOA:610`;
`FLExProject.__init__`'s `self.lexDB = self.lp.LexDbOA:362`). Choosing it
introduces no new pattern at all. **Gated on Q1**: if `lp.ResearchNotebookOA`
is ever null where `repos.Singleton` is not, this ruling flips to
`repos.Singleton.RecordsOC` and that becomes the precedent instead.
Whichever survives Q1 must be written down in
`docs/API_ISSUES_CATEGORIZED.md` as the named house pattern -- a precedent
that exists in only one call site is not a precedent.

**C2 -- #302's `Count` caveat is CLOSED, and lex-verification was right to
flag it.** The committed contract snapshot shows
`IRnResearchNbkRepository.properties == ['Count', 'Singleton']`, so the
issue's `Count` claim holds. Pin it in the ratchet
(`test_lcm_member_truth_sweep.py`) rather than leaving it as prose. The
report's refusal to silently accept an unverified half-claim is exactly the
behaviour this campaign wants; it is recorded here as resolved, not as a
defect in the report.

**C3 -- `AllInstances()` at `:232` is correct.** Out of scope, hands off.

**C4 -- `tests/operations/test_datanotebook_duplicate.py` is DELETED AND
REWRITTEN, not re-run.** It never imports `DataNotebookOperations`; it
hand-re-types the `Duplicate` logic against a `_MockRepository` that
*defines* `RecordsOC` -- a member the real repository lacks. It passes today
and would keep passing no matter what production does. That is not a
bug-asserting test, it is a **non-test**: it consumed a maintainer's
confidence budget while verifying nothing. The rewrite MUST import the
production module and MUST carry a live-marked case; a replacement that is
still mock-only does not discharge this ruling.

**C5 -- mock fidelity is a campaign-level finding.** C4's failure mode
generalises: any hand-rolled mock that invents an LCM member can green-light
a bug permanently. A ratchet cross-referencing member names asserted by test
doubles against the 4096-name snapshot is in scope as a LOW-priority task
(T8.3), explicitly droppable if the campaign runs long. It is recorded so
the insight does not die with this spurt.

**C6 -- #261 is fixed ONCE, in `__GetRecordObject`, and the mask comes off
with it.** Route `:187` through `self.project.Object(hvo)`; all 38 methods
inherit the fix. Additionally narrow `:190-196` so a genuine `AttributeError`
is no longer laundered into `FP_ParameterError("Invalid notebook record
object or HVO")`. Chain the cause (`raise FP_ParameterError(...) from e`) at
minimum. Leaving the mask in place would preserve exactly the diagnostic
blindness that let a one-line defect hide behind 38 misleading error
messages.

**C7 -- #283's context copy becomes UNCONDITIONAL reference assignment.**
Fix the names to `LeftContextRA`/`RightContextRA` and assign
`duplicate.LeftContextRA = source.LeftContextRA` (likewise Right) **outside**
the `if deep:` block. Under Reference Atomic there is nothing to clone: a
duplicate environment should point at the same `IPhPhonContext` objects, and
gating that behind a flag is precisely the CLAUDE.md "do not add a flag for
behaviour that should be unconditional" anti-pattern (compare C8 of
`specs/242-paragraph-whitespace/spec.md`). The `clone_properties` /
`NewObject(ClassID)` machinery in those blocks is deleted, and so are the two
bare `except Exception: pass` swallows. **`deep` stays in the signature** --
it is pinned in `EnvironmentOperations.pyi:18` (`deep: bool = True`) -- but
becomes inert for this method and must be documented as such in the docstring
and CHANGELOG. See Q4.

**C8 -- `test_260_environment_resolver_gate.py:311-317` is INVERTED, not
deleted, in the same commit as the #283 fix.** It genuinely calls the
production method and asserts `result is None` as a deliberate "lock the
discovery" anchor, so it will go red on a correct fix -- by design. Keep the
class, keep its narrative docstring, flip the assertion, and add a pointer to
this spec so the next reader sees the discovery and its repair in one place.
Same treatment for the `test_2a_*`/`test_2d_*` anchors in
`test_lcm_member_truth_sweep.py`.

**C9 -- `Grammar/compound_rule.py:220,244` is NOT #283.** `_concrete` is
`IMoEndoCompound`/`IMoExoCompound`, and **neither** `...OA` nor `...RA`
context member exists on either type. A blind `OA -> RA` rename would be
wrong in both directions. It is a separate suspected bug (Catalogue 2 row 25)
and goes to the separate filing. Hands off in this campaign.

**C10 -- #259 is a NAVIGATION fix with two guards, never a rename.**
`bundle.MsaRA` -> null check -> `cast_to_concrete` -> narrow to `IMoStemMsa`
-> `.InflectionClassRA`. The 1144/1838 AttributeError figure makes the type
narrowing load-bearing, not stylistic. A fix that only renames the member, or
that guards with `hasattr` alone on the uncast object, fails this campaign's
bar.

**C11 -- `SetInflectionClass` is BLOCKED pending a domain ruling (Q2).**
An MSA can be shared by many morph bundles, so writing `msa.InflectionClassRA`
through a bundle handle may mutate every other bundle sharing that MSA -- an
action-at-a-distance write that the current API shape
(`SetInflectionClass(bundle, infl_class)`) does not advertise. Do not write
this path on a guess. The read path (`GetInflectionClass`) and the three
silent copy loops are unblocked and may proceed first.

**C12 -- #303/#309 follows the cycle-1 domain ruling verbatim.** Inherit
`BaseOperations` directly (not `PossibilityItemOperations` -- only 1 of 13
inherited methods survives); re-root on `ILangProject.OverlaysOC`; delete the
10 dead methods outright with a Category-10-style migration table and **no
deprecation shim** (precedent: `SegmentOperations.Create`/`Duplicate`,
`docs/API_ISSUES_CATEGORIZED.md:627-682`). The break is derisked by the fact
that **none of the 10 appear in the pinned `.pyi` surface**. Split across
three spurts (A: re-root + core CRUD; B: deletions + `PossItemsRC` write
surface; C: docs, `.pyi`, tests). `GetPossItems` is untouchable.

**C13 -- Catalogue 2 stays OUT of scope for behaviour change; the boundary is
REAFFIRMED, with one zero-cost carve-out and a named owner.**
The 22 high-confidence silent-data-loss siblings are plausibly a larger body
of harm than the six in-scope issues, and that is exactly why they must not be
absorbed: folding 22 unverified, snapshot-derived candidates into a six-issue
campaign converts a bounded, live-verified sweep into an unbounded one, and
the six would ship later and weaker for it. Concretely:

- **Durable record.** The catalogue is copied out of the reviews directory
  into `specs/lcm-member-truth-sweep/catalogue2-siblings.md` (T2.6), so it
  survives independently of a cycle-1 review file.
- **Carve-out (ratchets only, no behaviour change).** While a fix spurt
  already has `DataNotebookOperations.py` / `AnthropologyOperations.py` open,
  add live-reflection **absence assertions** for rows 1-4 and for
  `DataNotebookOperations.py:825` (`ILangProject` has no `RecTypesOA`) to
  `test_lcm_member_truth_sweep.py` (T2.5). This costs one reflection call
  each and upgrades those rows from "snapshot-derived, medium confidence" to
  "live-confirmed" -- the difference between an issue a maintainer can act on
  and one they must re-investigate. **No production line in those rows is
  edited.**
- **Owner and date.** The main session drafts
  `specs/lcm-member-truth-sweep/proposed-issues.md` at the END OF CHECKPOINT
  2 (T2.7) -- not at campaign end, where it would be the first thing cut.
  Filing is **`needs_human`**: I cannot authorise opening issues and neither
  can the main session. The batch is presented to the user for approval; on
  approval the main session files them with `gh` (after
  `gh repo set-default MattGyverLee/flexicon` -- this repo's `upstream`
  remote will otherwise resolve issue numbers against `cdfarrow/flexlibs`).
  If the user declines or defers, the proposal file stays in the repo as the
  record.

**C14 -- dispatch hygiene (process, binding on future cycles).** Cycle 1
instructed `lex-domain` and `Explore` to write their own report files; neither
has `Write`/`Edit` (`lex-qc`, `lex-author`, `lex-README` and `lex-synthesis`
are likewise read-only). Both had to paste full bodies back through the main
session, defeating the path-relay discipline. From cycle 2 on: **only
`lex-programmer` and `lex-verification` are asked to write their own
reports.** For read-only specialists the dispatch prompt must instead say
"return a report body of at most N words; the main session will persist it to
`<path>`", and the main session persists it. Budget that body into the
context cost when planning how many read-only specialists to run in one cycle.

---

## 4. Open questions

**Q1 -- Is `lp.ResearchNotebookOA` ever null, and is it the same object as
`repos.Singleton`?** Gates C1. Cheap live probe on both Target and Sena 3:
assert non-null on both, and assert HVO equality with `repos.Singleton`. If
it is ever null where `Singleton` is not, C1 flips. (T2.1)

**Q2 -- Does writing `msa.InflectionClassRA` through a bundle mutate other
bundles?** Gates C11 / `SetInflectionClass`. Needs (a) a live count of how
many Sena 3 bundles share an MSA with at least one other bundle, and (b) a
domain ruling on whether the write should be refused, warned about, or
silently accepted at this API level. (T4.4)

**Q3 -- Live `dir()` on a real `MoEndoCompound`/`MoExoCompound`.** Raises
Catalogue 2 row 25 from MEDIUM to HIGH (or clears it) before it is filed.
Snapshot compound-rule coverage may be partial. Cheap; fold into T2.5 if a
live session is already open. (T2.5b)

**Q4 -- Does any caller actually pass `deep=False` to
`EnvironmentOperations.Duplicate`?** Informs how loudly C7's inert parameter
must be documented. Grep `flexicon/`, `examples/`, `tests/`. If nothing does,
a docstring note plus a CHANGELOG line suffices; if something does, its
expectation must be stated explicitly. (T3.4)

---

## 5. Checkpoint plan

| # | Checkpoint | Issues | Why here |
|---|---|---|---|
| 1 | Ground truth + spec (**DONE**) | all six | Nothing could be planned before the member surfaces were known. |
| 2 | Notebook resolver + ownership | #302, #261 | Cheapest (4 executable lines), same file, and settles the `lp.<Thing>OA` precedent the rest may lean on. Carries the C4 test rewrite and the C13 catalogue hand-off. |
| 3 | Environment contexts | #283 | Self-contained; one file; the assertion inversion (C8) is planned, not a surprise. |
| 4 | Morph bundle inflection class | #259 | Largest guard surface; read path + copy loops first, write path gated on Q2. |
| 5 | Overlay re-root + core CRUD | #303/#309 | Domain spurt A. |
| 6 | Overlay deletions + `PossItemsRC` writes | #303/#309 | Domain spurt B. |
| 7 | Overlay docs, `.pyi`, tests | #303/#309 | Domain spurt C. |
| 8 | Campaign close | all | CHANGELOG, migration table, house-pattern note, proposed-issues presentation. |

Ordering rationale: ascending blast radius and ascending unresolved-question
count, so the precedent-setting decisions (C1, C6) land while the diff is
still small enough to review cheaply.

---

## 6. Standing gates (every task inherits these)

1. **Fixtures:** `target_sandbox` / `sena3_sandbox` (tempdir copies) by
   default. Prefer **Target** for anything that writes. Never run
   `scripts/restore_*.py` unattended -- if a task genuinely needs the real
   Target restored, stop with `status: needs_human`.
2. **Live verification is REQUIRED** for every task touching an Operations
   class, factory call, property setter, or the write path. Mock-only is
   `FAIL: unverified`, never a clean result.
3. **Evidence or it did not happen.** `tests/live_status.json` must read
   `"run_mode": "live"`, and each task writes
   `specs/lcm-member-truth-sweep/evidence/live-<task>.md` with the exact
   command, the `run_mode` value, pre-state and post-state **re-read from the
   LCM by HVO**, and a pass/fail line. Asserting on the value you just passed
   in proves nothing.
4. **Required invocation:**
   ```
   $env:FLEXLIBS_REQUIRE_LIVE = "1"
   python -m pytest <file> -m requires_live_project -q
   ```
   **Never bare `pytest`**, never `pytest --ignore=tests/contract` -- neither
   applies an `-m` filter, so both execute ~322 `requires_live_project` tests
   in place against real projects.
5. **Derive counts with `--collect-only`; "no tests collected" is a ZERO,
   never a pass.**
6. **Never write `flexlibs2` in anything new** (ratchet:
   `tests/test_flexlibs2_alias_ratchet.py`, issue #240).
7. **Commit-message hazard:** do not put a close/fix/resolve keyword
   immediately before an issue number unless GitHub should genuinely close it.
   `close #302's rewrite` fires. The `commit-msg` hook catches it; enable it
   once per clone with `git config core.hooksPath .githooks`.

---

## 7. Corrections to the cycle-1 reports

Recorded so later readers trust the reports with the right caveats.

- **`cycle1-explore.md` (c), `.pyi` claim -- PARTLY WRONG.**
  `EnvironmentOperations.pyi:18` **does** pin
  `Duplicate(item_or_hvo, insert_after=True, deep=True)`. Explore's "no stub
  edit required" holds only for `GetLeftContextPattern`/
  `GetRightContextPattern`, which are indeed absent from the stub. The `deep`
  parameter is pinned surface, which is why C7 retains it rather than
  removing it.
- **`cycle1-verification.md`, #302 `Count` caveat -- now CLOSED** by the
  committed snapshot (see C2). The caveat was correctly raised; it simply has
  an answer.
- **`cycle1-explore.md` (a), line number -- CONFIRMED against the source.**
  `Duplicate`'s `RecordsOC.Add` is at `:2530`, not the issue's "~2533".
