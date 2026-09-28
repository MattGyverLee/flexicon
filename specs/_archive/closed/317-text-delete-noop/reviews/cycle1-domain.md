# Domain Expert Review -- flexicon #317 (dbabca6)

> Authored by the cycle-1 lex-domain agent (read-only: Read/Grep/Glob/WebFetch).
> The agent had no Write tool, so the main session committed this body verbatim
> to the path the dispatch specified.

**Date:** 2026-09-18
**Domain:** FieldWorks/LCM lexicon & text automation
**Score:** 92/100
**Status:** PASS-WITH-CONCERNS

**liblcm source unavailable** (C:/Github/liblcm does not exist here). All LCM
claims rest on the LCM 11.0.0 reflection index (`liblcm_api_v11.0.0.json`)
and FieldWorks GUI source (`C:/Github/fieldworks/Src`), cited inline.

## 1. Does Delete() cascade to Contents (IStText/IStTxtPara), or orphan them?

Cascades -- does not orphan. The reflection index shows `IText.ContentsOA`
is `"kind": "OA"`, described as "Single owned object reference (child)"
(liblcm_api_v11.0.0.json:78169 pattern, matching IText's own ContentsOA
entry at the same shape, confirmed via grep of `ContentsOA` occurrences
across text-owning types incl. IText). LCM's owning-reference contract
(OA/OC/OS) guarantees the framework deletes owned descendants when the
owner is deleted -- this is a structural invariant of `ICmObject.Delete()`,
not optional behavior. IStTxtPara paragraphs are themselves owned by
`IStText.ParagraphsOS` (owning sequence), so the cascade is transitive:
Text -> Contents -> Paragraphs -> Segments all get removed in one Delete().
FieldWorks GUI source corroborates the ownership direction directly:
`InterlinearTextsRecordClerk.GetObjectToDelete` walks `currentObject.Owner`
from the StText up to the owning `IText`
(`fieldworks/Src/LexText/Interlinear/InterlinearTextsRecordClerk.cs:71-76`,
comment: "if we can delete an StText at all, we want to delete its owning
Text").

## 2. Inbound references (genre, discourse charts, Notebook, overlays, concordance) -- auto-cleared or dangling/throw?

Auto-cleared, not dangling. The reflection index surfaces
`ILcmClearForDelete.Clear(Boolean forDelete)`
(liblcm_api_v11.0.0.json:76484-76517) implemented by every reference-vector
class: `LcmReferenceCollection` and `LcmReferenceSequence`
(:144670-144680, :144798-144808), which back `ref-collection`/`ref-sequence`
properties (e.g. genre lists, discourse chart word-group references,
concordance/analysis backpointers). This is LCM's documented mechanism for
severing incoming references when their target is deleted -- `Clear(true)`
is invoked on referencing vectors as part of the delete pipeline, which is
why the "genre" (ref-atomic/ref-collection to ICmPossibility) is on the
Text's own outgoing side and doesn't need special handling, while inbound
ref-collections elsewhere (discourse row word groups, notebook cross-refs)
get cleared via this same interface rather than left dangling. I could not
find the DomainDataByFlid delete-pipeline source itself (that logic lives
in liblcm, unavailable here), so I cannot cite the call site that invokes
`Clear(forDelete: true)` -- this is inferred from the interface's existence
and documented purpose, not confirmed against the calling code. Flag this
as the one point resting on architectural inference rather than a direct
citation.

## 3. Does FLEx GUI's own "Delete Text" do the same thing, or extra cleanup?

Same thing -- no extra cleanup layer. `RecordClerk.DeleteRecord`
(`fieldworks/Src/xWorks/RecordClerk.cs:1485-1563`) wraps deletion in
`UndoableUnitOfWorkHelper.Do(...)` around `RecordList.DeleteCurrentObject`,
which calls `VirtualListPublisher.DeleteObj(thingToDelete.Hvo)`
(`RecordList.cs:3790-3820`) -- a generic, object-type-agnostic call that
resolves to `ICmObject.Delete()` on the target. There is no
IText-specific pre-delete cleanup step in xWorks/ITextDll (no
`OnDeleteText`, `DeleteTextBase`, or similar handler exists anywhere under
`fieldworks/Src` -- grepped and found none). The only IText-specific
behavior is `InterlinearTextsRecordClerk.GetObjectToDelete`, which
redirects the delete target from the currently-selected StText up to its
owning IText (:71-76) -- i.e., GUI ensures it deletes the *Text*, not just
its Contents, exactly matching what the fix now does. No divergence found.

## 4. Is `text_obj.Delete()` inside a UOW transaction CM correct, or does LCM Delete() need its own UOW handling?

Correct as written, and matches precedent. `ICmObject.Delete()` mutates
the repository and must run inside an active Unit of Work -- it does not
manage its own UOW. `WordformOperations.Delete()`
(`flexicon/code/TextsWords/WordformOperations.py:216-218`) uses the
identical idiom: `with self._TransactionCM("Delete wordform"):
wordform.Delete()`. `TextOperations.Delete()` now mirrors this exactly
(`TextOperations.py:239-240`). The GUI's own delete path likewise wraps
the generic delete call in `UndoableUnitOfWorkHelper.Do(...)`
(`RecordClerk.cs:1544-1545`), confirming Delete() is meant to run inside
caller-managed UOW/transaction scope, not as a self-contained operation.

## 5. Confirm/refute: `ILangProject.Texts` is derived read-only in LCM 11, texts unowned.

Confirmed. Reflection index entry for `Texts` property on ILangProject:
`"can_write": false`, `"relationship": "property"` (not `owns_atomic` /
`owns_collection` / `owns_sequence`), `"type": "IList"`
(liblcm_api_v11.0.0.json:75905-75926, duplicated at :137052-137073 for a
second interface exposing the same shape). Contrast with a genuinely
owned collection on the same object, e.g. `TextMarkupTags`
(`"relationship": "owns_atomic"`, :75900-75903) immediately preceding it
in the same properties array -- the JSON schema clearly distinguishes
owning relationships from plain derived properties, and `Texts` falls in
the latter category. This is consistent with LCM 11's known move away from
`LangProject.Texts` as an owning sequence toward Texts being independent,
unowned, repository-managed objects (a `ITextRepository`, imported at
`TextOperations.py:21`, is exactly the kind of top-level repository LCM
uses for unowned objects, paralleling `IWfiWordformRepository` for
wordforms). The commit's claim is correct: the old
`self.project.lp.Texts.Remove(text_obj)` mutated a derived, read-only,
throwaway list -- a true no-op -- which is why #317 existed.

## Recommendations

1. None blocking. Consider a one-line code comment cross-referencing
   `ILcmClearForDelete`/`Clear(forDelete)` so future readers don't have to
   re-derive the backref-clearing guarantee from first principles.
2. Given inbound-reference clearing is inferred (not directly observed in
   delete-pipeline source, which lives in the unavailable liblcm repo), a
   smoke test that deletes a text with an assigned genre and an
   interlinear-tagged discourse chart entry (if easy to construct) would
   convert this from "well-founded inference" to "verified."

---
**Reviewed By:** Domain Expert Agent
**Domain:** FieldWorks/LCM (Texts & Words)
