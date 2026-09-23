# Issue #301 -- live verification

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue301_unordered_getsequence.py -m requires_live_project -q
```

(No live-marked tests in this file -- reorder guard is enforced offline.)

Optional reflection command (not run this session):

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_277_environment_sequence_property.py -m requires_live_project -q
```

## run_mode

**FAIL: unverified** -- Cloud Agent Linux pod has no FieldWorks / LCM runtime.
Offline regression tests passed (see PR CI / local `python -m pytest -m "not requires_live_project" tests/operations/test_issue301_unordered_getsequence.py -q`).

## Pre-state (from issue #301 live notes on Windows)

- `WfiAnalyses.MoveUp(wordform, analysis)` -> `AttributeError: ... AnalysesOS`
- `Phonemes.MoveUp(phon_data, phoneme)` -> `AttributeError: ... PhonemesOS`

## Expected post-state

- Same calls -> `NotImplementedError` with message naming unordered `AnalysesOC` /
  `PhonemesOC` (honest failure, not silent mis-order).

## Result

**PASS (offline guard)** / **FAIL: unverified (live LCM re-probe pending Windows)**
