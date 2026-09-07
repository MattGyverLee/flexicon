# Cycle 5 -- Programmer report: T5 (`MakeFeatStruc` generalization, closes #256)

Scope: **T5 only.** T6 and later were NOT started, per instructions.

## 1. Where the merged code lives

- `flexicon/code/BaseOperations.py` -- new methods, inserted immediately
  after `_ApplyFeatureStrucSpecMap` and before `_RejectLegacyKwargs`:
  - `_MakeFeatStruc(self, specs, owner=None, slot=None)` -- the ONE
    generalized implementation (C3 surface).
  - `__NormalizeFeatStrucLevel` -- private recursive resolver/validator
    (runs to completion, raising on malformed shape, before any LCM
    mutation).
  - `__PopulateFeatStrucLevel` -- private recursive populator (ownership-
    first at every level; each mutation group wrapped in its own
    `with self._TransactionCM("Add feature value"):`).
  - `__ResolveFeatStrucOperand` -- private per-operand resolver (HVO / GUID
    string / already-resolved object or wrapper).
- `flexicon/code/Grammar/InflectionFeatureOperations.py:970` --
  `MakeFeatStruc(self, specs, owner=None, slot=None)` is now a 1-line
  call-through: `return self._MakeFeatStruc(specs, owner=owner, slot=slot)`.
- `flexicon/code/Grammar/PhonFeatureOperations.py:553` -- same, thin
  call-through to the same shared method.

Both subclass methods keep their own docstrings (contract summary +
pointer to `BaseOperations._MakeFeatStruc` for the full spec), stay
decorated `@OperationsMethod` (unchanged dispatch), and both public
signatures gained one new optional keyword: `slot=None`.

## 2. Anchors found (symbol-anchored, per standing discipline)

| Anchor | Expected (task prompt) | Found | Unique in file? |
|---|---|---|---|
| `InflectionFeatureOperations.MakeFeatStruc` def | `:970` | **`:970`** (before edit; call-through now spans `:970-1013`) | yes |
| `PhonFeatureOperations.MakeFeatStruc` def | `:553` | **`:553`** (before edit; call-through now spans `:553-592`) | yes |
| `NaturalClassOperations.py` caller #1 | `:463` | **`:463`** | yes |
| `NaturalClassOperations.py` caller #2 | `:867` | **`:867`** | yes |
| `NaturalClassOperations.py` caller #3 | `:1034` | **`:1034`** | yes |
| `PhonemeOperations.py` caller | `:1886` | **`:1886`** | yes |
| `PhonFeatureOperations.py` docstring example | `:106` | **`:106`** | yes |

None of the three files I did not edit (`NaturalClassOperations.py`,
`PhonemeOperations.py`) moved at all -- their line numbers are exactly the
pre-existing ones (confirmed live via `grep -n` after my edits, not
assumed).

## 3. Behavioural-delta table: the two pre-T5 `MakeFeatStruc` bodies

Produced BEFORE merging, per instructions. Read both bodies in full
(`InflectionFeatureOperations.py:969-1059`,
`PhonFeatureOperations.py:552-641`) plus their private helpers
(`__ResolveFeature`/`__ResolveFeatureSystem` vs `__ResolveObject`, and both
files' `__Unwrap`).

| Axis | Infl body | Phon body | Merged version takes | Why |
|---|---|---|---|---|
| Owner check | `if not hasattr(owner_unwrapped, "FeaturesOA"): raise` | Byte-identical | **Neither.** Replaced with `self._ResolveFeatureStrucOwner(owner, slot=slot)` (T2, C1 table). | This IS the #256 fix -- both twins' gate is coincidentally correct only for `PhNCFeatures`/`PhPhoneme` and 100% dead code for every other owner (MSA x4, POS x2, Allomorph). Load-bearing insight from the task brief. |
| Feature-operand resolution helper name | `self.__ResolveFeature(feat_in) if not isinstance(feat_in,int) else self.project.Object(feat_in)` | `self.__ResolveObject(feat_in)` (which does the identical `isinstance(int)` branch internally) | **Functionally identical either way** -- confirmed by reading both helper bodies: both are `if isinstance(x, int): return project.Object(x); return x`. Merged as one `__ResolveFeatStrucOperand`. | Different method *names*, same *algorithm*. Not a real behavioural divergence -- verified by reading, not assumed. |
| Value-operand resolution | Inlined (`val_in if not isinstance(val_in,int) else self.project.Object(val_in)`), NOT routed through `__ResolveFeature` | `self.__ResolveObject(val_in)` | Same as above -- identical algorithm, different spelling. | ditto |
| `__Unwrap` (wrapper-peeling) | Present, byte-identical body to Phon's (confirmed by reading both) | Present | Kept, folded into `__ResolveFeatStrucOperand`. | Byte-identical already; no divergence to reconcile. |
| GUID-string operand support | Not supported (falls through unresolved, fails at LCM property-set) | Not supported (same) | **Added** (`isinstance(str) -> project.Object(str)`). | C3 explicitly names GUID strings as an accepted operand shape. Additive-only: any string that previously reached the LCM call unresolved would already have failed, so no passing input changes behaviour. |
| Name-string operand support | Not supported | Not supported | **Deliberately NOT added.** | C3's "a name" language is not backed by either pre-T5 body, no shipped test exercises it, and guessing which `Find`-style lookup applies to a bare string is exactly the kind of silent guess the C1 resolver exists to forbid. Documented as a scope limitation in `_MakeFeatStruc`'s own docstring Notes. |
| Malformed-tuple message | `f"specs[{i}] must be a (feature, value) tuple"` | Byte-identical | Kept verbatim. | No divergence. |
| `owner=None` error message wording | "...Pass owner=msa / owner=template / owner=context." | "...Pass owner=phoneme / owner=natural_class / owner=context." | **New, generalized wording** naming every C1-table owner kind (phoneme / natural_class / msa / pos / allomorph / context) plus a pointer to `slot=`. | Neither twin's wording is complete now that ONE method serves every C1 owner; picking either verbatim would misdescribe the other domain's callers. |
| Transaction label | `"Make feature structure"` | Byte-identical | Kept verbatim. | No divergence; also matches `_ApplyFeatureStruc`'s struct-creation label (T4 precedent). |
| Spec shape accepted | Flat list of `(feature, value)` tuples only | Identical | **Both shapes** -- flat list (unchanged, byte-for-byte back-compat) **and** new recursive dict (C3). | C3 is frozen; the tuple-of-list "nested" overload is explicitly REJECTED, not implemented (a list-shaped tuple value falls through to the scalar branch and fails naturally at the LCM call -- no special-case code written for the rejected shape). |
| Ownership-first ordering | Attach `owner.FeaturesOA = struct` before populating `FeatureSpecsOC` | Identical | Kept: `setattr(concrete_owner, prop_name, struct)` before any populate call, at every nesting level (nested `IFsComplexValue.ValueOA` attached before recursing). | C5 invariant, unchanged. |
| Mutation bracketing | Single outer `with self._TransactionCM("Make feature structure"):` wrapping create+attach+populate-loop | Identical | **Split**: outer transaction wraps only create+attach; `__PopulateFeatStrucLevel` wraps EACH spec's mutation in its own `with self._TransactionCM("Add feature value"):` (matches `_ApplyFeatureStrucSpecMap`'s existing per-item pattern). | Required by `tests/write_path_transactions/test_unbracketed_mutations.py` (B2g ratchet, baseline is now 0) -- it statically scans EACH method's own body for a lexically-enclosing `_TransactionCM`; an outer caller's transaction does not satisfy it for the callee. First pass violated this (caught by running the ratchet test); fixed and re-verified (see section 6). |

**No fourth mistake repeated.** The one real algorithmic difference between
the twins was the `hasattr(..., "FeaturesOA")` gate itself, and the merge
does not silently pick one side's version of it -- it replaces both with
the C1 resolver, which is the actual #256 fix, not a cast and not a
`hasattr` capability check.

## 4. Back-compat verification

### Production callers (5/5, all pass positional `specs` + keyword `owner=`)

| Site | Call shape | Still valid against new signature `(self, specs, owner=None, slot=None)`? |
|---|---|---|
| `NaturalClassOperations.py:463` | `MakeFeatStruc(specs, owner=duplicate)` | Yes -- `slot` defaults `None`, ignored for `PhNCFeatures` (single-row). |
| `NaturalClassOperations.py:867` | `MakeFeatStruc(specs, owner=nc)` | Yes, same reasoning. |
| `NaturalClassOperations.py:1034` | `MakeFeatStruc(specs, owner=nc)` | Yes, same reasoning. |
| `PhonemeOperations.py:1886` | `MakeFeatStruc(specs, owner=phoneme)` | Yes -- `PhPhoneme` is single-row. |
| `PhonFeatureOperations.py:106` (docstring example) | `MakeFeatStruc([(cons, plus)], owner=phoneme)` | Yes, unchanged text, still accurate. |

### Test files (4/4)

| File | What it exercises | Result |
|---|---|---|
| `tests/operations/test_phonemes.py:672` | `feat_ops.MakeFeatStruc([(feat, plus)], owner=phoneme)` (legacy flat list, no slot) | **PASS** (live, see section 5). |
| `tests/operations/test_phon_features.py:406/412/450/501` | `owner=None` always raises (with empty AND non-empty specs); `owner=phoneme` attach + populate | **PASS** (live) -- `owner=None` still raises unconditionally, confirming the issue #28 ruling is unchanged. |
| `tests/operations/test_feature_struc_resolver.py` | Deliberately does NOT call `MakeFeatStruc` (its own docstring: "deliberately NOT using MakeFeatStruc/T4/T5 helpers, which would make this test circular") | **PASS** (live) -- unaffected by construction, confirmed green. |
| `tests/operations/test_issue251_252_256_feature_struct_probe.py:411` | `infl_ops.MakeFeatStruc([], owner=stem)` where `stem` is `IMoStemMsa` -- the #256 reproduction (item 7) | **PASS** (live); printed evidence flips from `FP_ParameterError: owner has no FeaturesOA property` to `NO EXCEPTION -- returned <IFsFeatStruc ...>` (see `evidence/live-T5.md`). |

`owner=None` continues to RAISE unconditionally (issue #28 ruling,
unchanged) -- verified live by
`test_phon_features.py::test_make_featstruc_rejects_owner_none` and
`test_make_featstruc_unowned_requires_empty_specs`, both green.

## 5. Measurement (spec.md section 5.1, frozen comparator)

Full detail and exact commands in
`specs/feature-structure-sync-gap/evidence/live-T5.md`. Summary:

1. **Live subset, both sides, same shell:** BEFORE (stashed to parent) =
   AFTER (T5, final) = `1 failed, 77 passed, 1 skipped, 27 deselected`,
   `run_mode: live` confirmed on every run. The single failure is the
   documented known-foreign one. Item 7's *printed* evidence flips
   FAIL -> PASS as predicted (pytest status itself doesn't flip -- item 7
   is assertion-free by design).
2. **Pinned offline subset, delta:**
   `python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider`
   -- BEFORE `2 failed, 350 passed, 489 deselected`; AFTER identical.
   **Delta: 0.**
3. **Determinism check:** same-shell x2 + fresh-shell x1, all three
   `2 failed, 350 passed, 489 deselected`. Comparator valid.
4. **Falsifiability (mutation test):** forced `prop_name =
   "MUTATION_TEST_BOGUS_PROP"` after the C1 resolver call inside
   `_MakeFeatStruc`. Live subset went from 1 to **8 failed** (7 new real
   failures across `test_phon_features.py`, `test_phonemes.py`,
   `test_natural_classes.py`). Reverted; `git hash-object` on
   `BaseOperations.py` identical before/after
   (`a32d94151fee1c3c62ccc33e71f3253990b0181a`).

**Incident, disclosed:** the mutation test's 7 broken assertions left
transient residue in the real "Sena 3" project (these three test files open
it directly, write-enabled, no sandbox -- by the file's own design, "residue
is a diagnostic signal on failure"). Remedied with
`python scripts/restore_sena3.py`, run twice (once mid-investigation, once
after the final code state), each followed by a clean live re-run. The real
Target project was never touched. Full account in `evidence/live-T5.md`
section 4.

## 6. The ratchet catch (worth flagging for future spurts)

`tests/write_path_transactions/test_unbracketed_mutations.py` (B2g,
baseline now 0 -- ANY new unbracketed LCM mutator anywhere under
`flexicon/code/` fails it) initially caught my first-pass
`__PopulateFeatStrucLevel`: it performed mutations (`factory.Create`,
`.Add`, `FeatureRA`/`ValueOA`/`ValueRA` assignment) inside one *outer*
`with self._TransactionCM(...)` opened by the caller (`_MakeFeatStruc`),
but the scanner is per-method and lexical -- it does not credit a caller's
transaction to a callee. Fixed by wrapping each mutation group directly
inside `__PopulateFeatStrucLevel` in its own
`with self._TransactionCM("Add feature value"):`, matching
`_ApplyFeatureStrucSpecMap`'s existing pattern for the identical shape.
Re-ran the ratchet test (`4 passed`) and the full mutation-falsifiability +
live-subset cycle again against the corrected code (section 5's numbers are
all post-fix, final).

## 7. What I deliberately did NOT touch

- **T6-T17**, per instructions -- no `MSAOperations`, `POSOperations`,
  `AllomorphOperations`, `PhonemeOperations` policy-flip, `CopyFeatStruc`,
  docs, or `test_transaction_rollback.py`/alias-ratchet foreign failures.
- `tests/conftest.py` -- untouched (shared harness, T18 deferred).
- `NaturalClassOperations.py`, `PhonemeOperations.py` -- their 4 `MakeFeatStruc`
  call sites keep calling the SAME public method with the SAME arguments;
  no line in either file was edited. Confirmed unchanged by `git status`.
- **Any file under the other crew's fence**
  (`flexicon/code/TextsWords/{Paragraph,Segment,Discourse}Operations.py`,
  their test/spec files). Not opened, not staged. Their concurrent edits
  during this session (`flexicon/code/Notebook/AnthropologyOperations.py`,
  `specs/name-field-whitespace-identity/spec.md`,
  `specs/tier1-silent-data-loss/QUEUE.md`) were observed appearing mid-session
  via `git status` but never read, staged, or reverted.
- **Unused imports** left behind in `PhonFeatureOperations.py`
  (`IFsFeatStrucFactory`, `IFsClosedValueFactory`, `IFsClosedValue` are now
  referenced only by their import lines / a docstring comment) and
  `InflectionFeatureOperations.py` (`IFsClosedValueFactory`, `IFsClosedValue`
  likewise). Deliberately left in place -- Python does not error on an
  unused import, removing them is pure cosmetic churn unrelated to #256,
  and it would widen the diff for zero functional benefit.
- **Plain name-string resolution** for `MakeFeatStruc` operands (see
  behavioural-delta table, row "Name-string operand support") -- explicitly
  scoped out; documented in `_MakeFeatStruc`'s own docstring.
- **A new live test asserting a multi-level NESTED `MakeFeatStruc(...)` dict
  end-to-end** against a live MSA/POS owner -- recorded as a T14 item (see
  `evidence/live-T5.md` section 5); T5's own nested-populate code path
  reuses the same create-then-recurse shape already live-proven for the
  C4/C5 apply surface in T4, and the falsifiability mutation test proves the
  C1 resolution it depends on is genuinely exercised, but no NEW dedicated
  nested-`MakeFeatStruc` live assertion was added in this task.
- `docs/API_ISSUES_CATEGORIZED.md`, `CHANGELOG.md` -- not touched (T15's
  territory; #256 has no behavioural-flip/BREAKING angle the way #253/T9
  does, so no changelog entry was owed by T5 itself).

## 8. Commit

Staged and committed with **explicit paths only** (never `-A`/`-u`/`-a`):
`flexicon/code/BaseOperations.py`,
`flexicon/code/Grammar/InflectionFeatureOperations.py`,
`flexicon/code/Grammar/PhonFeatureOperations.py`,
`specs/feature-structure-sync-gap/evidence/live-T5.md`,
`specs/feature-structure-sync-gap/reviews/cycle5-programmer-T5.md`.
`git status --porcelain` reviewed before staging; confirmed no path outside
this list was staged, and the other crew's concurrent changes
(`AnthropologyOperations.py`, `name-field-whitespace-identity/spec.md`,
`tier1-silent-data-loss/QUEUE.md`) were left untouched in the working tree.
