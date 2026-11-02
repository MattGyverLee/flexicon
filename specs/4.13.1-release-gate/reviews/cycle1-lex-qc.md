# Cycle 1 QC (lex-qc) -- 4.13.1 release-prep commit f2c41871

Transcribed by the main session from the lex-qc hand-back (that agent had no
Write/Bash tool, and read current files only -- no diff or git log).
Score 68/100. P0=0, P1=2.

## P1
1. CHANGELOG.md:60-61 -- "Other fixes in this release carry offline and live
   evidence under `specs/`." Overstated: only #802 was run live at authoring
   time; per-issue evidence for the others says "FAIL: unverified".
2. RELEASE_NOTES_v4.13.1.md:28-31 "Known gaps" lists only #740, implying the
   rest were verified; lines 14-19 state outcomes as confirmed. CHANGELOG.md
   18-19 and 54-55 also give no hint the write paths lacked live proof.

## P2
3. MorphRuleOperations.py:742-764 -- `.Remove` is inside `_TransactionCM` in all
   3 branches; `_EnsureWriteEnabled` intact; HVO matching correct for
   CompoundRulesOS / AffixTemplatesOS / AdhocCoProhibitionsOC. Weakness: when
   `__FindMemberByHvo` returns None, Delete silently does nothing but still
   opens an empty named undo entry (contradicts the comment at 739-741).
   Should raise/log and open the bracket only after a member is found.
4. tests/operations/test_issue802_morphrule_delete_hvo_offline.py:31-43 asserts
   on source text only; would pass with a broken helper. No behavioural offline
   test with distinct stub objects sharing an Hvo.
5. tests/contract/extract_lcm_contract.py:217 -- SYSTEM_TYPE_MEMBERS is global
   (all LCM types), not scoped to IMultiString/IMultiUnicode. Low risk.

## P3
6. Mock edits (test_574, test_340, test_472) look faithful (Hvo / __iter__ added;
   no assertion weakened that was visible). The 472 stub's __contains__ and
   IndexOf still match by Python identity, so it cannot reproduce the
   bare-interface-view problem.
7. Version 4.13.1 in __init__.py OK; CHANGELOG and notes agree except P1.

## Q5 (verified afterwards by main session with shell)
- No `flexlibs2` in lines added since v4.13.0 (shim dir, CHANGELOG, specs, docs excluded).
- 56 close-keyword uses, all intended `closes #N` on the fixing commit; no prose misuse.

## Gates
- Live-LCM evidence gate: BLOCK for ~89 fixes (offline-only) at time of review.
