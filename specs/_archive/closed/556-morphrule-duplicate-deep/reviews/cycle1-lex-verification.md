# Verification Report -- issue #556 (MorphRuleOperations Duplicate deep-copy mocks)

**Verdict:** PASS
**Live run:** yes | **run_mode:** live
**Evidence:** specs/_archive/closed/556-morphrule-duplicate-deep/evidence/live-duplicate-deep.md
**Project:** Sena 3 (sena3_sandbox)

## Claim vs. observed
| Claim | Observed live | Status |
|-------|---------------|--------|
| deep=True copies slot refs | HVO lists equal on re-queried duplicate | PASS |
| deep=False leaves slots empty | dup prefix/suffix/proclitic/enclitic == [] on re-query | PASS |
| insert_after places dup at source_index+1 | post_order.index(dup_hvo) == source_index+1 | PASS |
| Mock fixture fix restores offline suite | 6 passed (was 4 failing) | PASS |

## Commands / output (tail)
```
python -m pytest tests/operations/test_morphrule_duplicate_deep.py -m "not requires_live_project" -q
6 passed in 0.95s

python -m pytest -m "not requires_live_project" -q
2534 passed, 1050 deselected, 16 warnings in 13.38s

FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue556_morphrule_duplicate_deep_live.py tests/operations/test_issue537_morphrule_duplicate_hvo_live.py -m requires_live_project -q
1 failed, 2 passed in 6.09s

live_status.json run_mode: live
```

## Pre-existing failure confirmed
`test_issue537...test_duplicate_affix_template_insert_after_raw_object_view`
fails with `AttributeError: 'ICmObject' object has no attribute 'Name'` at
`MorphRuleOperations.py:949` (`duplicate.Name.CopyAlternatives`) -- a
`__ResolveObject` cast gap for `MoInflAffixTemplate`. `git diff --stat
origin/main...HEAD` shows this branch touches only test files and the
evidence doc, no `flexicon/code/*`, confirming the failure is inherited
from main, not introduced.

## Mock suite (regression, supplementary)
2534 passed, 0 failed (not requires_live_project).

## Blockers
None.

## Recommendation
APPROVE (pre-existing #537 failure should be filed/tracked separately, not blocking this PR).
