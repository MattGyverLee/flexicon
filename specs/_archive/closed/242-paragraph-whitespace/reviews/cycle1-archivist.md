# Archivist report -- Issue #242, cycle 1

**Created:** `spec.md`, `tasks.md`, `STATUS.md`, `.crew-handoff.json`,
assembled from the three cycle-1 specialist reports plus the GitHub issue
#242 body (fetched via `gh issue view 242` -- none of the three reports
quoted the owner's verbatim 60/44 paragraph / 45/41 segment figures
directly). Every line number in C1/C4/C5/C6 was independently re-verified
against HEAD (not taken on any report's word); one correction surfaced:
the brief's "persist lines" (202/593/753/624) are the `MakeString(...)`
call lines, not the final `Contents =` assignment lines
(203/595/754/633) -- both now sit side by side in C1's table.

**C1-C7 frozen as fact:** dual line-numbering (issue-time vs HEAD); owner's
field evidence + the #239 `guid=` irony; the probe's three
decision-relevant measurements (whitespace survives a raw `MakeString`
write; in-memory agrees with on-disk; baseline behaves like Contents for
this probe's payloads) separated from what it did NOT reproduce (the
41/86 corpus figure); the null-marker ruling, discharged with negative
evidence; domain's `AppendSentence` finding (it inserts ". " with a
trailing space as its own terminator, then strips equivalent whitespace
from the next call -- internally inconsistent); the three-way str()-coercion
asymmetry (Paragraph preserves non-str, Segment strips it, `CheckOperations`
silently empties it); the sibling-sweep verdict (12 bug-shape sites vs
82/390 correct-shape).

**Contradictions preserved:** none found. All three reports, the evidence
file, and this pass's own re-verification were checked against each other
(spec.md section 5); the one apparent mismatch (Explore's "persist" lines
vs. the assignment lines) is a labelling-convention difference, not a
factual conflict.

**Left awaiting a `/lex-lead` ruling, never written as frozen:**
- **R1 (fix shape)** -- domain's direct-fix (a) recommended, kwarg (b)
  recommended rejected.
- **R2 (CHANGELOG)** -- `### Changed`, no `BREAKING`, plus a docstring
  `Note:` -- domain's recommendation; prose itself stays `/lex-doc`'s.
- **R3 (the 8 new sites)** -- marked IN/OUT OF SCOPE per site in C7's
  table; `tasks.md` Checkpoint 5 left with no tasks until R3 resolves.
- **Q3** (whether `CheckOperations.py`'s worse variant travels with R3) is
  also open.

`tasks.md` gates every code task behind Checkpoint 2 (CP-RULING, not a
code task); Checkpoint 3 is written provisionally on the direct-fix
assumption, flagged for rewrite otherwise.

**GitHub:** no issue filed. R3's sites and Q3 are recorded in
`.crew-handoff.json`'s `deferred_needs_user_approval` for future routing
into `specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user approval" --
its existing five items were read and left untouched. The
campaign-level `.crew-handoff.json` was not touched.
