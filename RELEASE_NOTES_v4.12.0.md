# pyflexicon 4.12.0

**Released 2026-10-02** | `pip install --upgrade pyflexicon`

Writing-system changes now reach the store, possibility-list and
semantic-domain names stop resolving through the default analysis WS, an
opt-in peer schema guard protects a FieldWorks that holds the project open,
and a run of morphology wrappers lands. **No breaking changes**; no
signature was removed and no default a caller passes explicitly changed
meaning.

---

## The headline: writing-system changes reach the store

- **`WritingSystems.Delete`** now removes the writing system from the store
  (#607): the `.ldml` moves to `trash/` and `idchangelog.xml` records the
  delete, as in FieldWorks. Like FieldWorks, this also purges data stored in
  that writing system.
- **`WritingSystems.Create` / `Ensure`** now save the store immediately
  (#625), so a crash no longer loses the `.ldml` and a second process can see
  the new writing system. `Ensure` on an already-active tag is still a no-op.
- **Change-log entries are attributed to flexicon** (#608, #626):
  `Producer="flexicon"` instead of `"???"`, including for projects a host
  such as FlexTools hands over already open.
- **Peer schema guard** (`FLExProject.SetPeerSchemaGuard`, capability
  `"peer-schema-guard"`): with the guard on, the writing-system mutators
  raise `FP_ExclusiveAccessRequiredError` before writing, because such writes
  from a shared-mode peer crash the holding FieldWorks. Off by default.

---

## Names no longer resolve through the default analysis WS

`SemanticDomainOperations` (#604) and the possibility-list family
(`PossibilityListOperations`, the Publications / TranslationTypes / Agents
base, Anthropology, Location, Person; #624) now return the best analysis
alternative when no `wsHandle` is given, and `Find*` matches every current
analysis writing system. An explicit `wsHandle` is honoured exactly. Setters
are unchanged.

---

## Also fixed

- Wrong-type arguments to Operations resolvers raise `FP_ParameterError`
  instead of a raw `AttributeError` (#600, #618).
- `GetAll(recursive=False)` on semantic domains, anthropology and location
  returns only top-level items (#603).
- `ReversalIndexOperations.Create` stores the language tag (#619) and
  rejects non-analysis writing systems (#605).
- Variant `Duplicate(insert_after=True)` indexes by HVO (#597).
- `LexiconSetListFieldSingle` accepts every `CmPossibility` subclass (#448).

---

## Added

- **Phonological rules describe themselves** (#572):
  `GetLeftContext` / `GetRightContext` / `GetInputPOSes` /
  `GetRequiredRuleFeatures` / `GetExcludedRuleFeatures` / `IsDisabled` /
  `SetDisabled` / `DescribeRule`; `PhonologicalContext` reads real names,
  descriptions and boundary/iteration/sequence members.
- **Morphology wrappers**: MSA inflection class, exception features,
  long name and type (#573-#575); allomorph inflection classes, required
  features and stem names (#580, #581); POS stem names; inflectable-feature
  and PhonFeature description readers (#577, #578);
  `LexEntryOperations.GetMorphTypeName` (#583).
- **`WordformOperations.GetParserCount` / `GetUserCount` / `IsParsed`**
  (#576) and **`WfiAnalysisOperations` human-evaluation removal** (#582).

`CHANGELOG.md`, section `[4.12.0]`, has every entry.

---

## Upgrade notes

None required. Two narrowings worth knowing: `ReversalIndexOperations.Create`
now raises `FP_ParameterError` for a non-analysis writing system (it never
validated before), and code that caught `AttributeError` from a wrong-type
resolver argument should catch `FP_ParameterError`.

---

## Known issues

Carried over from 4.10.0; neither is a regression.

- **`InflectionFeatures.InflectionClassCreate`** fails on every call: it adds
  the class to the production-restrictions list rather than to a part of
  speech. Create inflection classes on `IPartOfSpeech.InflectionClassesOC`.
- **`ScrNotes.Create`** fails on every call: it stores notes under
  `book.FootnotesOS` rather than `Scripture.BookAnnotationsOS`.

---

## Verification

| Gate | Result |
|---|---|
| Offline suite (`-m "not requires_live_project"`) | **3626 passed** |
| Live suite (`-m requires_live_project`, `FLEXLIBS_REQUIRE_LIVE=1`) | **1099 passed**, 41 skipped, 2 xfailed; `run_mode: live` |

Evidence: `specs/release-4.12.0/evidence/live-release-gate.md`.
