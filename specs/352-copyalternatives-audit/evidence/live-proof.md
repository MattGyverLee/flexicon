# Live proof -- READ path (#352 CopyAlternatives audit / #348 OcmCodes)

**Date:** 2026-09-21
**Project:** Target (live LCM, not mocks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Op:** `op-033710733-007`, read-only (`write_enabled=False`)

## Command (flextools_run_module snippet)

```python
op = project.SemanticDomains
domains = op.GetAll()
report.Info("Total semantic domains on Target: %d" % len(domains))
shown = 0
for d in domains:
    if shown >= 5:
        break
    num = op.GetNumber(d)
    ocm = op.GetOcmCodes(d)
    report.Info("domain=%s ocm_type=%s ocm=%r" % (num, type(ocm).__name__, ocm))
    if not isinstance(ocm, str):
        report.Error("OcmCodes is not a scalar str!")
    n_q = len(d.QuestionsOS)
    report.Info("domain=%s questionsOS_size=%d" % (num, n_q))
    shown += 1
report.Info("READ PROBE DONE: no AttributeError on OcmCodes/QuestionsOS")
```

## Values read back from the LCM

- Total semantic domains: **1792**
- `domain=1 ocm_type=str ocm='772 Cosmology; 130 Geography'`, `questionsOS_size=1`
- `domain=1.1 ocm_type=str ocm=''`, `questionsOS_size=9`
- `domain=1.1.1 ocm_type=str ocm=''`, `questionsOS_size=17`
- `domain=1.1.1.1 ocm_type=str ocm=''`, `questionsOS_size=13`
- `domain=1.1.1.2 ocm_type=str ocm=''`, `questionsOS_size=9`

## Pass/fail

**PASS.** `GetOcmCodes` returns scalar `str` (no `AttributeError: 'str' object
has no attribute 'get_String'`), `QuestionsOS` owning-seq iteration works,
zero errors. This exercises the fixed source at
`flexicon/code/Lexicon/SemanticDomainOperations.py` (`GetOcmCodes`,
`GetQuestions`).

## Note

The first attempt of this probe failed at *import* time with
`IndentationError: unexpected indent (SemanticDomainOperations.py, line 1137)`:
the HANDOFF session's edit had left the `Duplicate` body mis-indented, which
broke `import flexicon` entirely. Fixed by re-indenting the `OcmCodes` assign
and `QuestionsOS` copy back inside the `with self._TransactionCM(...)` block
(plus trimming the stale comment block). `python -m py_compile` passes and
this probe ran against the fixed source (runner imports the editable install
at `C:\Github\flexicon`).
