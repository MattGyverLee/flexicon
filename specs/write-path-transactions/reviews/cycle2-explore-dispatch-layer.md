# Cycle 2 explore: central bracket at the @OperationsMethod dispatch layer

**Cycle:** 2
**Date:** 2026-08-14

> Persistence note: the Explore agent is read-only and could not write this file. It also
> ran concurrently with the verification agent's `git stash -u` / `git stash pop` cycle,
> during which the untracked `specs/` tree and the Track A edits were transiently absent
> from disk. The agent detected the drift and corrected bucket (d) line numbers to
> post-restore values, but **line references into Track-A-modified files
> (`FLExProject.py`, `BaseOperations.py`, `transaction.py`) may be of mixed provenance
> and should be re-checked before being acted on.** Counts and structural conclusions are
> unaffected.

## P1 COVERAGE

Method: AST re-parse of all 111 `.py` under `flexicon/code/`, matching each of the 294
rows to its `def` node and decorator list, plus a name-based caller fixed-point for
transitive coverage. Buckets are mutually exclusive; (e) claims its files first.

| Bucket | Count |
|---|---|
| (a) public, carries `@OperationsMethod` | **235** |
| (b) private helper, all callers transitively decorated | **32** |
| (c) private helper reachable from outside any decorated method | **8** |
| (d) `FLExProject` methods (not a `BaseOperations` subclass) | **6** |
| (e) generic base-class helpers | **13** |
| total | 294 |

Bucket (e) breakdown: `BaseOperations.py` 7 (`Sort`:516, `MoveUp`:613, `MoveDown`:709,
`MoveToIndex`:806, `MoveBefore`:891, `MoveAfter`:966, `Swap`:1042 — all decorated, so
mechanically covered, but the *label* belongs to the subclass);
`Lists/possibility_item_base.py` 3 (206/336/380, decorated);
`Shared/catalog_backed.py` 3 (undecorated — see (c)).

**Bucket (c), all 8** — the SIL-catalog import chain. Every caller is undecorated:
`CatalogBackedMixin._create_from_entry` (`Shared/catalog_backed.py:457`) and
`_handle_entry_children` (`Grammar/InflectionFeatureOperations.py:1473`,
`Grammar/PhonFeatureOperations.py:929`, `Grammar/POSOperations.py:1079`).

- `Grammar/InflectionFeatureOperations.py:1416` `_factory_create_attached`
- `Grammar/InflectionFeatureOperations.py:1433` `_path_b_attach`
- `Grammar/InflectionFeatureOperations.py:1512` `_CreateValueFromEntry`
- `Grammar/POSOperations.py:1016` `_factory_create_attached`
- `Grammar/POSOperations.py:1037` `_path_b_attach`
- `Grammar/PhonFeatureOperations.py:880` `_factory_create_attached`
- `Grammar/PhonFeatureOperations.py:897` `_path_b_attach`
- `Grammar/PhonFeatureOperations.py:968` `_CreateValueFromEntry`

Root cause: `CatalogBackedMixin` is a plain mixin (`Shared/catalog_backed.py:54`, no
`BaseOperations` base). `ImportCatalog`:195, `CreateFromCatalog`:293,
`FixGuidsAgainstCatalog`:362 are all **undecorated**, and the comment at `:190-193`
explicitly delegates decoration to subclasses. Only `ImportCatalog` is actually
overridden-with-decorator (`Grammar/PhonemeOperations.py:1659`,
`Lexicon/SemanticDomainOperations.py:1148`, `Notebook/AnthropologyOperations.py:1817`).
`CreateFromCatalog` and `FixGuidsAgainstCatalog` are public and decorated **nowhere** — a
permanent hole in any dispatch-layer scheme.

**Bucket (d), all 6** (post-restore line numbers): `FLExProject.py:3465`
`LexiconSetFieldText`, `:3509` `LexiconClearField`, `:3682` `LexiconSetListFieldMultiple`,
`:4023` `LexiconDeleteObject`, `:4290` `LexiconSetComplexFormType`, `:4311`
`LexiconAddComplexForm`. `class FLExProject(object)` at `FLExProject.py:122`; the file
contains **zero** `_TransactionCM` references.

Residual per-site job under a central bracket: **8 + 6 + 3 = 17 methods minimum**
(bucket c + d + the three undecorated `catalog_backed` entries), plus 13 in (e) if label
fidelity matters.

## P2 DECORATOR MECHANICS

**Can `__get__` return a wrapping closure?** Yes. The class-level path *already* returns
a closure, not `func.__get__` — `BaseOperations.py:308-313` builds
`class_method(project, ...)` which instantiates `objtype(project)` then calls
`func(instance, ...)`. Only the instance path (`:316`) returns a bare bound method.
Wrapping both is structurally safe. Caveat: `__name__`/`__doc__` are copied onto the
descriptor at `:284-285` but **not** onto the returned closures, so introspection is
already lossy; adding a layer does not regress it but does not fix it either.

**Order.** Exactly two orders exist codebase-wide: `('OperationsMethod',)` x1144 and
`('wrap_enumerable', 'OperationsMethod')` x80. `wrap_enumerable` is *always* the outer
one. Its `wrapped_method` (`BaseOperations.py:236-240`) calls `inner_method(...)` and only
then constructs `EnumerableWrapper`. So a UoW opened inside `OperationsMethod.__get__`
**closes before** the wrapper is built. That is fine today — overlap between the 80
`wrap_enumerable` methods and the 294 mutators is **0** — but it is an unenforced
invariant.

**Generators.** 48 methods carry `@OperationsMethod` and contain a top-level `yield`,
e.g. `Grammar/POSOperations.py:101` `GetAll`,
`Grammar/InflectionFeatureOperations.py:152` `InflectionClassGetAll`,
`Lists/TranslationTypeOperations.py:478` `FindByWS`,
`System/AnnotationDefOperations.py:907` `FindByType`,
`Shared/MediaOperations.py:1616` `GetOrphanedMedia`. All are read-side. For any of these,
a `with` in the dispatch closure would enter, receive the generator object, and exit
before a single frame ran — the UoW would be empty and the mutations (if ever added)
unbracketed. With `mutating=True` gating this is latent, not live; it becomes live the
day someone writes a `yield`-based writer.

**Re-entrancy** — 71 cross-class call sites sit inside decorated methods. Three real
ones, all decorated -> decorated, all mutating:

- `Lexicon/LexSenseOperations.py:1439` `SetPartOfSpeech` -> `self.project.MSA.CreateInflAff`
  (`Lexicon/MSAOperations.py:243`)
- `Lexicon/ExampleOperations.py:1215` `AddMediaFile` -> `self.project.Media.CopyToProject`
  (`Shared/MediaOperations.py:1280`)
- `TextsWords/ParagraphOperations.py:342` `Duplicate` -> `self.project.Segments.AppendSentence`
  (`TextsWords/SegmentOperations.py:544`)

Nesting is already solved: `_NestingAwareTransaction.__enter__` (`transaction.py:48-69`)
reads `project._transaction_depth` and no-ops when depth > 0. Join-or-open is not new
work.

## P3 VALIDATION ORDERING

Docstring instruction: `BaseOperations.py:1784-1787` — "call validation helpers ... BEFORE
entering this context, so input errors never mark the undo stack."

Sampled 12 across 12 domains, comparing last `_EnsureWriteEnabled`/`_Validate*` line to
first mutation line: **12/12 validate-then-mutate**, zero interleave.
`Lexicon/LexEntryOperations.py:934` `SetLexemeForm` (validators 967-972, first mutation
981); `Lexicon/LexSenseOperations.py:1533` (1564/1567); `Grammar/POSOperations.py:241`
(270/277); `Grammar/PhonemeOperations.py:820` (863/872);
`Notebook/DataNotebookOperations.py:1852` (1892/1898);
`TextsWords/WfiMorphBundleOperations.py:730` (766/771);
`Discourse/ConstChartWordGroupOperations.py:442` (471/475);
`Reversal/ReversalIndexEntryOperations.py:454` (483/489); `Shared/MediaOperations.py:952`
(987/1002); `System/CheckOperations.py:232` (269/278); `Lexicon/ExampleOperations.py:1226`
(1268/1280); `Lists/PossibilityListOperations.py:538` (573/582). Six more checked for
`raise` after first mutation (`Grammar/NaturalClassOperations.py:643`,
`Lexicon/LexReferenceOperations.py:873`, `Lexicon/MSAOperations.py:426`,
`Grammar/PhonemeOperations.py:1440`, `Notebook/DataNotebookOperations.py:2431`,
`Shared/MediaOperations.py:186`): **zero**.

**Consequence, plainly:** the codebase is uniformly validate-then-mutate, which is exactly
the discipline a central bracket destroys. Under a dispatch-layer UoW, every
`_ValidateParam` failure and every read-only rejection opens an undo task, raises, and
closes it — in Phase 2 that is an empty named entry pushed onto the user's Ctrl+Z stack
for a call that changed nothing. 100% of the sample regresses. This is the single
strongest technical objection, and it is not fixable at the dispatch layer without moving
validators out of the method bodies.

## P4 LABELS

A dispatch-layer bracket sees `func.__name__`, `objtype.__name__`, and `*args`/`**kwargs`.
Method-qualified labels (`"LexEntryOperations.SetLexemeForm"`) are free. Argument-derived
labels are *possible* but only by blind `repr` of positional args — no parameter-name
mapping without `inspect.signature`, and no way to know which arg is the human-meaningful
one. Realistically: method name only.

Existing call sites: **174** `_TransactionCM(...)` invocations; **50 (29%)** use
argument-derived f-string labels. Examples: `BaseOperations.py:1804`
`f"Create entry '{form}'"`, `Grammar/PhonologicalRuleOperations.py:214`
`f"Create phonological rule {name!r}"`, `Discourse/ConstChartRowOperations.py:506`
`f"Move row to index {index}"`, `Grammar/MorphRuleOperations.py:794`
`f"Duplicate {class_name}"`, `Grammar/POSOperations.py:616`
`f"Add subcategory '{name}'"`. Those 50 lose fidelity under a purely central scheme — the
FLEx undo menu degrades from "Create entry 'famba'" to "LexEntryOperations.Create".

## Verdict: central vs per-site

A central bracket is **cheap and high-coverage but wrong-shaped**: it mechanically covers
267 of 294 (91%) and leaves a residual of 17 must-do sites, the nesting machinery already
exists, and the descriptor can host a closure without breaking the class-level path. But
it buys coverage at the cost of the two things the design already got right — validators
land inside the UoW (100% of sampled methods regress, every rejected input marking the
undo stack), and 29% of call sites lose argument-derived labels that a linguist actually
reads in the Ctrl+Z menu.

Recommendation: a **hybrid** — use the dispatch layer as a safety net (`mutating=True`
opening a UoW only if `_transaction_depth == 0` at the point of first mutation, not at
call entry), while bracketing the ~50 label-bearing and all 17 uncovered sites by hand.

**Strongest argument against my own conclusion:** the hybrid is strictly more machinery
than either pure option and depends on a first-mutation hook that does not exist in
liblcm today; if that hook proves unreachable — as `Transaction`'s rollback API already
did (`BaseOperations.py:1811-1818`, issue #236) — the hybrid collapses into "central
bracket plus 50 hand edits", at which point bracketing all 294 individually is more
honest, fully auditable by grep, and preserves label fidelity everywhere.
