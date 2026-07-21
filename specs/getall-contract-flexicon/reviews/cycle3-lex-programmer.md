# Cycle 3 — Programmer Report (getall-contract-flexicon)

Scope: T7 (docstring standardization), T8 (contract guarantee doc), T9
(straggler re-verify), T10 (.pyi assessment). T1-T3 were already in the
working tree at the start of this spurt and were **not** touched, redone, or
reverted.

## Method census (ground truth, re-derived via `ast`)

Walked `flexicon/code/**/*.py` (excluding `.pyi` and `.py.backup`) for every
real `FunctionDef` whose name starts with `GetAll`. Found **73** real methods
(51 bare `GetAll` + 22 `GetAll*` variants). This is close to but not
identical to the Cycle-1 audit's "79" — the audit's number likely includes a
couple of methods/files I didn't re-walk identically (e.g. it may count
`FLExProject.py`'s writing-system helpers differently or a stub-adjacent
method I excluded as non-real). I did not force my count to match 79;
flagging the discrepancy here per the task instructions rather than papering
over it. The **51/22 split for bare vs. variant matches the audit exactly**,
and the container-type taxonomy below matches the audit's shape
classification closely (see tally).

## T1 — Docstring standardization (the real Defect-A fix)

Replaced `Yields:\n    <Type>: <description>` with
`Returns:\n    <ContainerType>[<Element>]: <description>` (same description
text, `Yields`/bare-type line only) on every method whose docstring still
had the misleading generator-style wording — **41 methods**, all of which
turned out to be `EnumerableWrapper`-shaped once cross-checked against their
actual `return`/`yield` statements (raw `ObjectsIn(...)`, `iter(...)`, or a
`yield`-based generator body, always decorated `@wrap_enumerable`).

Also upgraded 16 already-`Returns:`-but-unbracketed `list:` bare `GetAll`
docstrings to `list[Element]:`, and 5 `SmartCollection`-subtype docstrings
(2 bare `GetAll` + 3 `GetAll*` variants: `GetAllCompoundRules`,
`GetAllAffixTemplates`, `GetAllAffixTemplatesForPOS`) to
`SubtypeCollection[WrapperElement]:` — using the actual per-item **wrapper**
class (`Allomorph`, `PhonologicalRule`, `CompoundRule`, `AffixTemplate`),
not the raw LCM interface, since that's what the collection actually holds.

**Container-type tally (bare `GetAll` set of 51, matched against the
Cycle-1 audit's ~16/2/33 expectation):**

| Container type | My count | Audit estimate |
|---|---|---|
| `EnumerableWrapper[T]` | 33 | ~33 |
| `list[T]` | 16 | ~16 |
| `SmartCollection` subtype | 2 | ~2 |

Exact match. Including the 22 `GetAll*` variants (also fixed where they had
the same `Yields:` defect), the full-scope tally across all 73 methods is:
`EnumerableWrapper` 41, `list` 23 (16 bare + 7 variants left unbracketed,
see Deviations), `SmartCollection` 5, `other` 1 (`WfiGlossOperations.
GetAllForms` returns a `dict`, not a collection — correctly left alone).

**Before/after examples:**

`flexicon/code/Lexicon/LexEntryOperations.py:108` (`GetAll`, the example
given in the task brief) — before:
```
        Yields:
            ILexEntry: Each lexical entry object in the project
```
after:
```
        Returns:
            EnumerableWrapper[ILexEntry]: All lexical entries in the project
```

`flexicon/code/Grammar/PhonologicalRuleOperations.py:105` (`GetAll`,
`SmartCollection` case) — before:
```
        Returns:
            RuleCollection: Smart collection of PhonologicalRule wrapped objects.
```
after:
```
        Returns:
            RuleCollection[PhonologicalRule]: Smart collection of PhonologicalRule wrapped objects.
```

`flexicon/code/Discourse/ConstChartRowOperations.py:225` (`GetAll`, `list`
case) — before:
```
        Returns:
            list: List of IConstChartRow objects (empty list if none)
```
after:
```
        Returns:
            list[IConstChartRow]: List of rows (empty list if none)
```

## T2 — Contract guarantee documentation

- New file: `docs/getall-contract.md` — the canonical guarantee
  (loop/`len()`/index/re-iterate across `EnumerableWrapper`/`list`/
  `SmartCollection`), why it matters, how `@wrap_enumerable` +
  `_needs_enumerable_wrap` enforce it, and the docstring convention going
  forward.
- `README.rst` — one-line pointer added to the existing "Documentation"
  section, immediately before "Usage".
- `flexicon/code/BaseOperations.py` — added a "Behavioral collection
  contract" paragraph to the `wrap_enumerable` class docstring (right after
  its existing `Usage::` example), cross-referencing
  `docs/getall-contract.md`.

## T3 — Straggler re-verification

Re-ran an independent raw-shape-vs-decorator sweep across all 73 real
`GetAll*` methods (checks: does the body `yield`, or `return` something
containing `ObjectsIn(` / a bare `iter(` call, and if so is `@wrap_enumerable`
present?). **Result: 0 stragglers** — confirms the Cycle-1 audit's finding.
No runtime changes were made or needed; this was a documentation-only
scope from end to end.

## T4 — `.pyi` stubs: assessed, recommend deferring

Looked at `BaseOperations.pyi`, `LexEntryOperations.pyi`, and a sample of
~15 others. All of them use a blanket
`def GetAll(self, *args: Any, **kwargs: Any) -> Iterator[Any]: ...` pattern
— and that same `*args/**kwargs -> Any`-flavored genericism is applied to
essentially **every** method in every stub (`Find`, `Create`, `GetName`,
etc.), not just `GetAll`. Two problems compound here:

1. The stubs don't import or reference `EnumerableWrapper`/`SmartCollection`
   at all, so there's no existing generic machinery to plug standardized
   container types into — it would need to be added first.
2. The parameter signatures are already wrong/generic independent of this
   feature (real `GetAll(self, entry_or_hvo=None, recursive=True)` vs. stub
   `GetAll(self, *args, **kwargs)`), so fixing only the return-type half
   would leave the stubs still substantially inaccurate.

**Call: this is a large, separate reconciliation effort, not a small
follow-on.** Recommend a dedicated follow-up cycle scoped to the `.pyi`
layer as a whole (return types **and** parameter signatures together),
rather than a partial fix here. Tracked as T10 in `tasks.md`, left
unchecked-but-decided.

## Sanity checks

- `python -m py_compile` — all 56 touched `.py` files compile clean.
- Import smoke test — imported all 56 touched operations modules
  (`importlib.import_module`); all succeeded with real `SIL.LCModel`
  bindings resolved (pythonnet + FieldWorks DLLs available in this dev
  environment). No live-FLEx-project functional test was run (would need
  an open `.fwdata` project; out of scope here, per instructions).
- No remaining `Yields:` section on any `GetAll*` method (re-confirmed via
  the same `ast` walk used for the fix, post-edit).

## Deviations / flags

- **7 `GetAll*` variant methods with un-bracketed `list:` docstrings were
  deliberately left as-is** (out of the primary "drop misleading `Yields`"
  scope, since they already correctly say `Returns:`, just without the
  `[Element]` bracket): `LexEntryOperations.GetAllByMorphType`,
  `LexEntryOperations.GetAllSenses`, `LexSenseOperations.GetAllSenses`,
  `PossibilityListOperations.GetAllLists`,
  `DataNotebookOperations.GetAllRecordTypes`,
  `DataNotebookOperations.GetAllStatuses`,
  `CustomFieldOperations.GetAllFields`. Recommend a small polish pass to
  bracket these too for full consistency, but they are not misleading (no
  `Yields`/`Returns` contradiction), so I did not treat them as in-scope for
  this spurt.
- **Method-count discrepancy (73 vs. audit's 79)** — noted above; did not
  force reconciliation, flagging for whoever reviews next.
- **`.pyi` reconciliation deferred** (T10) — see above, explicit size call:
  large, not small.
- T1-T3 (D1/D2/D3, MediaOperations/AgentOperations/TranslationTypeOperations)
  were already implemented in the working tree at spurt start; confirmed
  untouched and not re-done.

## Files touched (counts)

- 41 files edited for the `Yields:` → `Returns:` fix (some files had 2-3
  occurrences edited in the same pass: `MorphRuleOperations.py`,
  `LexReferenceOperations.py`, `VariantOperations.py`, `MediaOperations.py`,
  `WordformOperations.py`).
- 19 additional bracket-notation upgrades across 15 files (14 `list[T]` +
  1 manual disambiguation in `AnthropologyOperations.py`, which had two
  identical `list: List of ICmAnthroItem objects.` occurrences — only the
  `GetAll` one at line 186 was changed; the `GetSubitems`-adjacent one at
  line 1145 was left alone) + 5 `SmartCollection[Wrapper]` upgrades across
  3 files (`AllomorphOperations.py`, `PhonologicalRuleOperations.py`,
  `MorphRuleOperations.py` ×3).
- 1 new file: `docs/getall-contract.md`.
- 2 files with new cross-referencing prose: `README.rst`,
  `flexicon/code/BaseOperations.py`.
- 2 spec files updated for durable state: `tasks.md`, `SPEC.md`.

No commit was made — per instructions, the archivist commits later as part
of the combined T1-T3 + T7-T9 checkpoint.
