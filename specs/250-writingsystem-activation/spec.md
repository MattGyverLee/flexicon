# SPEC -- 250-writingsystem-activation / **DEFECT 4 ONLY**

**Repo:** flexicon, branch `main`
**Issue:** #250, **Defect 4 in isolation** (case/separator normalization divergence
between the writing-system lookup helpers and the sync write path's
`{ws.Id: ws.Handle}` maps).
**Status:** SCOPED, contract frozen below. **NOT YET DISPATCHED.**
**Sequencing:** dispatch only AFTER `specs/feature-structure-sync-gap` clears its
**Checkpoint 2b gate** (T4 + T5). See section 6 for the full sequencing ruling --
this micro-spurt has a *window*, not merely a predecessor.
**Scope:** Defect 4. **Defects 1, 2 and 3 of #250 are OUT** and stay queued behind
`feature-structure-sync-gap` reaching `feature_complete`. Section 1 is the fence
and it is enforceable; read it before writing any code.

---

## 0. One-paragraph problem statement

`WritingSystemOperations._NormalizeLangTag` lowercases and folds `_` -> `-`, so
`Exists()` / `_GetWSByTag()` treat `en_US`, `en-us` and `en-US` as the same
writing system. The sync write path disagrees: every `{ws.Id: ws.Handle}` map in
the repo is keyed on the **exact-case** `ws.Id`, and the resolution step in
`BaseOperations._apply_props_loop` is a plain `dict.get`. A caller who learned a
tag from the normalization-tolerant helpers (or who simply types `en-us`) hands
that string to `ws_map`, the `.get` misses, and the alt is dropped by a
documented `continue` that emits no diagnostic. **This half of #250 needs no
special project state and fires today.** The fix is a normalized **fallback at
the point of lookup** -- deliberately NOT at the 13 map-build sites (section 4,
C-D4-2 explains why that distinction is the whole ballgame).

---

## 1. THE FENCE (enforceable -- read before coding)

### 1.1 What this task MAY touch

Exactly two symbols, both in `flexicon/code/BaseOperations.py`:

1. `_apply_props_loop` -- the multistring writing-system **resolution step** only.
2. One new private module-level helper in the same file (name suggestion:
   `_resolve_ws_handle(target_ws_by_id, tgt_ws_id)`), plus a normalization helper
   if one is needed.

Plus new tests, plus a `CHANGELOG.md` entry, plus this spec's evidence file.

### 1.2 What this task MUST NOT touch

- **`flexicon/code/System/WritingSystemOperations.py` -- NOT AT ALL.** Not
  `Exists`, not `Create`, not `GetAll`, not `_GetWSByTag`, not
  `_NormalizeLangTag`, not the docstrings. Every one of those is Defect 1/2/3
  territory.
- **The 13 `{ws.Id: ws.Handle}` map-build sites** (inventory in section 3). They
  stay exactly as they are. This is a hard contract requirement (C-D4-2), not a
  preference.
- `FLExProject.__NormaliseLangTag` (`FLExProject.py:3618`) and its four callers.
  It normalizes in the **opposite direction** (`-` -> `_`) and feeds a different
  lookup path. Unifying the normalizers is a separate issue (section 7, F3).
- `ProjectSettingsOperations._GetWSByTag` / `_NormalizeLangTag` (the third copy).
- `BaseOperations._apply_props_loop`'s `fill_gaps` semantics, the
  `isinstance(value, dict)` dispatch at `:346-353`, or anything to do with
  feature structures. The dict-dispatch hazard is
  `specs/feature-structure-sync-gap`'s C6 and is owned there.

### 1.3 Questions that are OUT OF SCOPE -- do not answer them, do not act on them

A programmer picking this up will notice all four of these. Noticing them is
correct; acting on them is scope drift and a QC rejection. If you believe one of
them **blocks** Defect 4, **stop and hand off** with the blocker named -- do not
decide it.

1. "`Exists`'s docstring says active-only but the body scans the whole store --
   which side is right?" **OUT.** That is Defect 1, and it is a contract
   decision with two defensible answers and opposite blast radii.
2. "`Create` refuses a store-present tag, so there is no way to activate one --
   shouldn't `Create` activate it?" **OUT.** Defect 2.
3. "There is no public `Activate` / `AddToCurrent*WritingSystems` API at all --
   isn't the real bug the missing method?" **OUT.** That is arguably the true
   root cause of #250 and it is exactly why Defects 1-3 need their own freeze
   cycle rather than a bolt-on.
4. "The silent `continue` should raise / warn instead of dropping." **OUT.**
   That is Defect 3, and it is *also* the site
   `specs/feature-structure-sync-gap`'s C6 routes around; strictening it before
   that feature's T6-T8 land would turn a forgotten `pop` into a misattributed
   writing-system error. Defect 4 **converts a drop into a save**; it must not
   convert a drop into a raise.

### 1.4 The one-sentence test for scope drift

> Defect 4 makes an **already-active, already-present** writing system resolvable
> under a differently-cased or differently-separated spelling. It never changes
> **which** writing systems exist, **which** are active, or **whether** a miss is
> loud.

If a change you are contemplating fails that sentence, it is out of scope.

---

## 2. Ground truth (code-read, 2026-09-07; live measurement is D4-T3)

### 2.1 The mechanism, end to end

**Capture** (e.g. `POSOperations.GetSyncableProperties`, `POSOperations.py:1155`):

```python
all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}
...
for ws_id, ws_handle in all_ws.items():
    text = ITsString(prop_obj.get_String(ws_handle)).Text
    if text:
        ws_values[ws_id] = text          # key = SOURCE project's exact-case ws.Id
```

**Apply** (`BaseOperations.ApplySyncableProperties`, ~`:1306-1308`):

```python
target_ws_by_id = {
    ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()
}                                        # key = TARGET project's exact-case ws.Id
```

**Resolution** (`BaseOperations._apply_props_loop`, ~`:354-364`):

```python
for src_ws_id, text in value.items():
    if not text:
        continue
    tgt_ws_id = (ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id)
    tgt_handle = target_ws_by_id.get(tgt_ws_id)      # <-- EXACT-CASE dict.get
    if tgt_handle is None:
        # Target lacks this WS; skip silently. Callers wanting
        # strict mapping should pre-validate ws_map.
        continue                                      # <-- THE SILENT DROP
```

### 2.2 Three distinct ways Defect 4 fires (the issue names only the first)

| # | Trigger | Caller at fault? | Needs special project state? |
|---|---|---|---|
| **D4-a** | Caller passes `ws_map={"en": "en-us"}` against a target whose `ws.Id` is `en-US` | yes, but the mismatch is undetectable to them -- `Exists("en-us")` returned True | **no** |
| **D4-b** | **No `ws_map` at all.** Source LDML spells `en-US`, target LDML spells `en-us`. `src_ws_id` passes through unchanged and misses. | **no -- caller did nothing wrong** | two projects that disagree on subtag case |
| **D4-c** | Separator divergence: caller passes `en_US`, store holds `en-US` (or vice versa). `_NormalizeLangTag` says they are equal; the dict says they are not. | no | **no** |

**D4-b is the dangerous one and the issue does not mention it.** BCP-47 subtag
case is not normative and LDML `Id` strings are case-preserving, so two
independently-created FLEx projects can legitimately disagree. In D4-b the caller
passes no `ws_map`, receives no error, and loses text. Any fix that only
normalizes the caller-supplied `ws_map` **value** fixes D4-a and D4-c but not
D4-b. The contract in section 4 covers all three; a fix that misses D4-b is
incomplete.

### 2.3 There are three normalizers and two run in opposite directions

| Symbol | Body | Canonical form produced |
|---|---|---|
| `WritingSystemOperations._NormalizeLangTag` (`:937-947`) | `tag.replace("_", "-").lower()` | **hyphen**, `en-us` |
| `ProjectSettingsOperations._NormalizeLangTag` (3rd copy, used at `:1093`) | same as above | **hyphen**, `en-us` |
| `FLExProject.__NormaliseLangTag` (`:3618`) | `tag.replace("-", "_").lower()` | **underscore**, `en_us` |

So "just normalize it" is underspecified: the repo already contains both
canonical forms. **This spec picks hyphen-lowercase** (C-D4-1) because it matches
BCP-47/LDML canonical form and two of the three existing copies. `FLExProject`'s
inverted copy is **not** changed here (fence 1.2); the divergence is recorded as
finding F3 for a follow-up issue.

---

## 3. Blast-radius inventory: 13 map-build sites, not 1

Issue #250 names only `BaseOperations.py:1306-1308`. The exact-case
`{ws.Id: ws.Handle}` idiom is repo-wide. Verified by grep, 2026-09-07:

| File | Line | Role |
|---|---|---|
| `BaseOperations.py` | 1307 | **apply** (the shared sync write path) |
| `Grammar/PhonemeOperations.py` | 1441 | **apply** (second, Phoneme-local build) |
| `Grammar/PhonemeOperations.py` | 1336 | capture |
| `Grammar/POSOperations.py` | 1155 | capture |
| `Grammar/NaturalClassOperations.py` | 1086 | capture |
| `Grammar/EnvironmentOperations.py` | 694 | capture |
| `Grammar/GramCatOperations.py` | 630 | capture |
| `Grammar/InflectionFeatureOperations.py` | 1694 | capture |
| `Grammar/MorphRuleOperations.py` | 916 | capture |
| `Grammar/PhonFeatureOperations.py` | 683 | capture |
| `Grammar/PhonologicalRuleOperations.py` | 1470 | capture |
| `Grammar/StratumOperations.py` | 287 | capture |
| `Lexicon/ExampleOperations.py` | 491 | capture |

**This inventory is why the fix must be lookup-only.** Normalizing 13 builds
would (a) collide head-on with `specs/feature-structure-sync-gap` T6-T8, which
add five *more* sync implementations and will almost certainly add more rows to
this table, and (b) risk **collapsing two distinct writing systems onto one key**
-- silent data loss strictly worse than the bug being fixed. A fallback at the
lookup does neither. See C-D4-2 and C-D4-3.

---

## 4. Frozen contract (C-D4-1 .. C-D4-6)

### C-D4-1 -- Canonical form is hyphen-lowercase

Normalization is `tag.replace("_", "-").lower()`, matching
`WritingSystemOperations._NormalizeLangTag`. Do **not** import that method
(fence 1.2 forbids touching that module, and `BaseOperations` must not depend on
an Operations subclass); replicate the two-operation expression locally with a
comment naming `WritingSystemOperations._NormalizeLangTag` as the form it
deliberately mirrors, and cross-referencing finding F3 (the inverted
`FLExProject` copy).

### C-D4-2 -- The fix lands at the LOOKUP, not at the 13 BUILDS (FROZEN)

`_apply_props_loop` receives `target_ws_by_id` already built by its caller and
makes no runtime lookups of its own (its own docstring says so). The fix
**derives a normalized side-index from whatever dict it was handed** and consults
it only on an exact-match miss. Consequences, all of them required:

- **Zero call-site changes.** None of the 13 builds is edited.
- **No new idiom for `feature-structure-sync-gap` T6-T8 to adopt.** Their
  exact-case builds keep working and inherit the fix for free by routing through
  `_apply_props_loop`.
- The frozen FS contract is not amended, and no FS live evidence is invalidated.

If an implementer concludes lookup-only is infeasible, that **invalidates the
sequencing ruling in section 6** -- stop and hand off (`needs_human`); do not
expand to the builds.

### C-D4-3 -- Exact match first, normalized fallback second, ambiguity RAISES

```
1. exact:      handle = target_ws_by_id.get(tgt_ws_id)          -> hit? done.
2. normalized: look up normalize(tgt_ws_id) in a normalized index
               built from target_ws_by_id's keys.
   2a. exactly one distinct handle  -> use it.
   2b. two or more DISTINCT handles -> raise FP_ParameterError naming the
       ambiguous spellings and their handles. NEVER pick one.
   2c. no entry                     -> fall through to the existing silent
       `continue`, unchanged (that is Defect 3, and it stays OUT).
```

**Step 1 must come first and must be untouched.** Every write that succeeds
today takes step 1 and must be byte-for-byte unaffected -- this is what makes
Defect 4 a strict drop-to-save conversion that cannot alter existing behaviour,
and it is the basis of the zero-regression claim in section 5.1.

**Step 2b is not defensive padding.** Distinct keys normalizing to the same form
mean the caller's intent is genuinely undeterminable, and guessing writes text
into the wrong writing system -- a corruption, not a drop. Raising here mirrors
the "never guess" ruling frozen as C1 in `specs/feature-structure-sync-gap`
(an ambiguous `slot` raises rather than picking a default). Keys that normalize
together but share **one** handle are not ambiguous; dedupe by handle before
counting.

### C-D4-4 -- The normalized index is built at most once per apply call

Build it lazily on first miss and reuse it for the remaining writing systems in
that call. Do not rebuild per writing system (`_apply_props_loop` iterates all
alts of all properties), and do not build it eagerly -- the overwhelmingly common
case is all-exact-hits, which must stay allocation-free.

### C-D4-5 -- Covers all three trigger paths (D4-a, D4-b, D4-c)

Normalization applies to `tgt_ws_id` **after** the `ws_map` indirection, i.e. to
the value actually looked up. This single placement covers a caller-supplied
`ws_map` value (D4-a), a passed-through `src_ws_id` with no `ws_map` at all
(D4-b), and a separator mismatch (D4-c). A fix that normalizes only inside the
`ws_map.get(...)` call misses D4-b and is rejected.

### C-D4-6 -- Never activates, never creates, never widens to the store

The resolved handle must come from the dict that was passed in -- which the
caller built from `WritingSystems.GetAll()` (active-only). Defect 4 must not
consult `AllWritingSystems`, must not call `AddToCurrent*WritingSystems`, and
must not alter `CurVernWss` / `CurAnalysisWss`. Asserted directly by a test
(section 6.4, step 6). This is the machine-checkable form of fence 1.4.

---

## 5. Task list

- [ ] **D4-T1** Add the normalized-fallback resolution to
      `BaseOperations._apply_props_loop` per C-D4-1..C-D4-6. Locate the target by
      **symbol and literal**, not by line number (section 6.1). Report the line
      numbers you actually found.
- [ ] **D4-T2** Offline tests: exact-match-first preserved (a hit never consults
      the index); D4-a, D4-b and D4-c each resolve; ambiguity (`en-US` and
      `en-us` -> two distinct handles) raises `FP_ParameterError` naming both;
      keys normalizing together with one shared handle do **not** raise;
      genuinely-absent WS still hits the unchanged silent `continue`; the index
      is built at most once (assert via a counting fake). These run against
      `_apply_props_loop` directly with fabricated dicts -- it is a pure helper
      designed for exactly that (its docstring cites T-S3a).
- [ ] **D4-T3** Live verification on **`target_sandbox`** -- shape frozen in
      section 6.4. **Predictions committed BEFORE the run** (repo precedent:
      commits `be42aaf`, `a580f7b`, `558654e`). Both sides measured: the test
      must be run against **unfixed** code first and demonstrate the drop, then
      against fixed code and demonstrate the save. Evidence ->
      `specs/250-writingsystem-activation/evidence/live-D4-T3.md`,
      `run_mode: live` required.
- [ ] **D4-T4** Re-verify the section 3 inventory by grep and report any drift
      (T4/T5 of the FS feature may have moved
      `PhonemeOperations.py:1441`/`:1336`). **Report only -- do not edit those
      sites** (C-D4-2). Settle finding F2 explicitly.
- [ ] **D4-T5** `CHANGELOG.md` `[Unreleased] ### Fixed`. This is a **bug fix, not
      a breaking change**: no currently-succeeding write changes behaviour
      (C-D4-3 step 1). Note the new `FP_ParameterError` on ambiguous spellings as
      the one new failure mode.
- [ ] **D4-T6** Post a comment on #250 recording that Defect 4 is fixed
      independently, that Defects 1-3 remain open, and that the issue must NOT be
      closed. **Do not close #250.** Filing/closing needs the user's approval.

## 5.1 Acceptance criteria

1. D4-a, D4-b and D4-c all resolve to the correct existing handle, proven live
   with a post-write value **re-read from the LCM** after re-fetching the object
   (asserting on the value passed in proves nothing).
2. The **pre-fix drop is demonstrated**, not assumed -- an unfixed-code run
   showing the alt still empty after apply.
3. Zero offline-suite regressions. Baseline to beat is whatever the FS
   Checkpoint 2b gate recorded (1290+ at cycle 3; re-measure, do not assume).
4. Ambiguous spellings raise `FP_ParameterError` naming both.
5. `CurVernWss` / `CurAnalysisWss` and the writing-system count are unchanged
   across the whole live run (C-D4-6).
6. `git diff --stat` touches **only** `BaseOperations.py`, new test files,
   `CHANGELOG.md`, and this spec's tree. Any hit in
   `System/WritingSystemOperations.py` is an automatic rejection.
7. None of the 13 section-3 build sites is modified.

---

## 6. Sequencing and collision rulings

### 6.1 Re-locating the target after T4 (do not trust line numbers)

T4 adds `_ApplyFeatureStruc` to `BaseOperations.py` and de-duplicates two private
`__ResolveByGuid` copies, so **every line number in this spec below ~320 is
stable but everything after it may have shifted**, and T5 will shift more. Anchor
on symbols and literals:

- Enclosing function: `def _apply_props_loop(` (module-level, currently `:319`).
- The exact resolution line: literal
  `tgt_handle = target_ws_by_id.get(tgt_ws_id)`.
- The drop site: the comment literal `# Target lacks this WS; skip silently.`
- The caller's build (read-only reference): the literal
  `ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()` inside
  `def ApplySyncableProperties(`.

Confirm each anchor is **unique** in the file before editing (the build literal
is *not* unique repo-wide -- section 3 -- but is expected unique within
`BaseOperations.py`). Record the found line numbers in the D4-T1 report and note
any drift from this spec. If an anchor is missing or duplicated, stop and hand
off: it means T4/T5 restructured the function and this contract needs re-freezing.

### 6.2 Normalize at build, at lookup, or both? -> **LOOKUP ONLY**

Ruled in C-D4-2. The three reasons, in force order:

1. **It is the only shape that does not collide with T6-T8.** Normalizing the
   builds establishes a new idiom that the five sync implementations T6-T8 add
   would have to adopt -- under a contract already frozen without it. A lookup
   fallback gives those five sites the fix for free with no contract amendment.
2. **Normalizing the builds can lose data.** Two distinct keys folding to one
   normalized key silently overwrite each other in a dict comprehension. At the
   lookup, the same collision is *detectable* and raises (C-D4-3 step 2b).
3. **Lookup-only is provably zero-regression.** Exact-match-first means every
   write that succeeds today follows an unchanged path; the new code executes
   only where a silent drop occurs today. "Both" buys nothing over "lookup" and
   inherits every cost of "build".

### 6.3 Blast radius vs. T6-T8: **safe in the 2b -> T6 window, conditionally**

**Plainly: it does not have to wait for T8. The window between the Checkpoint 2b
gate and T6 is the best time to land it** -- but only in the C-D4-2 lookup-only
shape. Conditions, all three of which must hold at dispatch time:

1. The fix touches no map-build site (C-D4-2). If that proves infeasible, it
   waits until after T8.
2. Live verification runs on **`target_sandbox`**, not the in-place Target. This
   removes the live-Target contention that was reason (c) of the original
   not-in-parallel ruling.
3. Checkpoint 2b's gate has cleared and is committed, so `BaseOperations.py` has
   no uncommitted FS work in it. Two agents editing that file concurrently is
   what nearly cost cycle 3 an uncommitted copy of it.

**This refines rather than contradicts the earlier not-in-parallel ruling.** That
ruling's reason (b) was that #250 changes *what `target_ws_by_id` is built from*
-- store vs. active -- which would invalidate FS live evidence. That is Defects
1-3 territory and remains queued behind `feature_complete`. Defect 4 carved this
way changes neither the build source nor the loudness of a miss; it changes only
how an already-present key is matched. Reason (a) (the shared strictening site)
likewise does not apply: Defect 4 converts a drop into a **save**, never into a
raise, so a forgotten C6 `pop` in T6-T8 still fails exactly as it does today,
with the same diagnostics. And feature structures never reach this branch at all,
because C6 pops them before `super()`.

**Landing it before T6-T8 is actively better than after:** T6-T8 add five new
sync implementations whose multistring alts inherit the fix immediately, instead
of shipping five new instances of a known-buggy resolution and sweeping them
later.

### 6.4 Live-verification shape (D4-T3)

**Project: `target_sandbox`.** It is a write-path test, so per CLAUDE.md the
Target family is correct rather than Sena 3; the sandbox (fresh tempdir copy of
the Target `.fwbackup`) is the non-leaking form, cannot be blocked by an open
FieldWorks, and keeps this micro-spurt off the resource the FS feature is using.
Sena 3 is wrong here -- no pre-existing populated data is needed. The real
in-place Target is unnecessary and is the more destructive option.

**Why no special project state is needed -- and how to guarantee that.** Do not
hunt for a project that happens to spell a tag with an uppercase region subtag.
**Derive the mismatched spelling from whatever the sandbox actually has, by
flipping it**: read a real `ws.Id`, then case-flip it (`en` -> `EN`,
`en-US` -> `en-us`) and separator-flip it (`en-US` -> `en_US`). The test is then
portable across projects and self-evidently independent of project state, which
is precisely the reporter's "needs no special state" claim made machine-checkable.

**Concrete pre/post read-back:**

1. `ids = [(ws.Id, ws.Handle) for ws in project.WritingSystems.GetAll()]`.
   Record verbatim in the evidence file. Pick one `(canonical_id, handle)`.
2. Construct `flipped_case = <case-flip of canonical_id>` and
   `flipped_sep = canonical_id.replace("-", "_")`. Assert
   `flipped_case != canonical_id` (skip loudly, never silently, if the tag has no
   flippable character).
3. Create a `TEST_`-prefixed object in the sandbox (a POS is the cheapest -- its
   `Name` is a multistring and `POSOperations` capture/apply are already
   exercised). **Pre-state:** re-fetch it and assert
   `ITsString(pos.Name.get_String(handle)).Text` is empty.
4. **Act (D4-a):**
   `ApplySyncableProperties(pos, {"Name": {"en": "TEST_D4a"}}, ws_map={"en": flipped_case})`.
5. **Post-state:** re-fetch the object fresh (`project.Object(hvo)` or re-resolve
   by GUID -- do **not** reuse the pre-write reference) and read
   `ITsString(pos2.Name.get_String(handle)).Text`.
   - **Unfixed code -- predicted: still empty.** This is the proof Defect 4
     fires today.
   - **Fixed code -- predicted: `"TEST_D4a"`.**
6. **C-D4-6 assertions, both runs:** writing-system count unchanged, and
   `project.lp.CurVernWss` / `CurAnalysisWss` byte-identical to their pre-run
   values. The fix resolves to an existing WS; it never activates or creates one.
7. **D4-b (no `ws_map`):** apply `{"Name": {flipped_case: "TEST_D4b"}}` with
   **`ws_map=None`**, read back at `handle`. Same predicted before/after. This is
   the variant the issue omits and it must be covered live, not only offline.
8. **D4-c (separator):** repeat step 4 with `flipped_sep`.
9. **Ambiguity:** offline only (D4-T2) -- fabricating two live writing systems
   differing solely by case is not reliably possible on a case-insensitive
   filesystem, and forcing it would drift toward Defect 2. State that reasoning
   in the evidence file rather than leaving the gap silent.

**Invocation** (never bare `pytest` -- it executes ~322 live tests in place):

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue250_ws_case_divergence.py -m requires_live_project -q
```

`tests/live_status.json` must read `"run_mode": "live"`; a `"mock"` run proves
nothing and is reported as `FAIL: unverified`, never as a clean result.

---

## 7. Recorded findings (NOT changes in this task -- candidate follow-up issues)

Filing any of these needs the user's approval.

- **F1 -- Defect 4's real surface is 13 sites, not the 1 the issue names.**
  Section 3. Defect 4 as scoped here neutralises all 13 at the shared lookup, but
  the exact-case idiom itself remains the repo's default and will be
  copy-pasted again. A follow-up should introduce a single shared
  `_BuildWSHandleMap()` and retire the idiom -- **after** the FS feature's T6-T8,
  since those add more instances.
- **F2 -- `PhonemeOperations.py:1441` is a second, module-local apply-side
  build.** If Phoneme's apply path does its own resolution rather than delegating
  to `_apply_props_loop`, it will **not** inherit the Defect 4 fix. D4-T4 must
  determine which, and say so explicitly. If it self-resolves, that is a genuine
  gap in this fix and must be reported at handoff -- not quietly patched (it is
  one of the 13 fenced sites).
- **F3 -- Three normalizer copies, two inverted.** Section 2.3.
  `FLExProject.__NormaliseLangTag` produces `en_us` while
  `WritingSystemOperations`/`ProjectSettingsOperations` produce `en-us`. Two
  canonical forms in one codebase is a latent divergence of exactly the #250
  Defect 4 kind, one layer up. Candidate issue: unify on hyphen-lowercase behind
  a single shared utility (`Shared/string_utils.py` is the natural home).
- **F4 -- `_apply_props_loop`'s docstring advice is unfollowable.** It tells
  callers "wanting strict mapping should pre-validate `ws_map`", but the only
  available pre-validation is `Exists()`, which is normalization-tolerant and
  whole-store -- so it returns True for exactly the tags that then get dropped.
  This is the Defect 2 <-> Defect 4 interaction; it resolves when Defects 1-3 do.
  Recorded so the docstring is revisited then.
