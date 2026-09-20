# Cycle 2 -- programmer hardening of clone_properties (issue #321, suspect 2)

**File changed:** `flexicon/code/lcm_casting.py` (`clone_properties`, lines
~791-823 pre-change; the function itself is unchanged in overall shape --
only the collection-detection predicate and a new module-level constant
were added).
**Tests added:** `tests/test_issue321_clone_properties_ownership_discriminator.py`
**Scope:** ONLY `lcm_casting.py` and its new test file. No other module
touched, per the file-lock instruction (other agents are concurrently
editing Lexicon/Notebook/Lists operations files).

## Grounding

Read first, per the task instructions:
- `specs/318-321-nonexistent-member-mutations/reviews/cycle1-verification.md`
- `specs/318-321-nonexistent-member-mutations/evidence/live-321-derived-lists.md`

Both confirm, via live `.Clear()` probes on a disposable Sena 3 sandbox
copy, that `clone_properties`'s old predicate --
`hasattr(attr_value, "Count") and hasattr(attr_value, "Add")` -- matches
six DERIVED, rebuilt-per-access `ILexEntry`/`ICmObject` members
(`AllSenses`, `MorphTypes`, `PublishIn`, `ShowMainEntryIn`,
`MinimalLexReferences`, `ReferringObjects`), on which `.Clear()` "succeeds"
(raises nothing) but leaves `Count` unchanged on a fresh re-fetch -- the
#317 silent-no-op class, demonstrated on the actual `dest_collection.Clear()`
call at the old line 811. A genuine `OS`-suffixed collection (`EtymologyOS`)
cleared and stayed cleared under the identical probe, confirming the LCM
ownership-suffix convention is a reliable live discriminator where
duck-typing is not.

Cross-checked against the authoritative index
(`C:\Github\FlexToolsMCP\src\flextoolsmcp\index\liblcm\liblcm_api_v11.0.0.json`):
`AllSenses`'s declared `"kind"` is `"property"` (derived), while
`EtymologyOS`'s declared `"kind"` is `"OS"` (owned sequence) -- matching the
live evidence exactly and confirming the index's `kind` field independently
encodes the same real/derived split the naming-suffix convention encodes.

## The fix

Added a module-level constant just above `clone_properties`:

```python
_OWNED_OR_REFERENCE_SUFFIXES = ("OS", "OC", "OA", "RS", "RC", "RA")
```

And changed the collection-detection guard from:

```python
if hasattr(attr_value, "Count") and hasattr(attr_value, "Add"):
```

to:

```python
if attr_name.endswith(_OWNED_OR_REFERENCE_SUFFIXES) and hasattr(
    attr_value, "Count"
) and hasattr(attr_value, "Add"):
```

Members that fail the new suffix gate fall through to the existing
`else` branch (`setattr(dest, attr_name, attr_value)`), which is wrapped in
the pre-existing `try/except` that already silently skips failed sets
(logged at `logging.debug`). For a read-only derived property this raises
inside `setattr` and is swallowed exactly as before -- i.e. the net runtime
effect for these members is still a no-op, just without the wasted
`Clear()` + iteration cycle, and with the mechanism now honest (structural
exclusion, not an accidental Clear()-that-does-nothing).

This is a narrow, single-branch change. No other part of `clone_properties`
(recursion, factory lookup, exception handling shape) was touched.

## Old-predicate vs new-predicate member comparison

Built directly from the live enumeration in
`live-321-derived-lists.md` (`clone_properties predicate matches on
ILexEntry (16)` plus the `IPhCode` sweep), which is the authoritative
"what actually matches today" data for the real caller-reachable types:

| Member                   | LCM suffix    | Old predicate (Count+Add) | New predicate (suffix + Count+Add) | Live-confirmed kind |
|--------------------------|---------------|:--------------------------:|:-----------------------------------:|----------------------|
| AllSenses                | none          | MATCH                      | excluded                            | derived, Clear()-no-op (proven live) |
| MorphTypes               | none          | MATCH                      | excluded                            | derived, Clear()-no-op (proven live) |
| PublishIn                | none          | MATCH                      | excluded                            | derived, Clear()-no-op (proven live) |
| ShowMainEntryIn          | none          | MATCH                      | excluded                            | derived, Clear()-no-op (proven live) |
| MinimalLexReferences     | none          | MATCH                      | excluded                            | derived, Clear()-no-op (proven live) |
| ReferringObjects         | none          | MATCH                      | excluded                            | derived, Clear()-no-op (proven live; also the only member reachable via a real caller argument, `IPhCode`) |
| AlternateFormsOS         | OS            | MATCH                      | MATCH (unchanged)                   | owned, real |
| EntryRefsOS              | OS            | MATCH                      | MATCH (unchanged)                   | owned, real |
| EtymologyOS              | OS            | MATCH                      | MATCH (unchanged)                   | owned, real (live Clear()-and-stays-cleared control) |
| PronunciationsOS         | OS            | MATCH                      | MATCH (unchanged)                   | owned, real |
| SensesOS                 | OS            | MATCH                      | MATCH (unchanged)                   | owned, real |
| MorphoSyntaxAnalysesOC   | OC            | MATCH                      | MATCH (unchanged)                   | owned, real |
| DialectLabelsRS          | RS            | MATCH                      | MATCH (unchanged)                   | reference, not live-Clear()-tested but pre-existing behaviour preserved |
| DoNotPublishInRC         | RC            | MATCH                      | MATCH (unchanged)                   | reference, ditto |
| DoNotShowMainEntryInRC   | RC            | MATCH                      | MATCH (unchanged)                   | reference, ditto |
| MainEntriesOrSensesRS    | RS            | MATCH                      | MATCH (unchanged)                   | reference, ditto |

**Result: the old predicate matched 16 members on `ILexEntry`; the new
predicate matches 10. The difference is EXACTLY the six no-suffix members
independently proven live to be derived/Clear()-no-op members.** No
OS/OC/RS/RC/RA member present in the old match set was dropped. This
satisfies the mandatory conservative-hardening constraint: the change is a
pure narrowing of the *derived* subset, not of any genuine owned or
reference collection.

`IPhCode`'s only match (`ReferringObjects`, no suffix, empty in the tested
data) moves from "matched, wasted Clear()+no-op cycle" to "excluded" --
behaviourally identical for that caller today (both are no-ops), per the
cycle-1 verification's own conclusion.

### Members not live-reachable (honesty gap carried forward)

`IFsFeatStruc` and `IPhContext` (the other two real-caller argument types,
from `PhonemeOperations.py:374-384` and `EnvironmentOperations.py:631-652`)
were not reachable in Sena 3's sandbox data in cycle 1 and were not
re-probed in this cycle (no live project was opened in this session --
the task scope was a static, non-live hardening). Whether either type
exposes an RS/RC/RA member whose Clear()+Add() cloning semantics change
under this fix remains unverified. Per the recommended-fix note in cycle 1,
restricting to the ownership-suffix set does not remove any RS/RC/RA
member from the match set (it only removes no-suffix members), so even if
one of those two types turns out to expose an RS/RC/RA collection, this fix
does not change how it is handled. The only way this fix could change
behaviour for an unverified type is if that type exposes a no-suffix
Count/Add member -- in which case the change converts an already-proven-
possible silent no-op into an honest skip, which is the safe direction
per the task's own instruction ("prefer the SAFE direction... over
silently skipping it").

## Safety-direction confirmation

No case was found where the new discriminator would have dropped a
legitimate collection. All six excluded members were independently proven
live (cycle 1) to be `.Clear()`-no-op derived properties, not real backing
stores. No stop-and-report condition was triggered.

## Tests

`tests/test_issue321_clone_properties_ownership_discriminator.py`
(pure-Python fakes, no live project -- `FakeCollection` duck-types
Count/Add/Clear so it reproduces the old predicate's blind spot without
needing SIL.LCModel; `FakeLexEntry.ClassName` is deliberately unrecognised
so `cast_to_concrete()` is a no-op passthrough and no live/DLL-backed
interface lookup is required):

- `TestOwnershipSuffixDiscriminator::test_old_predicate_matched_all_derived_members_too`
  -- sanity-checks the bug shape itself (old predicate matches all of them).
- `TestOwnershipSuffixDiscriminator::test_new_discriminator_excludes_only_the_derived_members`
  -- static suffix-string assertion for the six derived members plus
  `EtymologyOS` (OS) and `DialectLabelsRS` (RS).
- `TestClonePropertiesBehaviour::test_derived_members_are_not_cleared_or_touched`
  -- EFFECT assertion: calls the real `clone_properties`, asserts
  `dest_member.clear_calls == 0` for each of the six derived members.
  **This is the regression test.** Verified by temporarily monkeypatching
  `lcm_casting._OWNED_OR_REFERENCE_SUFFIXES = ("",)` (every string ends
  with `""`, reproducing the old unconditional-match behaviour) and
  re-running: all six members flip to `clear_calls == 1`, i.e. this
  assertion is the one that catches a regression back to the old
  duck-typed predicate. Restored after the check; not left in the test
  file (the regression is instead documented as a monkeypatch experiment
  in this report, plus a code comment in the test pointing at this same
  assertion).
- `TestClonePropertiesBehaviour::test_owned_collection_is_still_cleared_and_cloned`
  -- EFFECT assertion that `EtymologyOS` (a genuine OS member) is still
  routed through Clear(), i.e. the mandatory no-narrowing check at the
  behavioural level, not just the static-string level.
- `TestClonePropertiesBehaviour::test_reference_collection_member_is_still_cleared`
  -- same no-narrowing check for a genuine RS member (`DialectLabelsRS`).

### Test run

```
python -m pytest tests/test_issue321_clone_properties_ownership_discriminator.py -v
=> 5 passed
python -m pytest tests/test_public_casting_export.py tests/operations/test_collection_cast_pattern.py \
    tests/operations/test_owner_cast_pattern.py tests/operations/test_yield_cast_pattern.py \
    tests/test_issue321_clone_properties_ownership_discriminator.py -q
=> 132 passed, 5 skipped (pre-existing requires_live_project tests, unaffected by this change)
```

All honest -- no failures suppressed, no test skipped to make this report
look cleaner. The 5 skips predate this change and are unrelated
(`requires_live_project`-marked tests not run in this non-live session).

## What was NOT done (explicitly out of scope)

- No refactor of `clone_properties`'s overall control flow, recursion, or
  exception handling beyond the one guard expression.
- No change to `PhonologicalRuleOperations.py`, `PhonemeOperations.py`, or
  `EnvironmentOperations.py` (the three real call sites) -- they call
  `clone_properties` unchanged; its externally observable contract for
  every currently-reachable caller argument type is unchanged except for
  `IPhCode.ReferringObjects`, which was already a no-op.
- No live re-verification of `IFsFeatStruc` / `IPhContext` in this cycle
  (documented gap carried forward from cycle 1, see above).
- No commit or push -- per instructions, changes are left staged/unstaged
  in the working tree for the owning session to commit.
