# live-T1-reflection.md

## Command

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/test_zzz_260_reflection_scratch.py -m requires_live_project -q -s
```

Throwaway probe file `tests/test_zzz_260_reflection_scratch.py` (deleted
immediately after this evidence was captured; not part of the permanent
suite). Ran against `target_sandbox` (tempdir copy of the Target
`.fwbackup`).

## Raw reflection output (verbatim)

```
[REFLECT] IPhEnvironment clr type = 'SIL.LCModel.IPhEnvironment'
[REFLECT] IPhEnvironment concrete/derived types found: ['SIL.LCModel.DomainImpl.PhEnvironment']
[REFLECT] Real env ClassName = 'PhEnvironment'
[REFLECT] Real env type = <class 'SIL.LCModel.IPhEnvironment'>
[REFLECT] bare.ClassName = 'PhEnvironment'
[REFLECT] hasattr(bare, 'StringRepresentation') = False
[REFLECT] hasattr(bare, 'Name') = False
1 passed, 4 warnings in 3.70s
```

`tests/live_status.json` for this run:

```json
{
  "by_class": {},
  "by_test": {
    "tests/test_zzz_260_reflection_scratch.py::test_reflect_phenvironment_shape": {
      "duration_seconds": 0.106,
      "operations_class": null,
      "phase": null,
      "status": "pass"
    }
  },
  "run_mode": "live",
  "run_timestamp": "2026-09-08T15:26:44Z",
  "uncategorized_live_tests": [
    "tests/test_zzz_260_reflection_scratch.py::test_reflect_phenvironment_shape -- missing live_phase marker"
  ]
}
```

`run_mode: "live"` -- this is a genuine live run, not a mock degradation.

## Interpretation

`clr.GetClrType(IPhEnvironment).Assembly.GetTypes()` filtered by
`IsAssignableFrom` finds **exactly one** implementing type in the whole
`SIL.LCModel` assembly: `SIL.LCModel.DomainImpl.PhEnvironment`. There is
no subtype hierarchy under `IPhEnvironment` the way there is under
`IMoForm` (`MoStemAllomorph` / `MoAffixAllomorph`). A real environment
created via `EnvironmentOperations.Create` reports
`ClassName == "PhEnvironment"`, confirmed both on the returned live
object and on a bare `sandbox.Object(hvo)` re-fetch.

The bare-view trap (P3) holds: `hasattr(bare, "StringRepresentation")`
and `hasattr(bare, "Name")` are both `False` on the uncast `ICmObject`
view, even though `IPhEnvironment` itself declares neither of those two
members as `object`/interface-only casts are required to reach members
declared only on the concrete `PhEnvironment` implementation (mirrors
the T8-style trap already established for `MoAffixAllomorph`/`Form`).

## Adjudication

**P1 HELD.** IPhEnvironment has no concrete LCM subtypes (single
implementing type, `PhEnvironment`), and a real environment reports
`ClassName == "PhEnvironment"`, exactly as predicted.

## Shape chosen

Per the lead's expectation given P1 HELD, and per CLAUDE.md Category 8
(never copy a pattern to a different interface without checking the
target), the correct shape is a GUARDED, NEVER-RAISING single-type
cast merging the int/object branches (mirroring the sibling's
`:1359-1369` int/object merge, but with a ONE-branch `ClassName`
check instead of the sibling's two-branch dance, since there is only
one concrete type to discriminate to):

```python
def __GetEnvironmentObject(self, env_or_hvo):
    if isinstance(env_or_hvo, int):
        obj = self.project.Object(env_or_hvo)
    else:
        obj = env_or_hvo

    class_name = getattr(obj, "ClassName", None)
    if class_name == "PhEnvironment":
        return IPhEnvironment(obj)
    return obj
```

This is NOT the sibling's two-branch dance (nothing to discriminate
between -- there is only one concrete type), and NOT an unconditional
`IPhEnvironment(obj)` (that would newly raise on non-environment inputs
the object branch returns unchanged today, a behavioral regression for
any caller passing something else through this permissive, never-raising
resolver).
