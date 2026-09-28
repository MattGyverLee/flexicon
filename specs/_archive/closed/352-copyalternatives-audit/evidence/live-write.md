# Live proof -- WRITE path (#352 CopyAlternatives audit / #348 OcmCodes)

**Date:** 2026-09-21
**Project:** Target (live LCM, not mocks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Ops:** `op-033748697-011` (first attempt, failed live -- see below),
`op-033847898-015` (orphan cleanup), `op-033902701-017` (passing round-trip),
`op-033910856-018` (post-cleanup verify)
**Safety:** `validate_only` green on all 11 gates (`op-033740657-009`);
mutation plan reviewed (`Duplicate` + `Delete`); pre-write backup taken by the
runner at `C:\Users\thoua\.flextoolsmcp\backups\Target\20260921T083748Z\Target.fwdata`;
project lock `free`; `confirmed=True`.

## Command (flextools_run_module snippet, write_enabled=True)

```python
op = project.SemanticDomains
cands = [d for d in op.GetAll() if len(d.QuestionsOS) > 0 and len(op.GetSubdomains(d, recursive=False)) == 0]
report.Info("leaf domains with questions: %d" % len(cands))
source = cands[0]
src_num = op.GetNumber(source)
src_ocm = op.GetOcmCodes(source)
src_nq = len(source.QuestionsOS)
report.Info("PRE source=%s ocm=%r n_questions=%d" % (src_num, src_ocm, src_nq))
dup = None
if modifyAllowed:
    dup = op.Duplicate(source, deep=True)
if modifyAllowed:
    if dup is not None:
        try:
            dup_ocm = op.GetOcmCodes(dup)
            dup_nq = len(dup.QuestionsOS)
            report.Info("POST dup_of=%s ocm=%r n_questions=%d" % (src_num, dup_ocm, dup_nq))
            assert dup_ocm == src_ocm, "OcmCodes not conserved"
            assert dup_nq == src_nq, "Questions count not conserved"
            report.Info("WRITE PROBE PASS: OcmCodes + QuestionsOS conserved")
        finally:
            op.Delete(dup)
            report.Info("cleanup: duplicate deleted")
report.Info("WRITE PROBE DONE")
```

(A leaf domain is used so the `deep=True` subdomain branch is a no-op;
the `QuestionsOS` copy path is still fully exercised. All `Delete` calls sit
directly under `if modifyAllowed:` -- the preflight rejects `Delete` in a
bare `finally:`, so cleanup is structured as guarded blocks instead.)

## Pre-state read back from the LCM

- Leaf domains with questions: **1377**
- `PRE source=1.1.1.1 ocm='' n_questions=13`

## Post-state read back from the LCM (duplicate, before cleanup)

- `POST dup_of=1.1.1.1 ocm='' n_questions=13`

## Pass/fail

**PASS.** `OcmCodes` (`'' == ''`) and `QuestionsOS` size (13 == 13) conserved
across `Duplicate(source, deep=True)`; `TEST` duplicate deleted in the same
call; post-probe verify (`op-033910856-018`) shows total=**1792**,
numbers_with_dups=**0** -- no orphan left behind.

## Two live-found defects fixed along the way (same session)

1. **`IndentationError` (line ~1137).** The HANDOFF session's edit left the
   `Duplicate` tail mis-indented, so `import flexicon` itself failed. Fixed by
   re-indenting the `OcmCodes` assign + `QuestionsOS` copy inside
   `with self._TransactionCM(...)`; verified with `py_compile` + the
   read-path probe above.
2. **`OccurrencesRS` does not exist on `ICmSemanticDomain`** (live
   `AttributeError` on `op-033748697-011`). The deep branch copied a
   `WfiWordform` pattern (`OccurrencesRS`) onto semantic domains -- the same
   bug family as #36/#39/#40. Removed the block; the docstring already said
   referring objects are not copied, and `GetProperties` notes
   `OccurrencesRS` as "not included". Because the runner opens the project
   with `undoable=False`, the half-finished duplicate persisted as an orphan
   (count 1793, dup number `1.1.1.1`); it was deleted (`op-033847898-015`)
   and the count returned to 1792 before the passing run.
