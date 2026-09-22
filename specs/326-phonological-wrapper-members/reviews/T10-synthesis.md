# T10 Synthesis — Issue #326: Phonological Wrapper Members

## Consensus

T1 live reflection established the LCM facts: `FeatureStructureRA` is the
actual link for simple segment and natural-class contexts; metathesis uses
`StrucDescOS` with switch/index ranges; and no `PhReduplicationRule`,
`IPhReduplicationRule`, or reduplication factory exists in the tested LCM.
T2's sweep found the affected code, tests, and documentation. T5 implemented
the corrections, preserved the real ConstChart segment members, and
deprecated the four public reduplication symbols through v5.0.0. T6 found no
behavioral change from simplification. T7 synchronized the documentation and
changelog.

T8 independently re-queried the final behavior against live LCM projects:
the context links resolved to real phoneme/natural-class objects and
metathesis parts resolved to real `PhSimpleContextSeg` wrappers. The live gate
was `run_mode == "live"`. T9 independently confirmed the pattern audit,
validation/error handling, warning coverage, no new alias references, and
assigned 96/100 with no P0/P1 findings.

## Conflict and resolution

T3 recommended removing the reduplication API immediately. T4 identified
`redup_rules()`, `has_redup_parts`, `redup_parts`, and
`as_reduplication_rule` as public surfaces and recommended deprecating them
now, then removing them at the established v5.0.0 boundary. T4's
compatibility ruling won: T5 retained these symbols with
`DeprecationWarning` and v5.0.0 messaging. T3's technical conclusion that
reduplication has no live LCM backing was retained.

T3 also recommended repairing metathesis in place using structural-description
slices rather than exposing raw indices. T4 agreed this was a behavioral
repair, not a removal; T5 implemented it accordingly.

## Gaps and blockers

- The offline suite still has five previously known, unrelated failures;
  T5, T6, T8, and T9 observed the same set with no new failures.
- T9 notes three non-blocking P2 items: repeated inline imports, an
  evidence-only T8 scratch test file to clean up or fold into the permanent
  suite, and the unusable Sena 3 fixture.
- Sena 3 could not be opened, but T8 used the sanctioned Target-sandbox plus
  read-only installed-project fallback and obtained live read-back evidence.

None of these gaps blocks approval. No production-code or commit action is
required from T10.

## Verdict

**APPROVE**
