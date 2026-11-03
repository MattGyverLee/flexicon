# Live evidence -- issue #864

**Command:** `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue864_phon_handle_children_closed_live.py -m requires_live_project -q`

**run_mode:** mock (FieldWorks / pythonnet CLR not available on cloud agent)

**Result:** FAIL: unverified -- live gate module present; offline ratchet PASS.

**Pre/post LCM readback:** not performed (runner cannot open Target).
