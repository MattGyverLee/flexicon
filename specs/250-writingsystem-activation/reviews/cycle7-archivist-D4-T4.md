# D4-T4 -- Inventory re-verification and F2 settlement

**Task:** specs/250-writingsystem-activation/spec.md, D4-T4 (read-only, no edits, no pytest)
**Pin commit:** b3ba083b
**Command used:** git grep -n "ws.Id: ws.Handle" b3ba083b -- flexicon/

---

## Part 1: Section-3 inventory re-verification

Grep pinned to b3ba083b returns exactly 13 hits of the literal
ws.Id: ws.Handle, matching the spec's count of 13. Table below: my
found line (at b3ba083b) vs. the spec's claimed line.

| File | Found (b3ba083b) | Spec claims | Role (found) | Role (spec) | Drift? |
|---|---|---|---|---|---|
| BaseOperations.py | 1307 | 1307 | apply | apply | none |
| Grammar/PhonemeOperations.py | 1441 | 1441 | apply (ApplyBasicIPASymbol, 2nd local build) | apply | none |
| Grammar/PhonemeOperations.py | 1336 | 1336 | capture | capture | none |
| Grammar/POSOperations.py | 1155 | 1155 | capture | capture | none |
| Grammar/NaturalClassOperations.py | 1086 | 1086 | capture | capture | none |
| Grammar/EnvironmentOperations.py | 694 | 694 | capture | capture | none |
| Grammar/GramCatOperations.py | 630 | 630 | capture | capture | none |
| Grammar/InflectionFeatureOperations.py | 1647 | 1694 | capture | capture | LINE DRIFT: -47 |
| Grammar/MorphRuleOperations.py | 916 | 916 | capture | capture | none |
| Grammar/PhonFeatureOperations.py | 634 | 683 | capture | capture | LINE DRIFT: -49 |
| Grammar/PhonologicalRuleOperations.py | 1470 | 1470 | capture | capture | none |
| Grammar/StratumOperations.py | 287 | 287 | capture | capture | none |
| Lexicon/ExampleOperations.py | 491 | 491 | apply (see below) | capture | ROLE DRIFT |

### Drift call-outs

1. Grammar/InflectionFeatureOperations.py: spec says :1694, actually :1647
   at b3ba083b (a 47-line shift). Consistent with the spec's own
   section-6.1 warning that FS-feature T4/T5 work in the same cycle
   window could move things; this file moved even though the map-build
   idiom itself (all_ws = {ws.Id: ws.Handle for ws in
   self.project.WritingSystems.GetAll()}) is unchanged text.
2. Grammar/PhonFeatureOperations.py: spec says :683, actually :634 (a
   49-line shift). Same idiom, same explanation.
3. Lexicon/ExampleOperations.py: line number matches (:490-492 for the
   dict-comprehension body), but the spec's ROLE label is wrong. The
   spec's table calls this site "capture." It is not. Confirmed by
   function enclosure: the file has exactly one GetSyncableProperties
   (:365) and one ApplySyncableProperties (:431); the ws.Id: ws.Handle
   build at :488-492 is textually inside ApplySyncableProperties,
   guarding the TranslationsOC special-prop branch:

```python
# :488-492
# Resolve target writing systems once.
target_ws_by_id = {
    ws.Id: ws.Handle
    for ws in self.project.WritingSystems.GetAll()
}
```

This build feeds a third self-resolving apply loop, structurally
identical to _apply_props_loop's vulnerable pattern -- exact-case
dict.get, silent continue on miss, no delegation to
_apply_props_loop or BaseOperations at all:

```python
# :543-555
for src_ws_id, text in trans_text_dict.items():
    if not text:
        continue
    tgt_ws_id = (
        ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id
    )
    tgt_handle = target_ws_by_id.get(tgt_ws_id)
    if tgt_handle is None:
        continue
    new_trans.Translation.set_String(
        tgt_handle,
        TsStringUtils.MakeString(text, tgt_handle)
    )
```

This is out of scope to fix here (fence 1.2/C-D4-2: this is one of the
13 build sites, not to be touched), but it is a second genuine
Defect-4 coverage gap alongside PhonemeOperations' BasicIPASymbol path
(F2) -- worth folding into F1's follow-up ("13 sites, not 1") scope,
since it means at least two of those 13 sites feed self-resolving
apply loops rather than all being pure captures. This is a finding, not
an action; no site was edited.

### Fourteenth site

None found. git grep -n "ws.Id: ws.Handle" b3ba083b -- flexicon/ returns
exactly 13 lines, one per spec row, files matched 1:1. A broader sweep of
git grep -n "WritingSystems.GetAll()" b3ba083b -- flexicon/ turns up many
more call sites (Lexicon/AllomorphOperations.py, EtymologyOperations.py,
LexEntryOperations.py, LexReferenceOperations.py, LexSenseOperations.py,
PronunciationOperations.py, SemanticDomainOperations.py,
possibility_item_base.py, ParagraphOperations.py, and the doc/example
references in FLExProject.py / FLExProject.py.backup /
System/WritingSystemOperations.py / examples/demo_writing_systems.py),
but every one of those iterates ws_def/ws one at a time rather than
building an exact-case {ws.Id: ws.Handle} dict comprehension, so none of
them match the vulnerable idiom this spec's Defect-4 fix targets. No hit
was found in System/WritingSystemOperations.py of the vulnerable idiom
(fence 1.2 respected -- not touched, not even read for editing purposes
beyond this grep sweep).

---

## Part 2: Finding F2 -- settled

Question: Does Grammar/PhonemeOperations.py's apply path
(ApplySyncableProperties, whose second local build sits at :1441 inside
ApplyBasicIPASymbol) resolve writing-system handles itself, or delegate
to BaseOperations._apply_props_loop?

Verdict: MIXED.

PhonemeOperations.ApplySyncableProperties (b3ba083b, ~:1400-1431) splits
props into two groups and handles each differently:

```python
# base_props excludes BasicIPASymbol/Features/FeaturesGuid
base_props = {
    k: v
    for k, v in props.items()
    if k not in ("BasicIPASymbol", "Features", "FeaturesGuid")
}
super().ApplySyncableProperties(
    phoneme, base_props, ws_map, fill_gaps=fill_gaps
)

if isinstance(basic_ipa, dict) and basic_ipa:
    self.__ApplyBasicIPASymbol(phoneme, basic_ipa, ws_map, fill_gaps)
```

- Name / Description (in base_props) DELEGATE. super().ApplySyncableProperties(...)
  resolves to BaseOperations.ApplySyncableProperties, which builds its own
  target_ws_by_id at BaseOperations.py:1306-1308 and calls the shared
  helper:

```python
# BaseOperations.py, ~:1305-1321
target_ws_by_id = {
    ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()
}
...
with self._TransactionCM("Apply syncable properties"):
    _apply_props_loop(item, props, target_ws_by_id, fill_gaps,
                      ws_map=ws_map, ...)
```

These alts route through _apply_props_loop and so will inherit the
D4-T1 fix automatically.

- BasicIPASymbol SELF-RESOLVES. __ApplyBasicIPASymbol (:1433-1450) builds
  its own target_ws_by_id at :1441-1443 and performs its own exact-case
  resolution loop, never calling _apply_props_loop or the new
  _resolve_ws_handle helper:

```python
# PhonemeOperations.py, :1433-1450
def __ApplyBasicIPASymbol(self, item, ws_values, ws_map, fill_gaps):
    phoneme = self.__GetPhonemeObject(item)
    target_ws_by_id = {
        ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()
    }
    for src_ws_id, text in ws_values.items():
        if not text:
            continue
        tgt_ws_id = ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id
        tgt_handle = target_ws_by_id.get(tgt_ws_id)
        if tgt_handle is None:
            continue
        if fill_gaps and self.GetBasicIPASymbol(phoneme, tgt_handle).strip():
            continue
        self.SetBasicIPASymbol(phoneme, text, tgt_handle)
```

  This is byte-for-byte the same vulnerable shape as the pre-fix
  _apply_props_loop (exact-case dict.get, silent continue on miss) and is
  structurally isolated from it -- it will NOT inherit the Defect-4 fix. A
  phoneme synced with a differently-cased/separated BasicIPASymbol
  writing-system tag will still silently drop that alt after D4-T1 lands,
  even though the same phoneme's Name/Description alts would be saved.

Reportable gap: confirmed per spec section 7 F2 instructions -- this is a
genuine, real gap in the Defect-4 fix's coverage. It is one of the 13
fenced sites (PhonemeOperations.py:1441) and per C-D4-2 / fence 1.2 must
NOT be quietly patched here. It should be recorded alongside F1 (13
sites, not 1) and the newly-observed ExampleOperations.py self-resolving
TranslationsOC loop (Part 1, drift #3 above) as follow-up-issue material:
at least two of the 13 "map-build" sites (PhonemeOperations.py:1441,
ExampleOperations.py:490-492) are not just alternate builds but alternate
self-resolving apply loops that a lookup-only fix at _apply_props_loop
cannot reach.

---

## Scope compliance

- No source file edited. No pytest run of any kind.
- System/WritingSystemOperations.py not touched (grepped for context only
  in the broader sweep above, confirmed zero hits of the vulnerable idiom
  there; the file itself was not opened/edited).
- None of the 13 section-3 sites edited.
- PhonemeOperations.py read only, not edited.
- Section 1.3's four out-of-scope questions: noted, not acted on. (None
  of them arose directly in this task's read path, but flagging per
  instruction.)

Command log:
- git grep -n "ws.Id: ws.Handle" b3ba083b -- flexicon/
- git grep -n "WritingSystems.GetAll()" b3ba083b -- flexicon/
- git show b3ba083b:flexicon/code/Lexicon/ExampleOperations.py | sed -n '480,555p'
- git show b3ba083b:flexicon/code/Grammar/PhonemeOperations.py | sed -n '1300,1470p'
- git show b3ba083b:flexicon/code/BaseOperations.py | sed -n '1280,1330p'

---

**Archivist:** /lex-archivist
**Cycle:** 7
**Task:** D4-T4
