# LIVE EVIDENCE -- #274 bucket-A inline comparison-symmetry fix

**Feature:** name-field-whitespace-identity
**Issue:** flexicon#274 (Q-242A), bucket-A sites
**Approach:** owner decision 2026-09-08 -- **"Extend C4's inline fix."**
Apply C4's proven both-sides INLINE shape
(`normalize_match_key(x, casefold=...).strip()` on BOTH needle and
haystack, bare `.strip()`) to the 7 still-asymmetric bucket-A sites per
NF6's ruling that all 10 sites are in scope. NF5's central-strip plan
(strip inside `normalize_match_key`) is REJECTED for this work.

C4 fence honored: `flexicon/code/Shared/string_utils.py` and
`flexicon/code/BaseOperations.py` are NOT edited; no `.strip()` added to
`normalize_match_key`; no shared helper added.

---

## The 7 sites edited (both needle and haystack now `.strip()` the KEY)

Per-site `casefold=` value preserved (NF3: case unchanged per site).
Existing `if not name or not name.strip(): return None` guards untouched
(all 7 already had them).

| # | File | Method | needle | haystack | casefold |
|---|------|--------|--------|----------|----------|
| 1 | `flexicon/code/Lexicon/SemanticDomainOperations.py` | `FindByName` | `normalize_match_key(name, casefold=True).strip()` | `...(domain_name, casefold=True).strip()` | True |
| 2 | `flexicon/code/Lists/AgentOperations.py` | `Find` | `normalize_match_key(name, casefold=True).strip()` | `...(agent_name, casefold=True).strip()` | True |
| 3 | `flexicon/code/Lists/PossibilityListOperations.py` | `FindList` | `normalize_match_key(name, casefold=True).strip()` | `...(list_name, casefold=True).strip()` | True |
| 4 | `flexicon/code/Lists/PossibilityListOperations.py` | `FindItem` | `normalize_match_key(name, casefold=True).strip()` | `...(item_name, casefold=True).strip()` | True |
| 5 | `flexicon/code/Lists/possibility_item_base.py` | `Find` | `normalize_match_key(name, casefold=True).strip()` | `...(item_name, casefold=True).strip()` | True |
| 6 | `flexicon/code/Notebook/LocationOperations.py` | `Find` | `normalize_match_key(name, casefold=True).strip()` | `...(location_name, casefold=True).strip()` | True |
| 7 | `flexicon/code/Shared/FilterOperations.py` | `Find` | `normalize_match_key(name, casefold=False).strip()` | `...(filter_data["name"], casefold=False).strip()` | False |

The `list_name and`/`item_name and` truthiness pre-guards at sites 3, 4
were preserved (the `.strip()` was appended after the existing
`normalize_match_key(...)` call, before `== target`).

Not touched (out of scope by ruling): the 3 already-fixed families
(Text/Anthropology/Check -- already this shape); `ScrDraftOperations.Find`
(containment match, NF5 condition 3 fences it off); `normalize_match_key`,
`string_utils.py`, `BaseOperations.py` (C4 fence).

---

## Commands

Offline suite (DELTA rule -- pre-edit baseline reconstructed via a
pathspec'd stash of my own authored paths only, per C13; a bare
`git stash` is FORBIDDEN in this clone):

```
# pre-edit baseline (my 8 code/test paths stashed with pathspec)
git stash push -- <7 source files> tests/test_normalize_match_key.py \
                  tests/operations/test_name_field_identity_probe.py
python -m pytest tests -m "not requires_live_project" -q
#   -> 1510 passed, 1 skipped, 561 deselected
git stash pop        # git stash list confirmed EMPTY afterward

# post-edit
python -m pytest tests -m "not requires_live_project" -q
#   -> 1514 passed, 1 skipped, 563 deselected
```

Focused unit:

```
python -m pytest tests/test_normalize_match_key.py -q
#   -> 15 passed
```

Live probe:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_name_field_identity_probe.py \
    -m requires_live_project -q
#   -> 22 passed
```

## run_mode

`tests/live_status.json`: **`"run_mode": "live"`**,
`"run_timestamp": "2026-09-08T21:03:31Z"`, `uncategorized_live_tests: []`.
Not mock. LocationOperations/add and AgentOperations/add both recorded
`"status": "pass"` for the two new tests.

## Offline DELTA

| | passed | skipped | deselected |
|---|---|---|---|
| pre-edit | 1510 | 1 | 561 |
| post-edit | 1514 | 1 | 563 |
| **delta** | **+4** | 0 | **+2** |

Expected and correct: `passed +4` = the 4 whitespace-identity unit tests
in `TestNormalizeMatchKeyWhitespaceIdentity` flipped from `xfail` (which is
not counted as "passed") to real passes after being rewritten to the C4
contract; `deselected +2` = the 2 new `requires_live_project` probe tests
(PN21 Location, PN22 Agent). No offline test regressed. No foreign
failure appeared.

---

## Live read-back (unreachable-object half now FIXED)

Both objects created through the real public `Create()` API with a
trailing-space name, then looked up with the UNPADDED needle, then the
FOUND object re-queried from the LCM (not the value passed in).

### PN21 -- LocationOperations

| stage | value read from LCM |
|-------|---------------------|
| pre-state (stored Name, direct read of created object) | `'TEST_NF_Loc '` (trailing space) |
| `Location.Find("TEST_NF_Loc")` (unpadded needle) | FOUND (`ICmLocation`, not None) |
| `Location.Find("TEST_NF_Loc ")` (padded needle) | FOUND (`ICmLocation`, not None) |
| post-state (stored Name, RE-QUERIED via the Find result) | `'TEST_NF_Loc '` (byte-identical, trailing space intact) |

PRE-FIX: `Find("TEST_NF_Loc")` stripped only the needle and missed the raw
haystack `'TEST_NF_Loc '` -- the object was unreachable by name. POST-FIX:
found by both needles. **PASS.**

### PN22 -- AgentOperations

| stage | value read from LCM |
|-------|---------------------|
| pre-state (stored Name, direct read of created object) | `'TEST_NF_Agt '` (trailing space) |
| `Agents.Find("TEST_NF_Agt")` (unpadded needle) | FOUND (`ICmAgent`, not None) |
| `Agents.Find("TEST_NF_Agt ")` (padded needle) | FOUND (`ICmAgent`, not None) |
| post-state (stored Name, RE-QUERIED via the Find result) | `'TEST_NF_Agt '` (byte-identical, trailing space intact) |

**PASS.**

Fixtures: `target_sandbox` ONLY (fresh tempdir copy). The real Target was
never touched; no `scripts/restore_*.py` run. Created objects prefixed
`TEST_NF_`; sandbox teardown discards them.

---

## Per-site PASS/FAIL

The 7 sites divide into two verification tiers.

- **Directly live-verified (2/7):** `LocationOperations.Find` (PN21) and
  `AgentOperations.Find` (PN22) -- created a padded name, found it with an
  unpadded needle, read the stored value back from the LCM. **PASS
  (live).**
- **Verified by the shared inline pattern + unit pin (5/7):**
  `SemanticDomainOperations.FindByName`, `PossibilityListOperations.FindList`,
  `PossibilityListOperations.FindItem`, `possibility_item_base.Find`,
  `FilterOperations.Find`. Each received the byte-identical edit shape as
  the two live-verified sites (confirmed by inspection of the diff), and
  the pattern itself -- `normalize_match_key(x, casefold=...).strip()` on
  both sides -- is pinned whitespace-insensitive by
  `test_inline_pattern_is_whitespace_insensitive` and
  `test_inline_pattern_whitespace_only_reduces_to_empty` in
  `tests/test_normalize_match_key.py` (both casefold=True and casefold=False
  branches). **PASS (pattern + unit); not independently driven through each
  of these 5 public APIs live.**

---

## WHAT WAS NOT EXERCISED

- **The 5 non-Location/Agent bucket-A sites were not each driven live
  through their own public `Create`/`Find` API.** Location and Agent were
  chosen as the two live representatives (task Part 3 item 4). The other
  five carry the byte-identical edit and are covered by the pure-Python
  unit pins on the inline pattern, but no live per-API create-then-find was
  run for them. Reason: the two live representatives establish the pattern
  works end-to-end against a real LCM; the remaining five are the same
  mechanical edit to the same-shaped code and are pinned by the unit tests
  -- a full live sweep of all seven was not requested and would add cost
  without materially changing confidence in an identical edit.
- **`FilterOperations.Find` (casefold=False) was verified live only
  indirectly.** Its `casefold=False` branch is exercised by
  `test_inline_pattern_is_whitespace_insensitive`'s final assertion in
  pure Python, not against a live filter round-trip. The site's edit is
  byte-identical in shape to the six casefold=True sites.
- **No persist-path change was made or needed at any of the 7 sites.**
  These are read-by-name lookups; Location.Create and Agent.Create already
  persisted the caller's raw bytes before this feature (confirmed live:
  pre-state read back byte-identical). The unreachable-object defect was
  purely the comparison asymmetry, which the inline fix closes.
