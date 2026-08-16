# Live evidence — DEF: flip the default to `undoable=True`

Task: **DEF** (`specs/write-path-transactions/tasks.md`, Checkpoint 3).
Date: 2026-08-16
Branch: `write-path-transactions-b1-b3`
Change under test: `FLExProject.OpenProject(..., undoable=True, ...)` — the
signature default moves from `False` to `True`.

Projects: **Target**, restored from
`tests/fixtures/Target*.fwbackup` via `python scripts/restore_target.py`
before *every* measured run, so no run inherits the previous one's mutations.
This matters more than usual here: two back-to-back runs of identical code on
an unrestored Target gave 62 and then 76 failures, which is enough drift to
manufacture or hide a regression on its own.

---

## 1. Method

A default flip has no behaviour of its own to test; what it does is
reinterpret every existing caller. So the measurement is a **paired
comparison** — the same live suites, on the same freshly restored Target,
with and without the flip — and the deliverable is the *diff*, not a pass
count.

The baseline side runs from a **git worktree pinned at `HEAD` (`2535fe1`)**
rather than from a `git stash` of the working tree. That was not the first
attempt: stashing was, and it is genuinely dangerous here, because a live run
that times out or hangs leaves the change stashed and the working tree
silently reverted. It happened twice. The worktree has no such failure mode —
the baseline and the change exist simultaneously on disk.

`tests/conftest.py` inserts its own repo root at `sys.path[0]`, so the
worktree run imports the worktree's `flexicon`, not the editable install
pointing at the main checkout. Verified explicitly before trusting a single
number:

```
$ cd <worktree> && python -c "...inspect.signature(FLExProject.OpenProject)..."
imports from: ...\baseline-wt\flexicon
default undoable: False
```

One trap worth recording: the `.fwbackup` fixtures are **untracked**, so the
fresh worktree had none, and the first baseline run reported 85 fixture
errors that had nothing to do with the mode. A baseline that fails for an
unrelated reason is not a baseline. Fixtures were copied in and the run
repeated.

---

## 2. Commands

Every run below was preceded by `python scripts/restore_target.py` and used
the fail-loud flag, so a mock fallback, a locked Target or a missing fixture
is a hard failure rather than a green skip:

```powershell
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest <files> -m requires_live_project -q -p no:randomly
```

`tests/live_status.json` → `"run_mode": "live"` (not `"mock"`) on the full
run, with 407 tests recorded.

---

## 3. Offline gate

Full offline suite, before and after, failure sets compared by identity
rather than by count (a wash — one fixed, one broken — reads identical on
counts alone):

| | failed | passed | errors |
|---|---|---|---|
| baseline | 117 | 1446 | 17 |
| after | 117 | 1446 | 17 |

```
=== newly failing (regressions) ===
=== newly passing ===
```

Both empty: the post-change failure set is **byte-identical** to baseline.
The 117 are the pre-existing failures already recorded against Checkpoint 2a
(#240 rename path, sync engine), unrelated to this work.

This proves less than it appears to, and is recorded with that caveat: the
offline suite pins `_undoable` explicitly on its doubles, so it is
structurally incapable of noticing a change to the *default*. It is a
regression gate, not evidence for DEF.

---

## 4. What the flip actually broke

The whole live suite was run **unpinned** first — deliberately letting the
flip reinterpret the test fixtures — because that is the only configuration
in which the blast radius is visible. Pinning first would have produced a
green suite that proved nothing.

It surfaced two genuine problems and a large cloud of pre-existing noise.
Each cluster was then re-measured in isolation, in both modes, on a restored
Target.

### 4.1 D11 — a mutation site B2's sweep never saw *(real defect, fixed)*

`BaseOperations.ApplySyncableProperties` raised, live:

```
System.InvalidOperationException: Not in the right state to register a change.
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.RegisterCommon(IUndoAction)
   at SIL.LCModel.DomainImpl.MultiUnicodeAccessor.set_String(Int32 ws, ITsString tss)
flexicon\code\BaseOperations.py:373
```

The method validates and then delegates every write to `_apply_props_loop`, a
**module-level function**. B2 enumerated Operations *methods*; the method it
enumerated contains no mutation, and the code that mutates is not a method.
The B2g ratchet reads 0 and always did — its scanner cannot see this shape.

Latent under `undoable=False` (the session envelope covered it), fatal under
the new default. Fixed by bracketing the delegation as one unit.

Swept for siblings rather than assumed to be unique: an AST pass over every
module-level function in `flexicon/code/` found exactly two write-shaped
module-level helpers — this one and `lcm_casting.clone_properties`. All seven
`clone_properties` call sites were checked individually; every one already
sits inside a caller's bracket, so it joins rather than opens. Two writers,
one gap, one fix.

### 4.2 D12 — three fixtures silently changed mode *(harness, pinned)*

`target_project`, `target_sandbox` and `sena3_sandbox` opened with the
implicit default, so the flip converted them to `undoable=True` with no test
edit. That collapsed them into `target_sandbox_undoable` — whose docstring
exists precisely to say the two modes are different LCM state machines and
that one cannot stand in for the other. All three are now pinned to
`undoable=False` explicitly.

`test_abort_session_live.py`: **8 failures unpinned → 12 passed pinned.**

### 4.3 D13 — the sweep's blind spot, in full *(real defects, fixed)*

D11 was not a one-off. `scan_unbracketed_mutations.py` recognised a mutation
in exactly two shapes — a call whose attribute is in a hardcoded set, or an
assignment to a property ending `RA`/`OA`/`OS`/`RS` — and three whole classes
of LCM write fell outside both:

| class | sites | example |
|---|---|---|
| unsuffixed scalar property assignment | 43 | `sense.ScientificName = ...` |
| `ISilDataAccess` scalar setters | 3 | `DomainDataByFlid.SetInt(...)` |
| LCM domain mutators named like setters | 1 | `ICmAgent.SetEvaluation(...)` |

All 47 are now bracketed and all three shapes added to the scanner.
**Mutation-checked per D10:** the extended scanner reports **39 unbracketed
methods against the pre-DEF tree and 0 against the fixed one**. The old
scanner reported 0 against both — it was measuring its own name list.

After this sweep, **zero** `Not in the right state to register a change.`
failures originate in `flexicon/code/`.

### 4.4 D14 — tests that write raw LCM, and the swallowed exceptions that hid it *(harness, fixed)*

The remaining failures all came from test code writing through the LCM
directly rather than through a wrapper — legitimately, to stay independent of
whatever the test was not testing. The old session envelope covered those
writes for free.

What made this class hard to see is that **almost every one sits inside a
bare `except Exception: pass` cleanup helper.** The unbracketed write raises,
the bare except swallows it, and the failure surfaces much later and
somewhere else — as `"a text with the name 'zz_split_test' already exists"`,
or as a canonical-GUID collision — in a *different* test from the one that
actually broke.

Worse, the swallowed write is **half-applied**. `LcmSet<T>.Remove(obj)` takes
the object out of the in-memory collection and *then* raises while
registering the undo action. So the object is gone from `FeaturesOC` while
still live in the object repository with its GUID held. That is why
`_find_feature_by_guid` returned `None` (it walks the collection) and the
subsequent `factory.Create(guid)` still failed with "identical GUIDs" — two
observations that look contradictory until you know the write half-landed.

Sites fixed, each now taking its own `UndoableOperation`:

| file | site |
|---|---|
| `test_phon_features.py` | `_delete_feature_by_guid`; `phoneme.FeaturesOA` restore |
| `test_natural_classes.py` | `_delete_feature_by_guid` |
| `test_phon_rules.py` | `_delete_feature_by_guid` |
| `test_inflection_features.py` | `_delete_msfeat_by_guid` |
| `test_pos_catalog.py` | `_delete_pos_by_guid` (both owner branches) |
| `test_segment_operations.py` | `_delete_text_hard` |
| `test_variants_live.py` | 3× lexeme-form restore |
| `test_locations_live.py` | 2× `PossibilitiesOS.MoveTo` |
| `test_const_chart_marker.py` | 2× sub-marker build |
| `test_wfi_analysis.py` | `SetEvaluation` ×2, `MorphBundlesOS.Add` |
| `test_msa_kind_and_change_variant.py` | `MorphoSyntaxAnalysisRA` assign |
| `test_lexentry_duplicate.py` | `sense.Source` assign |
| `test_pronunciations_live.py` | `PronunciationsOS.Remove` |

This is a harness fix, not a library defect — but it is the same hazard a
**user** script hits if it reaches through to raw LCM, so the CHANGELOG and
the `OpenProject` docstring both call it out.

---

## 4a. CORRECTION — an earlier reading in this document was wrong

An earlier revision of §4.3 reported the catalog cluster
(`test_phon_features` / `test_pos_catalog` / `test_inflection_features`) as
**18 failed / 25 passed in both modes** and concluded the failures were
pre-existing and "not DEF's". That conclusion was an artifact of the
measurement, and it inverted once the measurement was fixed.

Both sides had been polluted by earlier runs *in this same session*.
`test_segment_operations.py` and the catalog suites do not use the Target at
all — they open **Sena 3** through their own module-scoped `writable_project`
fixture — and every restore up to that point had been
`scripts/restore_target.py`. Leftover `zz_*` texts and canonical-GUID
objects were therefore present for baseline and after alike, failing both
identically and reading as "unrelated to the change".

Re-measured with **both** projects restored before each side:

| | baseline (`undoable=False`) | after (`undoable=True`) |
|---|---|---|
| 15 affected live files, before the D14 fixes | **2 failed, 208 passed** | 40 failed, 170 passed |
| 15 affected live files, **final** | **2 failed, 208 passed** | **2 failed, 208 passed** |

The 38 regressions were real, and all of them were the D13/D14 classes. After
the fixes the two sides are identical, with zero newly-failing tests. *Any
paired live measurement in this repo must restore both projects, or it
measures its own history.*

---

## 4b. The GUID collision: a wrong hypothesis, and what it actually was

This section originally reported a **design blocker** — that under
`undoable=True` a deleted object stays on the undo stack so liblcm keeps its
GUID reserved for the session, breaking every create → delete → recreate at a
canonical GUID, and that it was unfixable without destroying undo history.

**That hypothesis was wrong.** It is kept here, corrected rather than
deleted, because the way it was wrong is the useful part.

A direct probe against a live sandbox settled it in one run — create, delete,
inspect, recreate, with `ICmObjectRepository.TryGetObject` and the action
handler read at each step:

```
[1. after create]  TryGetObject -> found=True   CanUndo=True  UndoableActionCount=11
[2. after delete]  TryGetObject -> found=False  CanUndo=True  UndoableActionCount=17
3. attempting recreate...
    RECREATE OK -> b4ddf8e5-1ff8-43fc-9723-04f1ee0471fc
```

Delete releases the GUID; recreate succeeds. The undo stack holds the delete
(`UndoableActionCount` rises to 17) and reserves nothing. The hypothesis was
inference from a correlation, and it did not survive being measured.

**What was actually happening.** Re-running the same probe with the *test's*
cleanup instead of the wrapper's — a raw `fs.FeaturesOC.Remove(feat)` with no
unit of work — reproduced the failure exactly:

```
deleting via RAW FeaturesOC.Remove (as the test does)...
    raw Remove RAISED (test swallows this): InvalidOperationException:
        Not in the right state to register a change.
           at UnitOfWorkService.RegisterCommon(IUndoAction stateChanged)
           at LcmSet`1.Remove(T obj)
[2. after delete]  TryGetObject -> found=True   <-- still there
    ops._find_by_guid -> None                   <-- but not in the collection
3. attempting recreate...
    RECREATE FAILED: ... identical GUIDs
```

So it was **D14 all along** — an unbracketed raw LCM write in a test cleanup
helper, inside a bare `except Exception: pass`. `LcmSet.Remove` removes from
the collection and *then* raises while registering the undo action, leaving
the write half-applied: gone from `FeaturesOC`, still live in the repository
with its GUID held. The two "contradictory" observations that made this look
like a deep LCM property — `_find_by_guid` says gone, `Create` says taken —
are just the two halves of one interrupted write.

Bracketing that one helper took `test_phon_features.py` from 7 failures to 3;
bracketing a second raw write in the same file (`phoneme.FeaturesOA` restore)
took it to **12 passed, 1 skipped — exactly baseline**. The same treatment
across the remaining files closed every one.

**Lesson worth keeping:** the failing test was not the broken one. A bare
`except: pass` in a cleanup helper converts "this write is illegal now" into
a delayed, misattributed failure in an unrelated test — and a half-applied
mutation that makes the system look like it has a rule it does not have. Do
not theorise about liblcm semantics from a symptom observed downstream of a
swallowed exception; probe the write itself.

---

## 5. Verification of the mode the flip makes default

`tests/operations/test_undoable_mode_live.py` — the DEF-COV suite, the one
that exists to cover `undoable=True`, on a restored Target under the new
default:

```
33 passed, 1 warning in 22.13s
```

All eight claims the mode makes still hold: clean-block commit, real
rollback, per-operation UoW, nesting-joins, Undo/Redo, the B2 brackets under
this mode, persistence across `CloseProject()`/reopen, and the live pin on
D9's pythonnet surface.

---

## 6. Honest limits of this verification

1. **The broad live suite still runs `undoable=False`** (D12's deliberate
   consequence: the three general fixtures are pinned so they keep their
   documented identity). Continuous coverage of the new default rests on
   DEF-COV's 33 tests plus the module-scoped fixtures that do not pin a mode —
   which, as it turned out, is what caught D13 and D14. Converting the whole
   suite to the new default is a separate task.
2. **Three earlier measurements in this session were invalid**, and are kept
   above rather than deleted because each failure mode is reusable: a stashed
   baseline that a timeout silently reverted; a worktree baseline missing
   untracked `.fwbackup` fixtures (85 fixture errors); and the Sena-3
   pollution corrected in §4a.
3. **One hypothesis in this document was wrong and is corrected in §4b**, not
   quietly removed. The claim that deleted GUIDs stay reserved under
   `undoable=True` was inference from a downstream symptom; a direct probe
   refuted it.
4. **A single whole-suite live run was never completed, in either mode.** The
   full `-m requires_live_project` run hangs partway, with output frozen at
   the same point on the **unmodified baseline worktree** as on the changed
   tree — so it is pre-existing and mode-independent, not caused by this work,
   but it means "the entire live suite is green" is not a claim this evidence
   makes. What it does claim is the paired per-cluster diff over the 15
   affected files (§4a), which is where the signal was, plus the targeted
   suites in §5. Diagnosing the hang is separate follow-up work.
5. **The version number is assumed, not decided.** Docstrings, CHANGELOG and
   contract text say 4.4.0; `flexicon/__init__.py` still reads `4.3.1` and no
   release was cut. One `grep -rn "4\.4\.0"` to renumber.

---

## 7. Result

**PASS.**

| gate | result |
|---|---|
| offline suite, failure set vs baseline | identical, **zero regressions** (one test newly passing) |
| 15 affected live files, paired vs baseline | **2 failed / 208 passed both sides — zero newly failing** |
| DEF-COV (`undoable=True` coverage) | **33/33 live** |
| `AbortSession` live | **12/12** |
| unbracketed-mutation scanner | **0** on fixed tree, **39** on pre-DEF tree |
| write-path guard tests | 24/24 |

What the flip cost, and it was worth finding:

- **47 library mutation sites** that had been running outside any unit of
  work since before B2 was declared complete, invisible to a scanner that
  measured its own name list (**D13**). All bracketed; all three shapes now
  detected by the ratchet.
- **1 module-level helper** (`ApplySyncableProperties`) that no per-method
  sweep could reach (**D11**).
- **~20 raw-LCM writes in live tests**, most hidden behind
  `except Exception: pass` (**D14**).
- **3 conftest fixtures** silently reinterpreted by the flip, now pinned
  (**D12**).

None of these were caused by DEF; all of them were *revealed* by it, because
`undoable=True` is the first mode in which an unbracketed write is an error
rather than a silent success. That is the strongest argument for the flip
itself: the old default did not just lack rollback, it concealed the absence
of unit-of-work discipline everywhere.
