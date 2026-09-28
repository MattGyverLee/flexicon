# Live verification evidence -- issue #275 resolver sweep

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue275_resolver_sweep_live.py -m requires_live_project -q
```

Result: `17 passed in 14.17s`

## run_mode confirmation

`tests/live_status.json` -> `"run_mode": "live"` (line 466 at time of this
run). Real LibLCM, real FieldWorks 9 assemblies (FLExInitialize() completed,
59/59 operations classes loaded per the captured setup log).

## Fixtures used

- `target_sandbox` (tempdir copy of `Target 2026-07-06 0218.fwbackup`) for
  every class except one.
- `sena3_sandbox` (tempdir copy of `Sena 3 2018-09-11 1145.fwbackup`) for
  `ScrBookOperations` only, because the Target scratch project has no
  Scripture module enabled (`ScrBookOperations.Create` raises
  `FP_ParameterError("Project does not have Scripture enabled")` on a blank
  project -- confirmed live, not a resolver defect).

Neither the user's real Target nor real Sena 3 was touched; both fixtures
operate on tempdir copies that are deleted on teardown.

## Per-class pre-state / post-state, read back from the LCM

All values below are the object re-fetched via `project.Object(hvo)` or a
`Get*` accessor call **after** the write, not the value passed in.

| Class | Scenario | Pre-fix behaviour (from source inspection) | Post-fix live result |
|---|---|---|---|
| `EtymologyOperations` (`__GetEntryObject`) | `Etymology.Create(entry.Hvo, ...)` | `isinstance(obj, ILexEntry)` False on `project.Object()`'s ICmObject-declared return -> `FP_ParameterError` | PASS -- etymology created, `GetForm()` round-trips `TEST_275_form2` |
| `EtymologyOperations` (`__GetEtymologyObject`) | `GetForm(etym.Hvo)` and `GetForm(raw_icmobject)` | HVO branch raised `FP_ParameterError`; raw-object branch returned uncast, `.Form` access would raise `AttributeError` | PASS -- both return `TEST_275_form2`, matching |
| `VariantOperations` (`__GetEntryObject`, `__GetVariantObject`) | `Variants.Create(entry.Hvo, form, vtype)`, then `GetForm(ref.Hvo)` / `GetForm(raw)` | Same two defects on both resolvers | PASS -- `TEST_275_varform` round-trips via HVO and raw object |
| `VariantOperations` rejection | `GetForm(entry.Hvo)` where entry is genuinely a `LexEntry`, not a `LexEntryRef` | N/A (old guard rejected everything, valid or not) | PASS -- still raises `FP_ParameterError` (widening did not become permissive) |
| `LocationOperations` | `Location.Create(name)`, `GetName(loc.Hvo)`, `GetName(raw)` | HVO raised; raw object's `.Name` would `AttributeError` | PASS -- both return `TEST_275_Somewhere` |
| `LocationOperations` rejection | `GetName(person.Hvo)` | N/A | PASS -- still raises `FP_ParameterError` |
| `PersonOperations` | `Person.Create(name)`, `GetName(person.Hvo)`, `GetName(raw)` | Same two defects | PASS -- both return `TEST_275_Someone` |
| `StratumOperations` (non-raising resolver) | `Strata.Create(name)`, `GetName(stratum.Hvo)`, `GetName(raw)` | Resolver never raised, but returned bare `ICmObject` on the HVO path -- `.Name` access raised `AttributeError` | PASS -- both return `TEST_275_Stratum` |
| `ReversalIndexOperations` | `ReversalIndexes.Create(name, ws)`, `GetName(index.Hvo)`, `GetName(raw)` | Same two defects | PASS -- both return `TEST_275_Idx` |
| `ReversalIndexEntryOperations` (`__GetIndexObject`, `__ResolveObject`) | `ReversalEntries.Create(index.Hvo, form, wsHandle=en_ws)`, `GetForm(entry.Hvo, wsHandle=en_ws)`, `GetForm(raw, wsHandle=en_ws)` | Same two defects on both resolvers | PASS -- both return `TEST_275_revform` |
| `ReversalIndexEntryOperations` rejection | `GetForm(index.Hvo)` where the HVO is genuinely a `ReversalIndex`, not an entry | N/A | PASS -- still raises `FP_ParameterError` |
| `SemanticDomainOperations` | `SemanticDomains.Create(name, "9.9")`, `GetName(domain.Hvo)`, `GetName(raw)` | Same two defects | PASS -- both return `TEST_275_Domain` |
| `MediaOperations` (11 inline sites) | `Media.Create(path, label)`, `GetInternalPath(media.Hvo)`, `GetInternalPath(raw)` | HVO branch raised on every one of the 11 sites (the int-HVO path was **completely unreachable** for any genuine `ICmFile` before this fix); raw-object branch returned uncast | PASS -- both return `TEST_275_audio.wav` |
| `ConstChartOperations` | `ConstCharts.Create(name)`, `GetName(chart.Hvo)`, `GetName(raw)` | Same two defects | PASS -- both return `TEST_275_Chart` |
| `ConstChartRowOperations` (`__ResolveChart`, `__ResolveObject`) | `ConstChartRows.Create(chart.Hvo, label)`, `GetLabel(row.Hvo)`, `GetLabel(raw)` | Same two defects on both resolvers | PASS -- both return `TEST_275_Row` |
| `ConstChartRowOperations` rejection | `GetLabel(chart.Hvo)` where the HVO is genuinely a chart, not a row | N/A | PASS -- still raises `FP_ParameterError` |
| `ScrBookOperations` | `GetCanonicalNum(book.Hvo)` / `GetCanonicalNum(raw)` against an existing Sena 3 book | Same two defects | PASS -- HVO and raw-object results agree with the object-typed baseline |

## Two unrelated pre-existing defects surfaced incidentally

Neither is a #275 resolver defect; both are noted so they are not
mis-attributed to this fix, and are left unfixed here (out of scope):

1. `ReversalIndexEntryOperations.Create`'s and `.GetForm`'s default
   writing-system inference (`index.WritingSystem` -> `project.WSHandle()`,
   and `__GetEntryWS`) resolves to a value that fails
   `TsStringUtils.MakeString` / `get_String` on this build. Sidestepped in
   the test by passing `wsHandle` explicitly; the resolver itself (which is
   what #275 fixes) was proven working before this was hit.
2. `ScrBookOperations.GetTitle` reads `book.Title`, which does not exist on
   `IScrBook` (`AttributeError: 'IScrBook' object has no attribute
   'Title'. Did you mean: 'TitleOA'?`). Sidestepped by verifying via
   `GetCanonicalNum` instead, which is unaffected.

## Offline regression check

```
python -m pytest -m "not requires_live_project" -q
```

1858 passed, 2 failed (`tests/test_docstring_example_ratchet.py` -- a
pre-existing, unrelated docstring-example baseline check flagging
`PersonOperations.AddLanguage`'s docstring, a method this change did not
touch; present before any #275 edits and consistent with concurrent
in-flight work from other agents in this shared checkout), 774 deselected.

## Process note

One `pytest -k ... ` invocation during this work omitted the required
`-m "not requires_live_project"` filter and inadvertently executed
`tests/operations/test_text_operations.py::TestTextOperationsIntegration::test_create_and_delete_text`,
a live test, against whatever project fixture it defaults to. It failed at
the `Exists()` check before any write occurred (`FP_ParameterError: A text
with the name 'Test Text 123' already exists`), so no mutation happened in
that run; the pre-existing "Test Text 123" object is leftover state from
an earlier/other session, not created by this run. All subsequent test
invocations used the mandated `-m` filter.
