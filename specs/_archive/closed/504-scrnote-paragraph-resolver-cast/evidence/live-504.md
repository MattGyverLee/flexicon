# Live verification -- issue #504

**Command:**

```bash
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue504_scrnote_paragraph_resolver_cast_live.py -m requires_live_project -q
```

**Environment:** Cloud agent pod (Linux); no FieldWorks / SIL.LCModel.

**run_mode:** not executed (collection error: `ModuleNotFoundError: No module named 'SIL'`)

**Pre/post LCM readback:** N/A

**Result:** **FAIL: unverified** -- live LCM gate could not run in this environment.

**Offline gate (same worktree):**

```bash
python3 -m pytest tests/operations/test_issue504_scrnote_paragraph_resolver_cast_offline.py -q --noconftest
```

2 passed.
