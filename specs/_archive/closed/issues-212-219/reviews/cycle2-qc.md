# QC Report — Issues #220 / #217 (test-only files)

**Date:** 2026-07-17
**Files reviewed:**
- D:\Github\_Projects\_LEX\flexicon\tests\operations\test_yield_cast_pattern.py
- D:\Github\_Projects\_LEX\flexicon\tests\operations\test_apply_syncable_properties.py
- Reference: D:\Github\_Projects\_LEX\flexicon\tests\operations\test_owner_cast_pattern.py

## Pattern-Audit Gate
N/A — these are test-only additions pinning already-merged fixes (92762fa for
#220, 23eb9f7/171a9a7 for #217), not new bugfixes. Both files explicitly cite
the fixing commits and the categorized-issue docs (Category 5, Category 8) in
their headers, which is the substance the gate is meant to enforce anyway.
Gate status: **N/A (justified)**.

## 1. Coverage completeness

**#220 — verified complete.** Cross-checked against the actual source
(flexicon\code\Grammar\InflectionFeatureOperations.py:178-183,
flexicon\code\Lexicon\SemanticDomainOperations.py:610-656,
flexicon\code\Notebook\LocationOperations.py:1036-1075):
- Fast path + recursive-walk both covered via `min_count=2` for the two
  possibility-tree sites (test_yield_cast_pattern.py:196-198, 204-206) and
  `min_count=1` for InflectionClassGetAll (no recursive walk there — correct,
  that method has no recursion).
- All 3 static "no bare yield/pass-through" tests match the real pre-fix shape.
- Live behavioural layer (`TestYieldCastLive`, lines 309-411) checks `type(item)
  is not <base>` AND `type(item) is <concrete>` AND concrete-only member access,
  for all 3 sites, both `recursive=True/False` where applicable.
- 5 new ProjectSettings accessors: static existence+delegation check
  (lines 422-458) and live smoke test (lines 461-487) for all 5. Complete.

**#217 — verified complete against the requirement->test mapping in
cycle1-programmer-217.md.** All 6 requirements pinned:
1. multistring dict branch (4 tests, incl. ws-not-on-target, missing-prop,
   fill_gaps)
2. plain-str setattr (5 tests, incl. object-ref-typeerror-skip and
   unrelated-typeerror-reraise)
3. bool/int dispatch (7 tests, incl. bool-before-int ordering — the trickiest
   branch since `isinstance(True, int)` is `True` in Python)
4. ITsString->MakeString fallback (3 tests, incl. no-utils and
   no-default-ws-getter skip paths)
5. ws_map identity/remap/unmapped-skip (3 tests)
6. 171a9a7 Category-8 type corrections (9 tests: 7 parametrized field-shape
   locks + 2 apply-side locks)
Plus Section B's 4 top-level guard tests, correctly ordered
(`_EnsureWriteEnabled` fires before the None-item check — verified against
BaseOperations.py:1266-1268 — and test_write_enabled_check_happens_before_item_none_check
locks that ordering explicitly). No gap found in the requirement mapping.

## 2. Brittleness of static source-lock assertions

**P1 — test_apply_syncable_properties.py:701-724
(`test_lexsense_source_scientificname_importresidue_not_special_cased`).**
Parses source via `src.split("_special_fields")[1].split(")")[0]` to extract
the tuple body and check field names aren't in it. This is fragile in a way
the rest of the suite isn't: any reformatting that puts a `)` earlier in that
region (e.g. a parenthesized comment, a nested call, a multi-line tuple with
an inline default-argument call before `_special_fields` closes) silently
changes what gets checked, potentially passing even if a field IS added, or
raising an unrelated `IndexError`/`AssertionError` with no diagnostic
`msg_prefix` (unlike every other test in the file, this one has no source
included in its failure message). Recommend replacing with a regex over the
`_special_fields` tuple or an AST-based check, and add `msg_prefix`-style
source context to the assertion message.

**P1 — test_yield_cast_pattern.py:182-207 (`_SITES` table), specifically the
`InflectionFeatureOperations` row.** `cast_expr = "IMoInflClass(ic)"` locks
the loop-variable name `ic`, whereas the other two rows use
`"ICmSemanticDomain("` / `"ICmLocation("` (no variable name lock) — an
inconsistent brittleness level across three rows of the same parametrized
table. Renaming the loop variable in InflectionClassGetAll (a harmless,
behavior-preserving refactor) would fail `test_casts_before_yield` for that
row while leaving the other two rows passing. The failure message
(`msg_prefix` + full source + explanation, lines 226-235) is good — a
developer hitting this failure has everything needed to fix it in seconds —
but the assertion itself should not have required the fix to know that. Same
comment applies to `test_inflection_class_no_bare_yield` (line 247,
`"yield ic\n"`), though that one only breaks on introducing the *exact* old
bad string back, not on a harmless rename, so it is lower risk than the
`cast_expr` row.

**P2 — test_yield_cast_pattern.py:267-273, 289-295.** The assertions
(`"for child in collection:\n" not in src`) only forbid the *old* broken
shape; they do not verify the *new* code actually uses variable name `raw`
(that's asserted only in the docstring/message text, not in code). This means
the message is technically over-specific documentation of an implementation
detail that isn't being checked — if a future refactor renames `raw` to
`item` while keeping the cast, the test still passes (correctly), but the
failure message for an unrelated future regression would now describe a
variable name that no longer exists in the source, mildly confusing whoever
reads it. Low severity — recommend generalizing the message wording (e.g.
"the raw uncast loop variable" instead of naming `raw` specifically) next
time this file is touched, not a blocking issue now.

**P2 — test_apply_syncable_properties.py Section C (`TestSyncTypeCorrectionsStatic`,
lines 633-678) is stricter than the reference model it says it mirrors.**
`test_owner_cast_pattern.py`'s static checks (lines 236-256) check only that
the collection name and *a* recognised helper appear anywhere in the method
body — tolerant of reordering/refactor. Section C here locks the exact call
shape `self._ReadTsString(item.{field})` / `item.{field}.get_String(` as
contiguous substrings (lines 653-654). A harmless refactor (e.g. binding
`prop = item.{field}` first, or reformatting the call across lines) would
break this even though the underlying type-safety fix is intact. This is a
reasonable trade-off given the bug class is specifically about the *shape*
of the read (per-WS loop vs `_ReadTsString`), but it's worth noting the
divergence from the file's own claimed "mirrors test_owner_cast_pattern.py"
framing (line 26) — the two are not equally tolerant, and a reader relying
on that comment to gauge brittleness would be misled.

All failure messages otherwise include enough context (full source dump via
`msg_prefix`/`textwrap.indent`, explicit citation of the issue number and the
correct expected shape) that a maintainer could fix a false-positive break
without re-deriving the pattern from git history — this is the strongest
part of the brittleness story in both files.

## 3. Import-name consistency

**P1 — test_apply_syncable_properties.py is internally inconsistent.** Top of
file imports the real package name directly:
```
tests\operations\test_apply_syncable_properties.py:66
from flexicon.code.BaseOperations import (...)
```
but Sections C/D exclusively use the deprecated shim name:
```
tests\operations\test_apply_syncable_properties.py:583-629 (_TYPE_CORRECTION_SITES import_path values, e.g. "flexlibs2.code.Lexicon.EtymologyOperations")
tests\operations\test_apply_syncable_properties.py:742 ("from flexlibs2.code.FLExProject import FLExProject")
```
`flexlibs2` is confirmed (flexlibs2\__init__.py:19, 65-72) to be a
deprecation shim that emits a `DeprecationWarning` on import and will be
*removed* in flexicon v5.0.0. Mixing the canonical name and the deprecated
alias within the same file is worse than the cross-file inconsistency with
`test_yield_cast_pattern.py` (which is at least internally consistent,
using `flexlibs2.code.*` throughout). No `filterwarnings = error` is
configured, so nothing fails today, but once the shim is removed in v5.0.0,
`test_apply_syncable_properties.py`'s Sections C/D and its `writable_project`
fixture break, while the file's own top-level import (line 66) would keep
working. Recommend standardizing on `flexicon.code.*` everywhere (matching
the actual installed package name and avoiding the deprecation warning noise
in test output), and updating `test_yield_cast_pattern.py` and
`test_owner_cast_pattern.py` to match in a follow-up pass — not blocking for
this review since it doesn't affect current correctness, but it's technical
debt that compounds every time this pattern is copied into a new test file.

## 4. Style/header conventions (CLAUDE.md)

Both files pass:
- File headers follow the CLAUDE.md template shape (module name, Class:,
  brief description, Platform, Copyright) — test_yield_cast_pattern.py:1-61,
  test_apply_syncable_properties.py:1-58.
- No emoji characters found in either file (checked full text).
- No Unicode bullets; markdown-style docstring formatting only.
- Naming conventions consistent with the reference file
  (`Test<Feature><Aspect>` classes, `test_<what>_<expected>` methods).
- Both files correctly declare the bug commits and issue numbers being
  pinned in the header, consistent with the project's practice of tracking
  fix provenance in docs/API_ISSUES_CATEGORIZED.md.

No issues here.

## 5. Live-test safety (#217 Section D)

**Confirmed correctly gated.** `TestApplySyncablePropertiesLive`
(test_apply_syncable_properties.py:784) carries
`@pytest.mark.requires_live_project`, matching the project-wide selector
convention documented in tests\LIVE_TESTING.md. The class docstring
(lines 786-791) explicitly states "Any test in this class WRITES to the live
project — restore the .fwdata backup after running this class," and the
module header (lines 43-52) repeats the WRITE/`-restore` warning and notes
the author did not execute Section D even though FieldWorks was available in
the authoring environment. This is good practice and matches this task's
instructions.

**P1 — reminder, not a defect in this file.** Per tests\LIVE_TESTING.md:20-21,
an *unfiltered* `pytest` invocation still collects (and will run, if a
writable project is reachable) `requires_live_project` tests — the marker is
purely a selector, not an automatic skip. This is an existing, pre-established
repo-wide convention (shared by ~15 other `*_live.py` files), not something
introduced by this file, but it means the Ralph loop's standing test-runner
prompt MUST invoke pytest with `-m "not requires_live_project"` (or
equivalent) whenever it runs the full suite unattended, or Section D's throw-
away sense/example/etymology/pronunciation writes (and everything else in the
other `*_live` files) will execute against whatever `.fwdata` project happens
to be reachable on the runner. Confirm this is baked into whatever command
the ralph-loop / CI harness actually invokes; it is not something this test
file can enforce on its own.

## Final Assessment

**Quality Score:** 88/100
- Coverage completeness: 25/25 — both requirement sets fully pinned, verified
  against actual source.
- Static-lock brittleness: 18/25 — two P1 findings (inconsistent variable-name
  locking in #220's `_SITES` table; fragile string-splitting in #217's
  special-fields check) knock points off; failure messages otherwise strong.
- Import consistency: 20/25 — internal inconsistency within
  test_apply_syncable_properties.py itself is a real (if currently harmless)
  defect.
- Style/live-safety: 25/25 — headers, ASCII-only output, and live-test gating
  are all correct and well-documented.

**Recommendation:** FIX ISSUES (non-blocking, P1-level) — safe to merge as-is
since all findings are either forward-looking robustness concerns (brittle to
harmless refactors, not incorrect today) or documentation/consistency debt;
none affect current correctness or live-test safety. Recommend a follow-up
pass to: (a) loosen the `IMoInflClass(ic)` cast_expr to not lock the loop-var
name, (b) replace the `_special_fields` string-split with a regex/AST check,
(c) canonicalize on `flexicon.code.*` imports in
test_apply_syncable_properties.py.

---
**Reviewed By:** QC Agent
