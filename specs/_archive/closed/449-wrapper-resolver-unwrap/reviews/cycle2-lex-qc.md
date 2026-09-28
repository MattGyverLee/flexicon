# QC Report -- Issue #449 cycle 2

Source: lex-qc agent (read-only review of `git diff origin/main...HEAD`), saved by the main session.

Score: 94/100
Recommendation: APPROVE

Pattern-Audit Gate: N/A -- this bugfix IS the horizontal sweep (cycle1-sweep.md enumerates every wrapper-returning GetAll and every resolver reachable from it). Satisfied by construction.

Live-LCM Evidence Gate: PASS. evidence/live-T6.md (read-only roundtrip, run_mode=live, per-ClassName counts read back) and evidence/live-write-paths.md (10 write-path cases with pre/post state re-queried from LCM, 1 documented xfail). Both cite FLEXLIBS_REQUIRE_LIVE=1 and tests/live_status.json == "live".

- (a) `_UnwrapLcm` (BaseOperations.py:1688-1737): isinstance-only against LCMObjectWrapper/PythonicWrapper, no hasattr probing of raw pythonnet objects; int/str/None/raw pass through. `PythonicWrapper.unwrap()` (PythonicWrapper.py:220-236) isinstance-gated, uses object.__getattribute__. Never raises.
- (b) Sweep coverage confirmed: BaseOperations _GetObject/MoveUp/MoveDown/MoveToIndex/MoveBefore/MoveAfter/Swap/_FindCommonSequence (833, 931, 1018, 1098-99, 1177-78, 1256-57, 3157-58); AllomorphOperations.py:1598; MSAOperations.py:669 and 1351; MorphRuleOperations.py:1145; PhonologicalRuleOperations.py:1436; WfiMorphBundleOperations.py:1574, 1591; LexSenseOperations.py:1670. No missed resolver among the 4 wrapper-returning classes. POSOperations needs no change.
- (c) Reorder methods unwrap both operands where two are taken.
- (d) Never-raising resolver contracts preserved.
- (e) CLAUDE.md style OK: headers present, writeEnabled/transaction blocks untouched, no new flexlibs2 references, no emojis.
- (f) Docstrings accurate, including corrected GetAll Returns lines; docs/API_ISSUES_CATEGORIZED.md Category 13 (1019-1059) clear with before/after example and documents the MorphRule bare-owner follow-on.
- (g) Offline tests use realistic fakes (ClassName + Hvo) with cast recorders; 21/23 fail on unmodified main. Live write-path test re-queries state after each write.
- (h) Commits b8e4b92, bb95a1a, af45c41, 60489a8, 7af88db: no close/fix/resolve directly before "#449".

## P1
- STATUS.md:16-18 flags the unresolved off-by-one in the offline suite delta (168F/2089P main vs 148F/2109P branch vs 21 new-file tests failing on main). Needs a one-line reconciliation before merge; not a blocker.

## P2
- None affecting correctness or scope. The two MorphRule bare-owner bugs are triaged out of scope with a paper trail.

No P0 issues.
