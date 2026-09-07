# DRAFT ISSUE — NOT FILED

**Status: awaiting user approval. Do NOT post this to GitHub without it.**

Drafted 2026-09-07 by session `flexicon-cd`, cycle 7, under the crew split
agreed with session `flexicon-19` (which holds the live-pytest token and the
#250 campaign state). Target repo: `MattGyverLee/flexicon`. Precedent for
draft-then-approve: `specs/254-getmorphtype-allomorph/reviews/cycle3-archivist-inflclass-issue-draft.md`
and flexicon#265, both of which were drafted here and filed only after the
user approved.

---

## Title

`ApplySyncableProperties`: two writing-system apply paths still drop
case/separator-divergent alts (the sites #250 Defect 4 did not reach)

## Labels (suggested)

`bug`, `silent-data-loss`, `writing-systems`, `follow-up:250`

---

## Body

### Summary

#250 Defect 4 fixed writing-system id resolution in
`BaseOperations._apply_props_loop`, so a target writing system whose `Id`
differs from the source only by **case** (`ETU` vs `etu`) or **separator**
(`en_US` vs `en-US`) now resolves instead of being silently dropped.

Two other apply paths perform the **same self-resolving lookup** and were
deliberately left out of that fix's fence. They still drop divergent alts
silently:

| # | Site | Method | Property affected |
|---|---|---|---|
| 1 | `flexicon/code/Grammar/PhonemeOperations.py:1447` | `__ApplyBasicIPASymbol` | `BasicIPASymbol` |
| 2 | `flexicon/code/Lexicon/ExampleOperations.py:551` | `ApplySyncableProperties`, `TranslationsOC` loop | `ICmTranslation.Translation` |

Both contain this exact shape, byte-for-byte the pre-fix
`_apply_props_loop` code:

```python
tgt_ws_id = ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id
tgt_handle = target_ws_by_id.get(tgt_ws_id)   # <-- exact-match only
if tgt_handle is None:
    continue                                   # <-- silent drop
```

### Why this is worth its own issue

**The user-visible symptom is an inconsistency inside a single object.**
Syncing one phoneme between two projects whose writing-system ids differ
only in case now saves its `Name` and `Description` (they go through the
fixed `_apply_props_loop`) but silently discards its `BasicIPASymbol`
(site 1). The phoneme arrives looking complete and is not. There is no
warning, no exception, and no log line — the alt simply is not there.

Site 2 has the same shape for example-sentence translations: the example's
own fields transfer, its translations lose divergent alts.

### Site 1 is a one-line substitution. Site 2 is not — read this before estimating

#250's contract **C-D4-7** required the new resolver to be a module-level
function taking every input as a parameter — no `self`, no project handle —
*specifically* so these two sites could be closed without refactoring.
`flexicon/code/BaseOperations.py` already exports it, and its docstring
names both call sites as the intended future consumers:

```python
def _resolve_ws_handle(target_ws_by_id, tgt_ws_id, _index_cache=None):
```

So each site becomes:

```python
tgt_handle = _resolve_ws_handle(target_ws_by_id, tgt_ws_id, _index_cache)
```

`_index_cache` should be a dict created once per apply call and passed to
every iteration, per **C-D4-4** (build the normalized side-index at most
once per apply operation; the all-exact-hits path stays allocation-free).

**That holds for site 1 only.** For site 2 the substitution is necessary but
not sufficient, and treating it as a one-liner will produce a bug. See
"Decisions" item 2 below: the loop creates and attaches the `ICmTranslation`
*before* it resolves any writing system, so introducing a resolver that can
raise turns a previously-total operation into a partially-completed one.
Site 2 needs the resolution reordered ahead of object creation, or a proven
rollback — not a one-line swap. Estimate the two sites separately.

### Decisions the implementer must make — this is why it is not a trivial PR

1. **New failure mode.** `_resolve_ws_handle` raises `FP_ParameterError`
   when a normalized id matches **two or more distinct handles** (C-D4-3
   step 2b — ambiguity is never guessed). Routing these two sites through
   it means `SetBasicIPASymbol` and the translation writer can now raise
   where they previously always degraded silently. That is the correct
   behaviour, but it **is** a behaviour change and needs a CHANGELOG entry
   naming it.
2. **Partial-write semantics on site 2.** The `TranslationsOC` loop has
   already created and attached `new_trans` by the time the writing-system
   resolution runs. If resolution now raises mid-loop, an
   `ICmTranslation` with zero alts set may be left owned by the example.
   Decide whether to resolve all handles **before** creating the object, or
   to let the surrounding transaction roll it back — and verify which one
   actually happens rather than assuming.
3. **Scope check.** Fix only these two. #250 acceptance criterion 7 forbids
   touching the 13 map-**build** sites, and criterion 6 makes any edit to
   `flexicon/code/System/WritingSystemOperations.py` an automatic rejection.
   This issue is lookup-only, exactly as Defect 4 was.

### Verification requirements

Per `CLAUDE.md`, both sites are write paths, so **a mock-only pass is not
verification**. Required:

- Live run on `target_sandbox` with `FLEXLIBS_REQUIRE_LIVE=1`, asserting
  `tests/live_status.json` reads `"run_mode": "live"`.
- **Both sides measured**: demonstrate the drop on unfixed code first, then
  the save on fixed code. Do not assume the pre-fix behaviour.
- Post-state re-read from a **freshly re-fetched** object — asserting on the
  value just passed in proves nothing.
- **C-D4-6** assertions carried over: writing-system count unchanged, and
  `CurVernWss` / `CurAnalysisWss` byte-identical before and after. The fix
  must never activate, create, or widen the writing-system store.
- The `BasicIPASymbol` case additionally needs the scalar-vs-multistring
  shape guard from #222 to stay intact.

### Ratchet interaction — read before starting

`tests/operations/test_issue250_defect4_ws_resolution.py` contains a
resolution-site ratchet asserting the set of self-resolving sites is
**exactly three** (`BaseOperations.py`, `PhonemeOperations.py`,
`ExampleOperations.py`). Closing either site above **will turn that ratchet
red**, by design — its failure message says so and instructs you to update it
when a site is legitimately fixed. Update the frozen set in the same commit;
do not disable the test.

### Non-sites (checked, recorded so the next person does not re-derive it)

`PhonemeOperations.py:1336` (`all_ws = {ws.Id: ws.Handle ...}`) looks similar
but is a **read** path — `GetSyncableProperties` enumerating *source* writing
systems via `__ReadMultiString`. It performs no target resolution and is one
of the 13 protected map-build sites. It is correctly excluded from the
ratchet's three-site set.

### References

- `specs/250-writingsystem-activation/spec.md` — section 3 errata (the
  three-row resolution-site table), C-D4-1..C-D4-7, acceptance criterion 8
- `specs/250-writingsystem-activation/reviews/cycle7-archivist-D4-T4.md`
- `flexicon/code/BaseOperations.py` — `_normalize_ws_tag`,
  `_resolve_ws_handle`, and their contract docstrings
- `CHANGELOG.md` `[Unreleased] → Fixed` — already states this coverage
  boundary in plain words, per #250 acceptance criterion 8

---

## Notes for the approver (not part of the issue body)

- **Nothing here is filed.** Approve, edit, or reject; I will not post it.
- The coverage boundary this issue describes is *already documented* in
  `CHANGELOG.md` and in `evidence/live-D4-T3.md` per #250 acceptance
  criterion 8. Filing this converts a documented known-limitation into a
  tracked work item. If you would rather leave it as a documented limitation
  for now, that is a coherent choice and nothing in #250 depends on it.
- **One issue or two — I've changed my answer to two.** My first draft
  leaned "one issue", reasoning that the two sites share a root cause and an
  identical one-line fix. The second half of that is wrong. Site 1
  (`BasicIPASymbol`) really is the one-line C-D4-7 substitution. Site 2
  (`TranslationsOC`) is not: because the `ICmTranslation` is created and
  attached before any writing system is resolved, adding a resolver that can
  raise converts a total operation into a partial one, and closing it
  properly means reordering the loop or proving the transaction rolls back.
  Different sizes, different risk, different reviewers (Grammar vs Lexicon),
  different live fixtures. Bundling them would let the easy one carry the
  hard one through review. **Two issues**, with site 1 as the quick win and
  site 2 explicitly scoped as a correctness change rather than a substitution.
- `flexicon-19` is drafting the D4-T6 comment for #250 itself. These two
  texts should not contradict each other on the coverage boundary; this
  draft has been shared with that session for exactly that reason.
