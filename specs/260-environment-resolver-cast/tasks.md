# tasks

- [ ] T1: `__GetEnvironmentObject` cast landed + live-gated
  - LCM reflection recorded (evidence/live-T1-reflection.md)
  - RED test committed before the fix (test file + RED evidence)
  - Fix applied, GREEN captured
  - Live verification against target_sandbox (FLEXLIBS_REQUIRE_LIVE=1)
  - Offline regression run, P5 adjudicated
  - IMoForm unused-import ruling (AST/linter-verified, separate commit)
