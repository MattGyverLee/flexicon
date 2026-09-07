# Evidence -- T5 join-boundary fix (AppendSentence terminator branch, P8 follow-up)

**Committed BEFORE running anything** (C28 forward rule, matching
`be42aaf`/`066bab0` from cycle 2). Results are added in a second commit,
after the live run, per the same convention.

## Scope

Only `flexicon/code/TextsWords/SegmentOperations.py`'s `AppendSentence`
`current_length > 0` branch is touched. Per C12: AppendSentence may INSERT
at the join boundary; it may never DELETE at the join boundary. This is a
positioning fix, not a whitespace-policy change -- ZERO characters are
removed in any branch. `rstrip()` is used ONLY to compute an index; the
stripped string is never written and never passed to `MakeString`.

## Predictions

Existing `Contents` (via `Paragraphs.Create`) -> `AppendSentence(para, "bar")`
-> expected re-read of the full paragraph `Contents`:

| Existing Contents | Predicted result | Note |
|---|---|---|
| `''` | `'bar'` | inert -- empty-paragraph branch, untouched |
| `'foo'` | `'foo. bar'` | inert -- trail==0, not terminated |
| `'foo.'` | `'foo. bar'` | inert -- trail==0, already terminated |
| `'foo!'` | `'foo! bar'` | inert -- trail==0, already terminated |
| `'foo '` | `'foo. bar'` | **P8 FIXED**; pre-fix was `'foo . bar'` (space before period) |
| `'foo   '` (3 spaces) | `'foo.   bar'` | all 3 trailing spaces preserved as the separator |
| `'foo.  '` (2 trailing spaces) | `'foo.  bar'` | pre-fix was `'foo.  . bar'` (double terminator) |
| `'foo\t'` | `'foo.\tbar'` | tab preserved as separator |
| `'   '` (whitespace-only Contents) | `'   bar'` | pre-fix was `'   . bar'`; **CANNOT be built through the public API** (whitespace-only input raises `FP_ParameterError`) -- must be built via the same direct-LCM / layer-B path used for P6, or marked UNMEASURED. Will NOT fake this and will NOT relax the raise to enable it. |

## The inertness claim (C12.4)

C12.4 asserts the change is provably inert whenever `trail == 0` -- i.e. on
every input reachable before #242 (since pre-fix, `Create`/`SetText`/
`InsertAt` always stripped trailing whitespace, so `trail` could never be
> 0 on any paragraph built through the public API before this feature
landed). The first four prediction rows above (`''`, `'foo'`, `'foo.'`,
`'foo!'`) are that proof and MUST pass byte-for-byte unchanged from cycle
2's T1/T2 behaviour. If any of them moves, this falsifies the C12 ruling
and requires a re-rule by `/lex-lead` -- STOP and report, do not silently
adjust the prediction.

## Live verification plan

```
$env:FLEXLIBS_REQUIRE_LIVE="1"
python -m pytest tests/operations/test_issue242_whitespace_probe.py -m requires_live_project -q -s
```

`target_sandbox` / `target_sandbox_path` fixtures ONLY. `tests/live_status.json`
must read `"run_mode": "live"`.

`test_p8` is converted in place from a measurement of the pre-fix anomaly
into an assertion of the fixed behaviour (pre-fix string kept in a
comment). New assertions cover every prediction row above, including the
whitespace-only-Contents row via a direct-LCM bypass write to seed the
paragraph (matching the `test_p3`/`test_p4` layer-B pattern already in this
file), NOT through `Paragraphs.Create`.

## Results

(added after the live run, second commit)
