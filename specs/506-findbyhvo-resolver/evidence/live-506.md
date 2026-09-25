# Live verification -- issue #506

**Command:**

```bash
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue506_findbyhvo_resolver_live.py -m requires_live_project -q
```

**Environment:** Cloud agent pod (Linux); no FieldWorks / SIL.LCModel.

**run_mode:** not executed (collection error: `ModuleNotFoundError: No module named 'SIL'`)

**Pre/post LCM readback:** N/A

**Result:** **FAIL: unverified** -- live LCM gate could not run in this environment.

**Offline gate (same worktree):**

```bash
python3 -m pytest tests/operations/test_issue506_findbyhvo_resolver_offline.py -m "not requires_live_project" -q --noconftest
```

See commit message / CI for pass line.
