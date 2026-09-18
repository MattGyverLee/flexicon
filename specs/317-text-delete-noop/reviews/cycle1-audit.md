# Cycle 1 audit -- #317 pattern sweep verification

Source used for LCM interface shapes: no local `C:/Github/liblcm` clone on
this machine, so `C:/Github/FlexToolsMCP/src/flextoolsmcp/index/liblcm/liblcm_api_v11.0.0.json`
was used throughout.

## Verdict: OVERSTATED

The `.Remove(` half is essentially correct: 31 real (non-comment) `.Remove(`
sites, all target ownership-suffixed collections (`...OS/...OC/...RC/...RS`)
or a suffix-filtered dynamic loop (`FLExProject.py:5037`, guarded by
`prop_name.endswith("OS"/"OC")`). No unsuffixed `.Remove(` target remains
(the two `lp.Texts` sites were the fix). One caveat: three `.Remove(` calls
are on `dupe.OwningList`, which is **not** a suffix-guarded collection --
see below, confirmed broken.

The commit's claim that "the bug class does not recur elsewhere" is false
once `.Add`/`.Clear` and the `OwningList` idiom are swept. Three confirmed
bugs and two suspects exist outside `TextOperations.py`.

## Suspect table

| Site | Accessor | Confidence | Note |
|---|---|---|---|
| `Lexicon/LexEntryOperations.py:3138` | `dupe.OwningList.Remove(dupe)` (dupe = `ILexPronunciation`) | **confirmed-bug** | `OwningList` exists only on `CmPossibility`/`ICmPossibility` in LCM 11 (verified via reflection). `ILexPronunciation` has no such property -> `AttributeError` every call, swallowed by the surrounding broad `except Exception: logger.warning(...)`. Pronunciation dedup never runs. Fix: `entry.PronunciationsOS.Remove(dupe)`. |
| `Lexicon/LexEntryOperations.py:3209` | `dupe.OwningList.Remove(dupe)` (dupe = `IMoAffixAllomorph`/`IMoStemAllomorph`, from `entry.AlternateFormsOS`) | **confirmed-bug** | Same shape; neither allomorph interface has `OwningList` in the reflection index. Allomorph dedup never runs. Fix: `entry.AlternateFormsOS.Remove(dupe)`. |
| `Lexicon/LexSenseOperations.py:3885` | `dupe.OwningList.Remove(dupe)` (dupe = `ILexExampleSentence`, from `sense.ExamplesOS`) | **confirmed-bug** | Same shape; `ILexExampleSentence` has no `OwningList`. Example dedup never runs. Fix: `sense.ExamplesOS.Remove(dupe)`. |
| `Lists/OverlayOperations.py:283-391` (`GetElements`/`AddElement`/`RemoveElement`) | `overlay.InstancesOS` / `overlay.Elements` | **confirmed-bug** | Neither `InstancesOS` nor `Elements` exists on `ICmOverlay`/`CmOverlay` in the reflection index; the file's own later method (`GetPossItems`, line ~468) already documents -- citing issue #277's live reflection -- that `ICmOverlay`'s complete surface is `Name`/`PossItemsRC`/`PossListRA`. Both `hasattr` branches are always false, so these three methods are unconditional no-ops (mirrors #277, not yet applied to this trio). Fix: add a `PossItemsRC` branch using `.Add`/`.Remove` on the RC. |
| `Notebook/DataNotebookOperations.py:1297/1351/1391/1438/1488/1528` | `record.Researchers` / `record.Participants` | **confirmed-bug** | Reflection shows only `ResearchersRC` (on `IRnGenericRec`) and `ParticipantsRC` (on `IRnRoledPartic`) exist in LCM 11 -- no unsuffixed `Researchers`/`Participants`. All `hasattr(record, "Researchers"/"Participants")` guards are false, so `Get/Add/RemoveResearcher` and `Get/Add/RemoveParticipant` are silent no-ops, same user-visible symptom as #317 (reports success, does nothing). No RC-suffixed fallback branch exists anywhere in this block. |
| `System/WritingSystemOperations.py:495-501` | `lp.VernacularWritingSystems`/`AnalysisWritingSystems`/`CurrentVernacularWritingSystems`/`CurrentAnalysisWritingSystems` | suspect | All four report `kind="property"`, `can_write=False` in reflection -- the same red-flag shape as `Texts`. Unlike `Texts`, these back `IWritingSystemContainer`, a different (non-CmObject) persistence path; SIL's own C# code uses the identical remove-from-both-lists idiom, and the accompanying comment cites the documented removal contract, suggesting deliberate, correct use rather than a derived-list accident. Reflection alone can't distinguish "live backing List" from "rebuilt-per-access list" here -- needs a live-instance check (same method used for #277) before ruling out. |
| `lcm_casting.py:791-823` (`clone_properties`) | any `dir(source)` attribute where `hasattr(attr_value,"Count") and hasattr(attr_value,"Add")` | suspect | Generic duplication helper does pure duck-typing, not suffix-checking -- it would treat *any* derived list exposing `.Count`/`.Add` (e.g. a future `Texts`-shaped property) as a mutable owning collection and `Clear()`/`Add()` into a throwaway. Callers today (`EnvironmentOperations`, `PhonemeOperations`, `PhonologicalRuleOperations`) operate on grammar objects whose collections are conventionally suffixed, so no live instance was found broken, but the helper itself reproduces the #317 bug shape structurally and should discriminate by suffix/kind, not duck type. |
| `Lists/AgentOperations.py:204-207`, `Grammar/StratumOperations.py:83-254`, `Grammar/PhonologicalRuleOperations.py:1066-1076`, `FLExProject.py:5029-5037` | `agents_oc` (`AnalyzingAgentsOC`), `__Container()` (`StrataOS`), `contexts_pool` (`ContextsOS`), suffix-filtered `dir()` loop | clean | Variable names are unsuffixed but resolve to real `OC`/`OS` accessors confirmed in reflection; not the bug shape. |

Word count: under 700.
