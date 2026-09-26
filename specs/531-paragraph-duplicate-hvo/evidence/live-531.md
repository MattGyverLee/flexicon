# Live evidence -- issue #531

**Command (required gate):**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue531_paragraph_duplicate_hvo_live.py -m requires_live_project -q
```

**run_mode:** mock (cloud agent -- no FieldWorks / clr)

**Result:** FAIL: unverified -- live LCM not available in this environment.

**Expected pre/post (when run on a FieldWorks host):**

- Pre: three-paragraph text; duplicate middle paragraph via `Object(hvo)` with
  `insert_after=True` lands at end of `ParagraphsOS` (bug).
- Post: duplicate HVO appears immediately after source paragraph HVO in
  `GetAll(text)` order.
