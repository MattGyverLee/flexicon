# Issue #358 -- live verification evidence

## Command

```bash
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_variants_live.py -m requires_live_project -q
```

## run_mode

Not executed on this agent: Linux cloud pod has no FieldWorks / python.net LCM
stack (`python`/`FLExInitialize` unavailable in PATH; Windows-only live suite).

## Pre-state / post-state (LCM read-back)

**FAIL: unverified** -- live LCM read-back was not performed on this run.

## Offline substitute (machine-checkable)

```bash
python3 -m pytest -m "not requires_live_project" \
  tests/test_syncable_properties_member_ratchet.py \
  tests/operations/test_variant_syncable_properties_offline.py -q
```

Expected: all selected tests pass; ratchet no longer allowlists
`ShowComplexFormsIn` on `VariantOperations.py`.

## Result

**FAIL: unverified (live)** -- fix is backed by liblcm baseline contract +
offline tests only. Re-run the live command above on a FieldWorks host before
merge if write-path duplicate behaviour must be signed off in LCM.
