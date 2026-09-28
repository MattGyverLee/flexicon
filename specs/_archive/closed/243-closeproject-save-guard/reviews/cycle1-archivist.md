# Cycle 1 -- Archivist: spec + tasks authored for #243

**Frozen (spec.md C1-C8):** C1 fix is a GUARD around line 326, not a
reorder (P-5 verdict). C2 exposes `HasOpenSessionTask()` + `CurrentDepth`.
C3 scopes `HasOpenSessionTask()` narrowly (`False` under `undoable=True`).
C4 sets edge returns (read-only: real value, no raise; closed/never-opened:
`FP_ProjectError`). C5 consolidates the depth read into one private helper;
the lenient `except: return 0` stays out of the public surface. C6 makes P1
a hard prerequisite of P0 -- the guard checks depth first, then still wraps
the End call. C7 keeps End-then-Save order. C8 assigns P2's CHANGELOG prose
to `/lex-doc`.

**Left open:** Q1 (REQUIRED) -- probe reproduced total loss but not owner's
file-swap or literal `Commit at wrong place.` via P-3; that string only
arises from P-5's sequence, so owner's incident likely matches P-5, not
P-3 -- reconcile before final. Q2 -- broader `try/finally`? Q3 -- P1 joins
`flexicon.CAPABILITIES`? Q4 -- CHANGELOG wording, deferred to `/lex-doc`.

**Checkpoints (tasks.md):** 1 = T1-T2, P1 depth-read surface. 2 = T3-T4, P0
guard + regression tests extending the existing probe's P-3/P-5 in place.
3 = T5, CHANGELOG, docs-only, live-exempt.

**Contradiction found:** the issue/QUEUE prose frames P0 as reordering
`Save()` before/independent of the End mirror; P-5 refutes that -- `Save()`
itself raises at `CurrentDepth > 0` and collapses the envelope, trading one
guaranteed raise for another. spec.md follows the probe, not the issue
prose.

No file under `flexicon/code/` touched. No GitHub issue filed.
