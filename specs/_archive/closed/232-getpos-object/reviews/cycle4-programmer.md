# Cycle 4 — Programmer report: close two P1 findings on issue #232 fix

## Files changed

- `flexicon/code/lcm_casting.py` (~lines 354-373 added; lines 410-441 → 410-428
  rewritten) — new `_MSA_POS_PROPERTY` dict + public `POS_BEARING_MSA_CLASSES`
  frozenset added immediately above `get_pos_from_msa()`; the function's
  if/elif chain replaced with a dict lookup.
- `flexicon/code/Lexicon/LexSenseOperations.py` (lines 45-52 import block;
  line ~1199 call site) — deleted the local `_POS_BEARING_MSA_CLASSES`
  literal, now imports `POS_BEARING_MSA_CLASSES` from `..lcm_casting`, and
  `GetPartOfSpeechObject`'s gate uses the imported name.
- `tests/test_lexsense_getpos_object.py` — header rationale corrected (lines
  ~17-32); replaced the stale "constant is a module assignment" test with
  four coupling tests; `_build_harness()` now injects
  `POS_BEARING_MSA_CLASSES` into the synthetic namespace instead of lifting
  a (now-removed) local assignment out of the AST.

## Final dispatch table (lcm_casting.py)

```python
_MSA_POS_PROPERTY = {
    "MoStemMsa": "PartOfSpeechRA",
    "MoDerivAffMsa": "ToPartOfSpeechRA",  # output POS of derivation (see #87)
    "MoInflAffMsa": "PartOfSpeechRA",
    "MoUnclassifiedAffixMsa": "PartOfSpeechRA",
}
POS_BEARING_MSA_CLASSES = frozenset(_MSA_POS_PROPERTY)
```

`get_pos_from_msa()` now:
```python
class_name = msa.ClassName
pos_property = _MSA_POS_PROPERTY.get(class_name)
if pos_property is None:
    return None
try:
    interface_type = _interface_cache.get(class_name)
    if interface_type:
        concrete = interface_type(msa)
        return getattr(concrete, pos_property)
except Exception:
    pass
return None
```

## Semantic equivalence confirmed

- `_ensure_interfaces()` call and `if not hasattr(msa, "ClassName"): return None`
  guard above this block are untouched.
- Four known ClassNames: same property read per type (`PartOfSpeechRA` for
  Stem/InflAff/UnclassifiedAffix, `ToPartOfSpeechRA` for DerivAff), same
  `_interface_cache.get(class_name)` lookup, same "falsy interface_type ->
  no return, falls through to trailing `return None`" behavior, same
  "any exception in cast/read -> `except: pass` -> `return None`".
- Unknown ClassName: old code — none of the if/elif branches match, no
  exception raised, falls to trailing `return None`. New code — returns
  `None` immediately via the `pos_property is None` check before entering
  the try block. Same observable result (`None`), reached one statement
  earlier; no exception is possible in the gap either way, so this is
  behavior-preserving.
- Missing `ClassName` attribute: unchanged, still handled by the untouched
  guard before the dispatch table is consulted.

`LexSenseOperations.GetPartOfSpeechObject` behavior is unchanged: it still
warns+returns `None` for unrecognized subtypes and returns `None` silently
for no-MSA, now gated on the imported `POS_BEARING_MSA_CLASSES` instead of
a local copy.

## Test-header fix

Replaced the false "matches test_agent_version_unicode.py" claim (that file
is pure static AST, no exec step) with the real reason, based on reading
`tests/conftest.py:41-52`: three sibling files
(`test_affix_template_wrappers.py`, `test_annotation_wrappers.py`,
`test_prohibition_wrappers.py`) stub `sys.modules["SIL"] = MagicMock()` at
module scope, which conftest documents as poisoning the real CLR `SIL`
namespace for any later real import of flexlibs2/flexicon modules in the
same process (why those three are in `collect_ignore`). This file avoids
that risk entirely — and avoids needing a real FieldWorks install — by
never importing `LexSenseOperations` directly, instead extracting
`GetPartOfSpeechObject`'s own AST and exec'ing it into an isolated
synthetic module.

## Test rewrite

Removed `test_pos_bearing_classes_constant_has_exactly_the_four_known_subtypes`
(pinned the old module-level assignment). Added, AST-based and consistent
with the file's existing style:
- `test_lexsense_no_longer_defines_its_own_msa_class_list` — fails if
  `_POS_BEARING_MSA_CLASSES` reappears as a module-level assignment in
  `LexSenseOperations.py`.
- `test_lexsense_imports_pos_bearing_classes_from_lcm_casting` — asserts an
  `ImportFrom` of `lcm_casting` bringing in `POS_BEARING_MSA_CLASSES`.
- `test_get_part_of_speech_object_gates_on_the_imported_canonical_name` —
  asserts the method body references `POS_BEARING_MSA_CLASSES`.
- `test_lcm_casting_dispatch_table_has_exactly_the_four_known_subtypes` —
  parses `lcm_casting.py`'s AST and asserts `_MSA_POS_PROPERTY`'s keys are
  exactly the four known subtypes.

Together these fail if the two files diverge again in either direction.
`_build_harness()` now injects `module.POS_BEARING_MSA_CLASSES` (the same
four literal values) directly into the synthetic namespace so the
behavioral (mock-based) tests keep running unmodified.

## Verification (actual output)

`python -m pytest tests/test_lexsense_getpos_object.py -v`:
```
collected 14 items
... (all 14 PASSED, listed individually) ...
======================== 14 passed, 1 warning in 1.76s ========================
```

`python -m pytest tests/ -q -k "msa or pos or casting"`:
```
5 failed, 137 passed, 1320 deselected, 147 warnings, 1 error in 14.82s
FAILED tests/test_consolidation_coverage.py::TestInheritanceVerification::test_agent_operations_inherits_from_possibility_item_operations
FAILED tests/test_consolidation_coverage.py::TestInheritanceVerification::test_overlay_operations_inherits_from_possibility_item_operations
FAILED tests/test_consolidation_coverage.py::TestInheritanceVerification::test_translation_type_operations_inherits_from_possibility_item_operations
FAILED tests/test_consolidation_coverage.py::TestInheritanceVerification::test_publication_operations_inherits_from_possibility_item_operations
FAILED tests/test_consolidation_coverage.py::TestConsolidatedClassStructure::test_possibility_item_operations_parent_exists
ERROR tests/contract/test_lcm_contract.py::TestContractExtraction::test_contract_has_repositories
```

These 5 failures + 1 error matched the `-k` filter only because
"possibility"/"repositories" contain the substrings "pos"/"pos" — they are
unrelated to MSA/POS-object/casting logic (they concern
`PossibilityItemOperations` inheritance consolidation and a live LCM
contract snapshot). Confirmed pre-existing and unrelated: `git stash`
(removing all of this session's changes, including the not-yet-committed
issue-#232 fix) then re-running the same two files reproduced the same
category of failures (in fact more — 13 failed/16 errored, since the
contract test needs a live FieldWorks/LCM snapshot this environment
doesn't have). Changes were restored via `git stash pop` immediately after
and `git status` confirmed the working tree matched pre-stash state. No
`msa`/`pos`/`casting`-filtered test touching `get_pos_from_msa`,
`GetPartOfSpeechObject`, `POS_BEARING_MSA_CLASSES`, or MSA dispatch
regressed.

No git add/commit performed.
