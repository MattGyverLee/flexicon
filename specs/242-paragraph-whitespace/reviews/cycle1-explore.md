# Explore sweep — sibling validate-then-persist sites (Issue #242, cycle 1)

**Persisted by:** main session (Explore has no Write tool).

## Bucket 1 — BUG SHAPE (transform -> validate -> persist the transform)

AST-verified: a param is reassigned through `.strip()`/coercion, then that variable is what reaches `MakeString`/`set_String`/attribute assign.

| site | method | transform line | persist line |
|---|---|---|---|
| `flexicon/code/TextsWords/ParagraphOperations.py:180` | `Create` | 180 | 202 (known #242) |
| `flexicon/code/TextsWords/ParagraphOperations.py:585` | `SetText` | 585 | 593 (known #242) |
| `flexicon/code/TextsWords/ParagraphOperations.py:726` | `InsertAt` | 726 | 753 (known #242) |
| `flexicon/code/TextsWords/SegmentOperations.py:595` | `AppendSentence` | 595 | 624 (known #242) |
| `flexicon/code/System/CheckOperations.py:196` | `CreateCheckType` | 196 | 218 **NEW** |
| `flexicon/code/System/CheckOperations.py:432` | `SetName` | 432 | 439 **NEW** |
| `flexicon/code/TextsWords/TextOperations.py:152` | `Create` | 152 | 170 **NEW** |
| `flexicon/code/TextsWords/TextOperations.py:608` | `SetName` | 608 | 616 **NEW** |
| `flexicon/code/TextsWords/DiscourseOperations.py:327` | `CreateChart` | 327 | 351 **NEW** |
| `flexicon/code/TextsWords/DiscourseOperations.py:482` | `SetChartName` | 482 | 492 **NEW** |
| `flexicon/code/Notebook/AnthropologyOperations.py:265` | `Create` | 265 | 301 **NEW** |
| `flexicon/code/Notebook/AnthropologyOperations.py:374` | `CreateSubitem` | 374 | 391 **NEW** |

Note the issue's line numbers (171/576/716/589) are the `_ValidateParam` lines; the transform is 9-10 lines lower in HEAD.

## Bucket 2 — CORRECT SHAPE (throwaway validation, original persisted)

**COUNT: 82 writer sites.** 71 use the literal `if not x or not x.strip():` / `if not x.strip():` guard then `MakeString(x)`; 11 more delegate the same throwaway check to `BaseOperations._ValidateStringNotEmpty` (`AllomorphOperations.py:299, 681`; `ExampleOperations.py:207`; `LexEntryOperations.py:231, 990, 1860`; `LexSenseOperations.py:228, 1853, 1957`; `PronunciationOperations.py:214`; `LexReferenceOperations.py:261`). Representative confirmations: `POSOperations.py:190->228`, `PhonemeOperations.py:188->218`, `PossibilityListOperations.py:222->234`, `possibility_item_base.py:178->200`, `PhonFeatureOperations.py:313->361`, `ReversalIndexOperations.py:170->195`, `AnnotationDefOperations.py:194->222`, `NoteOperations.py:178->206`, `DataNotebookOperations.py:295->311`.

Counting *all* writers that persist the caller's original unmodified (including those with only a `_ValidateParam` None-check, e.g. `ScrTxtParaOperations.py:153/374`, `WordformOperations.py:176/379`, `SegmentOperations.py:382/449/514`): **390**.

**Verdict: 82 vs 12 — the four #242 sites are outliers. Fix shape = persist the original, validate on a throwaway.**

## Bucket 3 — DELIBERATE

| site | why deliberate |
|---|---|
| `SemanticDomainOperations.py:177` | inside `FindByNumber` — read/compare path, nothing persisted |
| `InflectionFeatureOperations.py:792` | `type_normalized` is a factory **discriminator** (`== "complex"`), never persisted |
| `MediaOperations.py:235, 838, 1345` | filesystem paths/filenames; the stripped value is used for real `os.path` operations, so DB and disk stay consistent (Windows rejects trailing-space names) |
| `TextOperations.py:892` | same: `filepath` feeds `os.path` copy, not a multistring |
| `BaseOperations.py:~366, ~393` (`_apply_syncable_properties_to_item`) | `.strip()` only inside `fill_gaps` emptiness guards; persists `text`/`value` **untouched**. Shared code is CLEAN — no wide blast radius |
| `BaseOperations.py:2536` (`_ValidateStringNotEmpty`) | pure `len(text.strip()) == 0` check, documented "No side effects" |
| `*Operations.py` `target = normalize_match_key(name.strip(), ...)` (9 sites) | compare-only locals |

## Specifically requested checks

- **`normalize_text()`-then-persist: NONE.** All 44 call sites are getters/comparisons (`GetX`, `_NormalizeMultiString`, filter predicates). No `MakeString(normalize_text(...))` or `set_String(..., normalize_text(...))` anywhere.
- **`normalize_match_key()`-then-persist: NONE.** All 80 uses land in a compare-only local (`target`, or inline `==`). No casefold destruction.
- **`str()`-coercion asymmetry — there is a THIRD variant, and it is the worst:** `CheckOperations.py:196/341/432` use `name.strip() if isinstance(name, str) else ""`. Because `_ValidateParam` (`BaseOperations.py:2377`) is a **None-check only**, `""` passes validation — a non-`str` argument is silently coerced to empty and persisted as an empty name.
- **`ScrTxtParaOperations.py`: CLEAN.** `Create:153` and `SetText:374` persist the raw `text` after only `_ValidateParam`. Does not share the bug shape (it also does no emptiness check at all).
- **`WordformOperations.py`: CLEAN.** `176`/`379` persist raw `form`; `246`/`278` are throwaway guards in `Find`/`Exists`.

## Highest-severity NEW sites (ranked by caller data destroyed)

1. `System/CheckOperations.py:196` and `:432` — non-`str` -> `""` -> **empty name persisted, entire payload lost**, no exception.
2. `TextsWords/TextOperations.py:152` / `:608` — text titles silently re-whitespaced; `Create` also dedups against the *stripped* name, so `"Genesis "` collides with `"Genesis"`.
3. `Notebook/AnthropologyOperations.py:265` / `:374` — OCM item names; `Exists()` at 269 uses the stripped form, same silent-collision effect.
4. `TextsWords/DiscourseOperations.py:327` / `:482` — chart names (lower blast radius, metadata only).
