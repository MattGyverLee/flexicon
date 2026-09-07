# Cycle 2 -- Doc Agent report: T3+T4 (paragraph/segment whitespace docs)

## T3 -- docstrings

Added one `Note:` line (not `Warning:`) to the `Args:` entry for
`content`/`text` in all four methods, matching each docstring's existing
voice/indentation, referencing #242:

- `flexicon/code/TextsWords/ParagraphOperations.py` -- `Create`, `SetText`,
  `InsertAt`
- `flexicon/code/TextsWords/SegmentOperations.py` -- `AppendSentence`

Text: "leading/trailing whitespace in the value is preserved verbatim
(#242); a value that is entirely whitespace still raises
FP_ParameterError." None of the four previously documented the stripping
at all -- closes the pre-existing gap per R2/domain's recommendation. No
executable line touched; verified by re-reading each patched block.

## T4 -- CHANGELOG.md

Added one bullet under `[Unreleased]` -> `### Changed`, after the
`SaveChanges()` guard bullet, before `### Fixed`, matching the
`**BREAKING (behavioural): ...**` register/depth of `CHANGELOG.md:15/63/431`
per C9's ruling. Names all four methods, cites #242, states the
persist-different-data risk with the `f"{sentence} "` /
`" ".join(...)` example and the `.strip()`-at-call-site mitigation,
states whitespace-only input still raises (emptiness contract
unchanged), frames the rationale as faithful reproduction of FLEx's own
`". "`-terminator structure (not cleanup), and notes the non-`str`
branch is no longer stripped either. Did not mention the 8 sibling
sites (C10 -- queued separately).

Included the P8 anomaly as a "**Known interaction, not yet resolved**"
sub-paragraph under the same bullet, citing the evidence file, stated
as unfixed and awaiting a `/lex-lead` ruling next cycle -- not
described as resolved or settled.

## Manifest

No `docs/MANIFEST.md` exists in this repo; CHANGELOG.md and docstrings
are the only artifacts in scope for T3/T4, both handled directly.

---
**Doc Agent:** /lex-doc
