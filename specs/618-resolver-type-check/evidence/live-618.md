# Live verification: #618 resolver wrong-type check

Date: 2026-10-02
Worktree/branch: p2-618 / fix/618-resolver-type-check
Fixtures: sena3_sandbox (read-side resolvers on real data), target_sandbox
(write round-trip). Both are tempdir copies of the .fwbackup fixtures, so no
real project was touched.

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue618_resolver_type_check_live.py -m requires_live_project -q -s
```

## run_mode

`tests/live_status.json` -> `"run_mode": "live"` (run_timestamp 2026-10-02T16:09:56Z).

## Pre/post values read back from the LCM

Output lines (`[EVIDENCE]` lines are printed by the test after re-querying the
LCM object; none is an echo of the value passed in):

```
[EVIDENCE] entry hvo=15 headword(obj)='cibubu' headword(hvo)='cibubu'
.....[EVIDENCE] _GetObject(hvo=4257) -> Hvo=4257 ClassName=LexSense
[EVIDENCE] _GetObject('not-an-object') -> FP_ParameterError: Expected an LCM object or an int HVO, got str.
[EVIDENCE] _GetObject(['a', 'list']) -> FP_ParameterError: Expected an LCM object or an int HVO, got list.
[EVIDENCE] _GetObject(1.5) -> FP_ParameterError: Expected an LCM object or an int HVO, got float.
.[EVIDENCE] chart hvo=10442 PRE name='TEST_618 chart'
[EVIDENCE] after rejected str arg: name='TEST_618 chart' (unchanged)
[EVIDENCE] POST (re-read via object) name='TEST_618 by hvo'
```

Reading the chart lines: PRE name `'TEST_618 chart'` read back from the new
chart; a `SetName("not-a-chart", ...)` call raised `FP_ParameterError` and the
re-read name was unchanged (no mutation from a rejected wrong-type argument);
then SetName by object and by HVO both wrote through and the final re-read
via the object returned `'TEST_618 by hvo'`. The chart and row were deleted in
`finally:`.

Resolvers exercised live (real objects, HVOs, wrapper, and str/list/float):
BaseOperations._GetObject, LexEntryOperations.__ResolveObject (via
GetHeadword), LexSenseOperations.__GetSenseObject (via GetGloss),
TextOperations.__GetTextObject (via GetName), POSOperations.__ResolveObject
(via GetName), WfiAnalysisOperations.__GetWordformObject/__GetAnalysisObject,
ConstChartOperations.__ResolveObject, ConstChartRowOperations.__ResolveChart /
__ResolveObject.

## Regression run of existing sandbox-only live tests (same worktree)

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_352_discourse_live.py ... test_569_create_parent_sweep_live.py test_260_env_resolver_hvo_gate.py test_260_environment_resolver_gate.py -m requires_live_project -q
76 passed in 54.01s
```

## Result

PASS: 7 passed (live), run_mode=live
Offline: `python -m pytest -m "not requires_live_project" -q` -> 3584 passed, 1123 deselected
