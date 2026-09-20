# Doc Agent Report -- T2.7

**Date:** 2026-09-18
**Trigger:** `lcm-member-truth-sweep` campaign, task T2.7 (ruling C13)

## What was produced

`specs/lcm-member-truth-sweep/proposed-issues.md` -- 10 clusters, each with a
proposed title, affected `file:line` sites, member-named-vs-actual table,
symptom classification (silent no-op / silent wrong-value / loud crash),
confidence level, and a one-line suggested fix shape.

**Cluster count and confidence:** 10 clusters. 6 fully **live-confirmed**
(Clusters 1, 2, 6, 7, 8, 9), 3 fully **snapshot-derived** (Clusters 3, 4, 5 --
Discourse `ClauseMarkersOS`, sync-payload mismatches, phonological wrapper
fabricated members -- none of these were in T2.4/T2.5/T2.5b's live scope),
1 mixed (Cluster 10: two live-confirmed sites plus one additional site at
`DataNotebookOperations.py:243` (`GetAll`) that I noticed independently while
reading the file for line numbers, sharing the identical `isinstance` bug
pattern but not exercised by any live test in this campaign -- flagged
explicitly as snapshot-derived/unverified, not folded into the confidence of
the chartered sites). Clusters 1, 2, 6 map to Catalogue 2 rows 1-4/:825,
6-10, and 25 respectively; Clusters 7-10 are the four out-of-scope T2.4
findings (none in Catalogue 2). Cluster 6 (compound-rule contexts, row 25) is
recorded as CLEARED per T2.5b -- a "document the correct access path" issue,
not a rename, per ruling C9.

Also updated the `## Live upgrades` placeholder table in
`catalogue2-siblings.md` with the actual T2.5/T2.5b results transcribed from
`evidence/live-T2.5-siblings.md` -- no results invented.

## Confirmation

**Nothing in this task was filed.** `gh` was never invoked, at any point, by
this task. The proposed-issues.md header states the filing precondition
(`gh repo set-default MattGyverLee/flexicon`) and that the main session files
from this draft after review. No production file, no test file, and no
`flexicon/` path was touched. The string `flexlibs2` does not appear anywhere
in either file written by this task.

---
**Doc Agent:** /lex-doc
