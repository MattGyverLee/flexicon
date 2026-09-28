# Cycle 2 -- T2.8 verification report

**Provenance.** The dispatched `lex-verification` subagent died mid-run on an
account spend limit (HTTP 429, `req_011CfBfhXFd1RmrUNuwMSrvo`) after its
regression runs but before writing any file. The **main session** re-ran the
verification and wrote this report and
`evidence/live-T2-notebook.md`. Independent of the fix author, not independent
of the orchestrator.

**Verdict: PASS**, with one honestly-scoped limitation.

## What was proven

- **Live, not mock.** 25 collected / 25 passed on the two campaign test files,
  plus 4/4 on a freshly-written independent probe. `tests/live_status.json`
  read back `"run_mode": "live"` after both runs. `--collect-only` was run
  first each time, so neither result is a no-tests-collected zero.
- **#302.** Pre/post state was obtained by re-querying
  `lp.ResearchNotebookOA.RecordsOC` and diffing HVO sets -- never by asserting
  on an in-hand reference. Seed -> `Duplicate()` -> `Delete()` x2 returns the
  collection to its exact starting HVO set.
- **#261.** Three routed methods (`GetSubRecords`, `GetParentRecord`,
  `GetLocations`) accept a bare Python `int` HVO and resolve. An invalid HVO
  still raises `FP_ParameterError`; a genuine `AttributeError` now propagates
  as itself instead of being relabelled. C6's mask is confirmed off.
- **Carve-outs intact.** The C3 site survives at `:238` with its import; the
  three `LexSenseOperations` sites and `compound_rule.py` are untouched.
- **No regressions.** 1876 passed / 0 failed offline vs 1883 / 0 at `03d82c6`.
  The -7/+20 delta closes exactly: 7 deleted mock tests out, 20 live tests in.

## The limitation, not buried

`Duplicate()` **does not run to completion** and was not verified end-to-end.
Four lines after the #302 placement it raises `AttributeError:
'ITsString' object has no attribute 'CopyAlternatives'` -- T2.4 finding 1, a
pre-existing out-of-scope defect. The #302 *placement* is verified by its
observable effect on `RecordsOC` before the crash, and the probe pins the
crash to that specific defect so a real placement regression cannot hide
behind it. `Create()` is blocked by the same defect, which is why both the
crew's tests and my probe seed records through the raw factory.

Also worth flagging for whoever fixes that defect: the transaction layer logs
`no mark available, rollback not performed` on this raise, so the partial
duplicate persists. Harmless in a sandbox, not harmless in a real project.

## Disagreement check

I initially wrote the probe expecting `Duplicate()` to return cleanly, and it
failed. On inspection the crew's own test had already documented this exact
behaviour and asserted around it correctly. Their handling was sound; my
expectation was wrong. Corrected rather than reported as a defect.
