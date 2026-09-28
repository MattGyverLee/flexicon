# Issue #330 -- SetDateOfEvent GenDate assignment (lex-lead ruling)

## Decision

**SetDateOfEvent** must assign a **normalized date string** to
`IRnGenericRec.DateOfEvent`, never a `System.DateTime` instance. Accept
`DateTime` or string from callers (unchanged public contract), validate with
`DateTime.Parse`, then format to `yyyy-MM-dd` or `yyyy-MM-dd HH:mm:ss` before
assignment -- mirroring `PersonOperations.SetDateOfBirth`, which already stores
GenDate fields via string assignment.

**GetDateOfEvent** is **out of scope** for this fix: it still returns the raw
GenDate object from the LCM. Docstrings already note the type mismatch; a
follow-up may normalize the read surface after `FindByDateRange` comparison
behaviour is audited.

## Pattern audit

Single chokepoint (`SetDateOfEvent`); no same-class siblings assign DateTime to
GenDate in this file. `Duplicate` copies GenDate objects directly and is
correct.

## Out of scope

- #328 Title/Text crashes
- #329 StatusRA/TypeRA/ConfidenceRA
- GetDateOfEvent return-type normalization
