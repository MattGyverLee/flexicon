# Issue #242 -- cycle 1 programmer report (measuring, not fixing)

Test file: `tests/operations/test_issue242_whitespace_probe.py` (5 tests, all
`requires_live_project`, fixtures `target_sandbox` / `target_sandbox_path`
only). Evidence: `specs/242-paragraph-whitespace/evidence/live-probe-cycle1.md`.

**`git diff --stat -- flexicon/` is empty** (pasted in the evidence file,
re-confirmed after the live run) -- no file under `flexicon/code/` was
touched.

## Gates

- Collect-only: `5 tests collected` (`test_p1`..`test_p5`).
- Offline baseline: `python -m pytest tests -m "not requires_live_project" -q`
  -> `1292 passed, 480 deselected` (passed count unchanged from the frozen
  baseline; deselected rose 475 -> 480, exactly +5 for the new live tests).
- Live run: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest
  tests/operations/test_issue242_whitespace_probe.py -m requires_live_project
  -q -s` -> `5 passed`. `tests/live_status.json` shows `"run_mode": "live"`.
- C28: predictions were written into the evidence file and committed
  (`b28c8640`) BEFORE the live measuring command ran; results were added in
  a second commit (`558654e`) after.

## Headline findings (all 5 predictions matched -- no misses this cycle)

**Whitespace does NOT survive layer A.** All four sites
(`Create`/`SetText`/`InsertAt`/`AppendSentence`) lose leading space,
trailing space, tabs, newlines, and NBSP identically, preserve internal
double spaces unchanged, and collapse `' *** '` to the exact FLEx null
marker `'***'` -- a semantic reclassification to "empty" for any
`normalize_text()`/`is_empty_text()` consumer, not just a whitespace trim.

**Whitespace DOES survive layer B.** Building the TsString from the raw,
unstripped payload and setting `para.Contents` directly (bypassing this
library entirely) preserved every one of the 8 payloads byte-for-byte,
including the padded null marker `' *** '`. **The loss is caused entirely
by this library's own `.strip()` calls; a fix is real, not cosmetic.**

**In-memory agrees with on-disk** for every payload measured (`test_p4`,
layer-B values, full open->write->close->reopen->read cycle) -- no
CloseProject()/reopen divergence found here, unlike item 1 of this
campaign.

**The segment baseline behaves like the paragraph Contents**:
`GetBaselineText()` was a clean tail-match of Contents for every payload
immediately after `AppendSentence`, with no measurable reparse lag. Note:
this probe used a fresh scratch paragraph per payload and did not
reproduce the owner's field report of 41/86 differing baselines in a
populated corpus -- that would need a separate, targeted follow-up.

**Non-str branch divergence confirmed live**: `ParagraphOperations.Create`
preserves a non-str payload's trailing space (`str(content)`, never
stripped); `SegmentOperations.AppendSentence` strips it
(`str(text).strip()`) even on the non-str branch.

No blockers encountered; Target sandbox and sandbox-path fixtures worked
as documented.
