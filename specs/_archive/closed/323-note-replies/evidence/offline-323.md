# Issue #323 -- offline evidence

## Commands

```
python3 -m pytest tests/operations/test_issue323_note_replies_offline.py -m "not requires_live_project" -q
```

## Result (cloud agent, Linux, 2026-09-23)

See pytest output in CI / local run.

## Behaviour

| Path | Before | After |
|------|--------|-------|
| `GetReplies` / `AddReply` / deep `Duplicate` | `hasattr(..., "RepliesOS")` always false on `ICmBaseAnnotation` -- silent empty / orphan replies | `ResponsesOS` for scripture; `BeginObjectRA` + `AnnotationsOC` for general notes |
| `annotation.replies` | Always `[]` | Same discovery as `GetReplies` |

**Pass/fail:** PASS offline. Live LCM not available in cloud agent (`No module named 'clr'`).
