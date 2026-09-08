# Q5 -- `flexlibs2` alias ratchet: 9 offending imports

Decision record for Q5 in `specs/242-paragraph-whitespace/spec.md` section 6.

Branch: `spec/242-gate-and-name-field-identity` (changes left in the working
tree; not committed here).

## The failure

`tests/test_flexlibs2_alias_ratchet.py::TestFlexlibs2AliasIsInboundOnly::test_no_executable_flexlibs2_imports_outside_alias_package`
failed on 9 executable `flexlibs2` imports left behind by the
`flexlibs2 -> flexicon` rename (PR #241, commit `ec54432`). The ratchet was
added by that same commit and has been red since, unnoticed because the
Python environment was broken until now.

## How a site becomes exempt (the mechanism that shapes the fix)

The ratchet is a static AST scan. Its only exemption mechanism is
`_ALLOWED_PATHS` -- a set of paths (file OR directory subtree) that
`_iter_python_files()` skips wholesale via `_is_relative_to`. Pre-change it
held exactly two entries: the `flexlibs2/` alias package and the ratchet file
itself. There is no marker, no per-line pragma, no comment-based opt-out.

Consequences that drove the decision:

* An exemption is **file-granular at finest**. Exempting a file blinds the
  ratchet to *every* alias import in it, forever, including ones added later.
* The scan only sees `ast.Import` / `ast.ImportFrom` nodes. Docstrings and
  comments are free (`_executable_flexlibs2_imports` docstring says so
  explicitly), and a sibling test
  (`test_no_flexlibs2_dotted_string_references_outside_alias_package`) closes
  the string-literal hole (`@patch("flexlibs2....")`) -- but **not**
  `importlib.import_module("flexlibs2")`, because that argument is a
  single-segment string with no dot and `_STRING_FLEXLIBS2_RE` requires
  `flexlibs2` followed by at least one `.segment`.

## Site-by-site classification (all 9 verified in context)

| # | Site | Imported symbol | Verdict |
|---|------|-----------------|---------|
| 1 | `tests/conftest.py:1392` | `flexlibs2.code.FLExProject.FLExProject` | INCIDENTAL |
| 2 | `tests/conftest.py:1451` | `flexlibs2.code.FLExProject.FLExProject` | INCIDENTAL |
| 3 | `tests/operations/test_issue251_252_256_feature_struct_probe.py:36` | `...FLExProject` | INCIDENTAL |
| 4 | `tests/operations/test_natural_classes.py:917` | `...FP_ParameterError` | INCIDENTAL |
| 5 | `tests/operations/test_natural_classes.py:954` | `...FP_ParameterError` | INCIDENTAL |
| 6 | `tests/operations/test_natural_class_feature_sync.py:721` | `...FP_ParameterError` | INCIDENTAL |
| 7 | `tests/operations/test_owner_cast_pattern.py:71` | `...FLExProject` | INCIDENTAL |
| 8 | `tests/operations/test_owner_cast_pattern.py:630` | `flexlibs2.code.lcm_casting.cast_to_concrete` | INCIDENTAL |
| 9 | `tests/write_path_transactions/test_capabilities.py:96` | `import flexlibs2` | **DELIBERATE** |

Evidence for INCIDENTAL (1-8): every one of these is an ordinary lazy import
of a library symbol the test needs (`FLExProject` inside a fixture's
`try/except` skip-guard, `FP_ParameterError` inside a
`pytest.raises` test body, `cast_to_concrete` in a casting test). None is
inside a test that asserts anything about deprecation; none references
`DeprecationWarning`, `warnings`, `sys.modules["flexlibs2"]` or the alias's
identity. Site 6 is the clearest proof of "leftover": it sits immediately
below a already-renamed `from flexicon.code.Grammar.NaturalClassOperations
import NaturalClassOperations` in the same statement block -- the rename
touched one line of the pair and missed the other. Substituting `flexicon`
for `flexlibs2` at all eight sites is behavior-identical by construction: the
alias package's whole contract (see `flexlibs2/__init__.py`) is that
`flexlibs2.code.X.Y is flexicon.code.X.Y`.

Evidence for DELIBERATE (9): the import is the body of
`TestCapabilities::test_capabilities_reachable_through_the_flexlibs2_alias`,
wrapped in `warnings.catch_warnings()` with
`simplefilter("ignore", DeprecationWarning)` -- i.e. it knowingly suppresses
the alias's own deprecation warning -- and the assertion is
`flexlibs2.CAPABILITIES is flexicon.CAPABILITIES`, an identity check whose
entire subject is the alias. Its docstring states the intent ("FlexTools
scripts on disk still import under the old name"). Rewriting it to
`flexicon` would delete the test, not fix it.

No other site is deliberate. 8 incidental / 1 deliberate.

## Decision

**Sites 1-8 (incidental):** rewritten `from flexlibs2.code.` ->
`from flexicon.code.`. Nothing else changed -- diff is 8 single-line import
swaps (`git diff --stat`: 4 files, 2 lines each in the pair-sites).

**Site 9 (deliberate):** the test was **moved** into a new dedicated module,
`tests/test_flexlibs2_alias_surface.py`, which is added to `_ALLOWED_PATHS`.
The test body is preserved verbatim (same `catch_warnings` block, same
identity assertion); only its home and class name changed
(`TestCapabilities` -> `TestFlexlibs2AliasSurface`). A comment at the old
site in `test_capabilities.py` points to the new home so the move is
discoverable. `_ALLOWED_PATHS` gained a "keep this set MINIMAL" note stating
the admission rule, and the new file carries a SCOPE FENCE header forbidding
anything but alias-subject tests.

### Alternatives rejected

* **Exempt `tests/write_path_transactions/test_capabilities.py` in
  `_ALLOWED_PATHS`.** Rejected: exemptions are file-granular, so this blinds
  a 98-line file of which one 10-line test is about the alias. Every future
  incidental leftover in that file -- it is a write-path capabilities test
  file that will keep growing -- would pass the ratchet silently. The
  exemption surface should be a file that exists *only* to test the alias, so
  that "this file is exempt" and "this file is about the alias" are the same
  statement.
* **`importlib.import_module("flexlibs2")` in place, no exemption.**
  Rejected as a loophole, not a fix. It would work -- the AST scan sees no
  Import node, and the string-literal ratchet's regex requires a dotted
  suffix so a bare `"flexlibs2"` slips through -- but it makes the ratchet
  pass by hiding a real runtime alias walk from it, which is exactly the
  evasion the ratchet exists to catch. Worse, it establishes the pattern:
  any future leftover could be "fixed" the same way. If this were chosen it
  would also have to be *behind* an exemption to be honest, at which point
  it buys nothing over the move.
* **Leave the ratchet red.** Rejected: the test is a merge gate, and a
  permanently-red gate trains everyone to ignore it.
* **Delete the deliberate test.** Rejected: the alias ships and is
  documented as supported until v5.0.0; the identity guarantee needs
  coverage.

The chosen fix leaves the ratchet strictly *more* meaningful than a
find-and-replace would: the exempted surface is one 47-line file with a
documented admission rule, and all 1294 collected offline tests plus the
whole `tests/` tree remain scanned.

## Commands and results

All runs offline, marker-filtered. `FLEXLIBS_REQUIRE_LIVE` never set; no
live test, no `scripts/restore_*.py`.

### Before

Captured by stashing this task's changes and running the ratchet against
plain HEAD (`git stash push -u` / run / `git stash pop`):

```
$ python -m pytest tests/test_flexlibs2_alias_ratchet.py -m "not requires_live_project" -q -p no:randomly
1 failed, 1 passed in 1.74s

E  AssertionError: Found executable `flexlibs2` imports outside the alias package. Use `flexicon` instead:
E      tests\conftest.py:1392: from flexlibs2.code.FLExProject import ...
E      tests\conftest.py:1451: from flexlibs2.code.FLExProject import ...
E      tests\operations	est_issue251_252_256_feature_struct_probe.py:36: from flexlibs2.code.FLExProject import ...
E      tests\operations	est_natural_classes.py:917: from flexlibs2.code.FLExProject import ...
E      tests\operations	est_natural_classes.py:954: from flexlibs2.code.FLExProject import ...
E      tests\operations	est_natural_class_feature_sync.py:721: from flexlibs2.code.FLExProject import ...
E      tests\operations	est_owner_cast_pattern.py:71: from flexlibs2.code.FLExProject import ...
E      tests\operations	est_owner_cast_pattern.py:630: from flexlibs2.code.lcm_casting import ...
E      tests\write_path_transactions	est_capabilities.py:96: import flexlibs2
```

Exactly the 9 sites recorded in Q5, and exactly the 9 returned independently
by `grep -rn "flexlibs2" tests/ --include=*.py` (excluding the ratchet file
itself). The sibling
`test_no_flexlibs2_dotted_string_references_outside_alias_package` was
already green before and after.

### After

```
$ python -m pytest tests/test_flexlibs2_alias_ratchet.py tests/test_flexlibs2_alias_surface.py tests/write_path_transactions/test_capabilities.py -m "not requires_live_project" -q
8 passed in 1.77s
```

Affected-files slice (the requested command, plus the two files the fix
added/created):

```
$ python -m pytest tests/test_flexlibs2_alias_ratchet.py tests/test_flexlibs2_alias_surface.py tests/operations/test_natural_classes.py tests/operations/test_natural_class_feature_sync.py tests/operations/test_owner_cast_pattern.py tests/write_path_transactions/test_capabilities.py tests/operations/test_issue251_252_256_feature_struct_probe.py -m "not requires_live_project" -q
46 passed, 32 deselected in 1.78s
```

`tests/conftest.py` is shared infrastructure, so collection and a full
offline slice were re-proved:

```
$ python -m pytest tests/ -m "not requires_live_project" -q --collect-only
1294/1777 tests collected (483 deselected) in 0.71s

$ python -m pytest tests/ -m "not requires_live_project" -q -p no:randomly
1 failed, 1292 passed, 1 skipped, 483 deselected, 12 warnings in 4.14s
```

### The one failure is pre-existing and unrelated

`tests/contract/test_lcm_contract.py::TestLiveRegressionCheck::test_no_regressions_from_baseline`
fails with a `Windows fatal exception: access violation` inside
`flexicon/code/FLExInit.py:64 FLExInitialize`, reached from
`tests/contract/generate_lcm_snapshot.py`. Confirmed pre-existing by stashing
this task's changes and re-running:

```
$ git stash push -u -m q5-tmp
$ python -m pytest tests/contract/test_lcm_contract.py -m "not requires_live_project" -q -p no:randomly
1 failed, 21 passed, 4 warnings in 1.22s     # same test, changes absent
$ git stash pop
```

It touches no file this task modified. Not in scope for Q5; it is a separate
defect (a contract test that initializes FLEx despite carrying no
`requires_live_project` marker -- arguably a marker bug, since it means the
"offline" slice loads pythonnet/FieldWorks). It appears the main session was
working on exactly this in parallel: uncommitted changes to `.gitignore`,
`tests/contract/generate_lcm_snapshot.py` and
`tests/contract/snapshots/liblcm_baseline.json` (fixing the
`liblcm_version: "unknown"` snapshot bug) were present in the working tree
during this task and are NOT part of this change.

Note on method: the two `git stash push -u` / `git stash pop` round trips
used to capture before-state also stashed and restored that concurrent work.
Both popped cleanly and `git stash list` is empty; no work was lost. The
final verification run below was made after the pop, with the full working
tree in place.

## Files changed

* `tests/conftest.py` -- 2 import swaps (lines 1392, 1451)
* `tests/operations/test_issue251_252_256_feature_struct_probe.py` -- 1 (36)
* `tests/operations/test_natural_classes.py` -- 2 (917, 954)
* `tests/operations/test_natural_class_feature_sync.py` -- 1 (721)
* `tests/operations/test_owner_cast_pattern.py` -- 2 (71, 630)
* `tests/write_path_transactions/test_capabilities.py` -- deliberate test
  moved out, pointer comment left behind
* `tests/test_flexlibs2_alias_ratchet.py` -- `_ALLOWED_PATHS` gains the new
  alias-surface file plus a minimality note
* `tests/test_flexlibs2_alias_surface.py` -- NEW; holds the moved deliberate
  test behind a documented scope fence

## Not determined

* Whether the four `"flexlibs2"` path-segment strings in
  `tests/contract/extract_lcm_contract.py:220-229` are still wanted. They are
  filesystem fallbacks for a pre-rename source tree (`repo/flexlibs2/code/`),
  not module lookups, so neither ratchet test fires on them (the
  string-literal regex needs a dotted suffix) and nothing here changed them.
  They are dead on any post-#241 checkout; removing them is a separate
  cleanup decision, not a ratchet violation.
* The root cause of the `FLExInit` access violation above -- diagnosing it
  would require live FieldWorks work, which is out of scope and forbidden for
  this task.
