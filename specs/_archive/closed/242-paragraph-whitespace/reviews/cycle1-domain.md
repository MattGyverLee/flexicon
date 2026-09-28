# Domain Expert Review — Issue #242 Paragraph/Segment Whitespace Stripping

**Date:** 2026-09-07
**Cycle:** 1 (campaign `tier1-silent-data-loss`, queue item 2)
**Persisted by:** main session (lex-domain has no Write tool)

## Q1 — Is the strip load-bearing for the FLEx null-marker path?

**No. Discharged with negative evidence: the null-marker mechanism is entirely absent from these four write sites and their read counterparts.**

`normalize_text`/`FLEX_NULL_MARKER` handling (`flexicon/code/Shared/string_utils.py:18-47`) exists only for **multilingual accessor fields** (`IMultiString`/`IMultiUnicode` `BestAnalysisAlternative`/`BestVernacularAlternative`) — the module header says so explicitly (`string_utils.py:7-9`). Grepping every caller of `normalize_text` across the codebase turns up 15 files, all in Lexicon/Grammar/Notebook (`LexEntryOperations.py`, `LexSenseOperations.py`, `PhonemeOperations.py`, etc.). **`ParagraphOperations.py` and `SegmentOperations.py` are not in that list — zero matches for `normalize_text`, `FLEX_NULL_MARKER`, or `string_utils` in either file.**

Confirmed by reading the read paths directly: `GetText` (`ParagraphOperations.py:541-542`) does `text = para_obj.Contents.Text if para_obj.Contents else ""`; `GetBaselineText` (`SegmentOperations.py:337`) does `segment_obj.BaselineText.Text or ""`. Neither calls `normalize_text` or checks for `"***"`. Also, `IStTxtPara.Contents` and `ISegment.BaselineText` are plain `ITsString`, not `IMultiString` — the type the null-marker mechanism actually applies to.

The specific delta raised in the brief (`' *** '` -> strip -> `'***'` -> read-back `''`) does not occur here: since the read path never calls `normalize_text`, a literal `"***"` written to `Contents` reads back as literal `"***"`, not `""`. This is a **pathological-input-only curiosity**, not a regression tied to null-marker semantics — because the null-marker path doesn't run on this data at all, under either the current code or the fix. A FLEx user typing three asterisks and spaces would expect exactly what they typed back, verbatim; neither today's behavior nor the fix's behavior involves the null marker.

## Q2 — What does FLEx itself do?

The codebase's own segment-construction logic answers this. `AppendSentence` (`SegmentOperations.py:612-617`) explicitly builds multi-sentence paragraphs by inserting `". "` — period **plus a trailing space** — as the sentence terminator (`terminator = TsStringUtils.MakeString(". ", ws)`), then computes the next insertion point as `current_length + 2` to land after that space. This is the same file that then strips trailing whitespace on the *next* `AppendSentence` call's input (line 595) — internally inconsistent.

It demonstrates that trailing whitespace inside paragraph content is not anomalous in this domain's own data model; it's how sentence boundaries are represented. Segment baselines in FLEx's interlinear analysis routinely include the trailing space up to the start of the next segment — this is structural, not corruption. So: preserving whitespace is **faithfully reproducing valid FLEx paragraph structure**, not fixing corrupt data.

## Q3 — Fix shape

**Recommend (a), the direct fix — unambiguously.**

Critically, (a) already matches the codebase's *actual* dominant idiom, not just its style. Verified at `POSOperations.py:190-206`: the check is `if not name or not name.strip(): raise ...`, but the **persisted** value at line 205 is the original `mkstr_name = TsStringUtils.MakeString(name, wsHandle)` — the un-mutated `name`, not a stripped copy. The `.strip()` result is used transiently for the truthiness test and discarded. That is exactly candidate (a)'s shape, and it's the pattern at 60+ sites (`PhonemeOperations.py:188`, `PossibilityListOperations.py:222`, `possibility_item_base.py:178`, etc.).

Paragraph/Segment's bug is that `content_str` — the *stripped* copy — is what gets passed to `MakeString` (`ParagraphOperations.py:180,202`; `585,593`; `726,753`; `SegmentOperations.py:595`), diverging from the codebase's own convention, not just from an abstract ideal.

(b)'s `preserve_whitespace=False` kwarg is the CLAUDE.md anti-pattern named directly: "do not make the caller manage a flag to get correct data." It would also make these four methods the only ones in the library with an opt-in flag for behavior every other CRUD method gives for free. Reject (b); it's an inconsistency, not a safety net — the owner's own preference is correct.

## Q4 — Breaking change?

Yes, worth a `### Changed` CHANGELOG entry, no `BREAKING` prefix (no signature or exception-type change, unlike #254's `GetMorphType`).

Candidates who could be relying on today's stripping: interactive scripts building text via `f"{sentence} "` loops or `" ".join(...)` that never itself calls `.strip()`, expecting the library to absorb the padding — precisely the class of silent-dependency risk Item 1's `undoable` flip taught the campaign to flag explicitly rather than assume nobody's affected.

Recommend: a CHANGELOG `### Changed` bullet naming the four methods and the round-trip-fidelity rationale, plus a one-line `Note:` (not `Warning:`) added to each of the four docstrings' `Args` section for `content`/`text`, since none currently document the stripping behavior at all — the current silence is itself a documentation gap independent of which way this is fixed.
