# Domain Expert Review — Issue #232: `GetPartOfSpeechObject` Semantics

**Cycle:** 1
**Agent:** lex-domain
**Date:** 2026-08-13

Root cause is settled and out of scope here: `flexicon/code/Lexicon/LexSenseOperations.py:1184`
does `getattr(msa, "PartOfSpeechRA", None)` on the **base** `IMoMorphSynAnalysis`, where that
property exists only on concrete subtypes. This review fixes the *semantic contract* the repair
must implement.

Evidence base: `flexicon/code/lcm_casting.py` (`get_pos_from_msa`, `cast_to_concrete` map),
`flexicon/code/Lexicon/LexSenseOperations.py` (`GetPartOfSpeech`, `GetPartOfSpeechObject`,
`SetPartOfSpeech` including its #87/#89 resolutions), `tests/contract/snapshots/liblcm_baseline.json`.

---

## Q1 — `MoDerivAffMsa`: `ToPartOfSpeechRA` or `None`?

`SetPartOfSpeech` already resolved this exact asymmetry under issue #87
(`LexSenseOperations.py:1388-1400`): when the existing MSA is `MoDerivAffMsa`, "Set POS" writes
`ToPartOfSpeechRA`, reasoned in-comment as "the canonical *output POS* ... matches what
SetPartOfSpeech logically means."

Round-trip check: `GetPartOfSpeechObject` returning `ToPartOfSpeechRA`, fed back into
`SetPartOfSpeech(sense, pos_obj)` with the default `msa_kind='auto'`, hits the
family+subtype-match short-circuit and rewrites only `ToPartOfSpeechRA` — a true no-op round
trip that never touches `FromPartOfSpeechRA`.

Returning `None` instead would break the docstring's own compare/reassign example and
misrepresent the sense as POS-less, when FLEx's *Grammatical Info.* field for a
derivational-affix sense visibly shows an input>output category pair — the output category being
what a user identifies as "the POS this affix produces."

The current docstring's "defer to #87" language is **stale**: #87 already chose
`ToPartOfSpeechRA` on the Set side. Returning `None` on Get would create a *new* asymmetry, not
preserve an existing one. Note this **overrides the issue reporter's suggestion** of `None`.

**RULING: Return `ToPartOfSpeechRA` for `MoDerivAffMsa` (delegate to `get_pos_from_msa`), matching SetPartOfSpeech's #87 resolution; delete the stale None/#87-deferral language from the docstring.**

## Q2 — Is `MoDerivStepMsa` reachable?

Absent from `cast_to_concrete`'s interface map, absent from `get_pos_from_msa`, and absent from
the liblcm reflection inventory in `tests/contract/snapshots/liblcm_baseline.json`. Every internal
source of truth — `cast_to_concrete`'s whitelist, `get_pos_from_msa`'s docstring enumeration, and
`SetPartOfSpeech`'s #89 comment naming "the known LCM whitelist" — agrees that the abstract
`MoMorphSynAnalysis` has exactly four concrete subclasses: `MoStemMsa`, `MoInflAffMsa`,
`MoDerivAffMsa`, `MoUnclassifiedAffixMsa`.

**RULING: `MoDerivStepMsa` is not reachable from `ILexSense.MorphoSyntaxAnalysisRA` in FW9/liblcm11; treat the reporter's mention as vestigial and exclude it from scope.**

## Q3 — Is `GetPartOfSpeech` (string getter) harbouring the same defect?

Confirmed in the liblcm baseline snapshot: the **base** `IMoMorphSynAnalysis` property list
directly includes `InterlinearAbbr` / `InterlinearAbbrTSS`, alongside `PosFieldName` /
`MLPartOfSpeech` — but **not** `PartOfSpeechRA`. That absence is precisely the #232 defect, and
precisely why `InterlinearAbbr` does not share it.

**RULING: `InterlinearAbbr` is genuinely declared on the base interface; the string getter needs no cast and carries no latent defect — leave `GetPartOfSpeech` unchanged.**

## Q4 — Silence or `logger.warning` on an unrecognized MSA class?

The harm in #232 was that the method returned `None` for every sense — including ordinary
stem/inflection cases with a perfectly valid POS — indistinguishably from "nothing set." The
codebase's own convention (`SetPartOfSpeech`, #89) already refuses to treat an unrecognized MSA
subtype as equivalent to a known-good state.

For a *getter*, raising is wrong: it would break every caller relying on `None` meaning "no MSA"
and break parity with `GetPartOfSpeech`. But staying silent on a *populated but unrecognized* MSA
reproduces exactly what #232 reports. Two `None` cases must be distinguished:

- (a) `msa is None` — no MSA at all. Normal. No log.
- (b) an MSA exists but its `ClassName` is not one of the four known POS-bearing subtypes — a
  real gap.

**RULING: Return `None` in both cases (preserving the caller contract), but emit `logger.warning` only for case (b), naming the sense and the unrecognized `ClassName`, so the gap is discoverable instead of silently collapsing into "no POS set."**

---

## Orchestrator verification note

The Q1 ruling was independently spot-checked against source before acceptance, because it
contradicts the issue reporter. `LexSenseOperations.py:1398` reads:

```python
msa = cast_to_concrete(existing_msa)
if existing_class == "MoDerivAffMsa":
    msa.ToPartOfSpeechRA = pos_obj
    return
```

The `ToPartOfSpeechRA` precedent and the round-trip claim are confirmed.
