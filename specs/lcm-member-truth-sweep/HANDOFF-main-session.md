# Main-session operational handoff -- lcm-member-truth-sweep

**Audience:** the main session driving this campaign under the Ralph loop,
in a fresh context. `STATUS.md` tells you the campaign state; this file
tells you how to *run* it. Read both.

**Loop started:** 2026-09-18, after spurt 1 (`3b2c0789`).

---

## 1. The dispatch contract, and how it fails

The protocol is: `/lex-lead` returns a ```dispatch_plan``` block -> you
execute every task in it verbatim -> you re-invoke `/lex-lead` with report
**paths plus 2-line summaries**, never bodies.

**Known transport failure.** Only a subagent's FINAL hand-back reaches the
main session. Anything lex-lead writes before that is discarded. In spurt 1
lex-lead composed the block, believed it had sent it, and reported back
"the block is in my prior message" -- three times. The block itself never
arrived.

**Fix, in order of preference:**

1. When re-invoking lex-lead, state plainly: *"Make the fenced
   `dispatch_plan` block the ENTIRE BODY of your hand-back report -- not a
   description of it, not a claim that it exists elsewhere."*
2. If it still does not arrive, do **not** retry a fourth time and do not
   reconstruct the prompts from lex-lead's prose summary.

   **-- CHECK THIS BEFORE RELYING ON THE SNIPPET BELOW (spurt 4, 2026-09-18). --**
   The transcript-extraction fallback **did not work** in the spurt-4 session.
   It is not that the parse failed: every subagent `output_file` under
   `.../tasks/*.output` was **0 bytes**, for all eleven agents of that
   session, so there was nothing to parse. The block lex-lead believed it had
   emitted was simply gone. Recovery there was a `SendMessage` back to the
   same agent (which resumes it with its context intact, so it can re-emit the
   block cheaply without re-deriving the plan) -- prefer that over a fresh
   `Agent` call, which would re-plan from scratch.

   Treat the snippet as conditional: `stat` the `output_file` first, and only
   parse it if it is non-empty. When it is empty, fall back to `SendMessage`.
   Where the transcript IS populated, it is large (300KB+ of JSONL) -- never
   `cat`/`tail` it. Parse it:

```python
# adapt the path; the agent's output_file is given in its spawn result
import json, re
best = None
def walk(o, out):
    if isinstance(o, str): out.append(o)
    elif isinstance(o, dict):
        for v in o.values(): walk(v, out)
    elif isinstance(o, list):
        for v in o: walk(v, out)
for line in open(TRANSCRIPT, encoding="utf-8"):
    line = line.strip()
    if not line: continue
    try: obj = json.loads(line)
    except Exception: continue
    strs = []; walk(obj, strs)
    for s in strs:
        if "```dispatch_plan" in s:
            m = re.search(r"```dispatch_plan\n(.*?)\n```", s, re.S)
            if m and (best is None or len(m.group(0)) > len(best)):
                best = m.group(0)
open(OUT, "w", encoding="utf-8").write(best)
```

   This worked in spurt 1 and cost one tool call.

---

## 2. Which specialists can write their own report files

This is ruling **C14**, and violating it silently defeats the path-relay
discipline -- the read-only agent pastes its full body back, and the body
transits your context anyway.

| Agent | Tools | Writes own report? |
|---|---|---|
| `lex-verification` | Read, Grep, Glob, **Bash** | YES |
| `lex-programmer` | Read, Grep, Glob, Bash, **Edit, Write** | YES |
| `lex-doc` | Read, Grep, Glob, **Edit, Write** | YES |
| `lex-archivist` | Read, Grep, Glob, Bash, **Edit** | Edit only -- cannot create a new file |
| `lex-simplify` | Read, Grep, Glob, **Edit** | Edit only -- cannot create a new file |
| `lex-domain` | Read, Grep, Glob | **NO** |
| `lex-qc` | Read, Grep, Glob | **NO** |
| `lex-author` | Read, Grep, Glob | **NO** |
| `lex-synthesis` | Read, Grep, Glob | **NO** |
| `lex-README` | Read, Grep, Glob | **NO** |
| `Explore` | read-only by design | **NO** |

For a NO row: the dispatch must cap the report body by word count, and you
persist it to `specs/lcm-member-truth-sweep/reviews/cycle<N>-<agent>.md` on
the agent's behalf. Add a provenance note at the top -- see the existing
`cycle1-domain.md` and `cycle1-explore.md` for the exact wording. Keep the
content verbatim; do not edit or summarize it into the file.

**Writing tip:** `Write` beats a Bash heredoc for these. A heredoc carrying
backticks, quotes and pipe tables failed to parse in spurt 1; `Write`
handled the same content first try.

---

## 3. Commit discipline for this campaign

- "Commit" means **commit AND push** (user's global CLAUDE.md). A commit
  that never reaches `main` on GitHub leaves the work looking unfinished.
- Direct-to-`main` is the house convention on this solo fork.
- `core.hooksPath` is already set to `.githooks` in this clone, so the
  commit-msg guard is live. It blocks a close-keyword in a **possessive,
  negated, quoted, or narrated** position. Referring to the issues as
  `for #302/#261/...` is safe; `close #283's review` is not.
- **These six issues must NOT be auto-closed by commit keyword** until the
  campaign actually lands each fix. Phrase around the verb.
- Keep unrelated working-tree changes out of campaign commits. At spurt 1
  there was an in-flight `examples/grammar_pos_operations_demo.py` edit and
  a `specs/grammar_pos_demo_fix/` tree from separate work; check
  `git status --porcelain` and stage paths explicitly, never `git add -A`.

---

## 4. Live verification -- non-negotiable

Every checkpoint from 2 onward touches Operations classes and the write
path, so a mock pass is a FAILED verification, not a safety net.

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest <live test file> -m requires_live_project -q
```

Never bare `pytest` and never `pytest --ignore=tests/contract` -- neither
applies an `-m` filter, so both EXECUTE the ~322 `requires_live_project`
tests in place against real projects.

Then confirm, every time:

```
python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"
```

It must print `live`. If it prints `mock`, the run proved nothing -- report
`FAIL: unverified` and do not claim the checkpoint.

Evidence goes to `specs/lcm-member-truth-sweep/evidence/live-<task>.md` with
the exact command, the `run_mode` value, pre-state and post-state **read
back from the LCM** (re-query the object; asserting on the value you passed
in proves nothing), and a pass/fail line.

**Testbed:** the user authorized **Sena 3** for this campaign, preferring
the `sena3_sandbox` fixture (tempdir copy of the `.fwbackup` -- nothing
leaks). Seeding inside that sandbox is authorized, `TEST_` prefix, restored
in a `finally:`. Use `target_sandbox` where a task genuinely needs a clean
slate. Never open or write the live Target or the live Sena 3 unattended.

---

## 5. Stop conditions

Stop and surface to the user -- do not let the loop proceed -- when:

- lex-lead's handoff has `status: needs_human`. Relay the `blocker` verbatim.
- The next step would be a **destructive live-LCM write** (e.g. writing to a
  target that must be `-restore`d first). The loop must never do this
  unattended.
- **T2.7 / T8.4 -- gate LIFTED 2026-09-18.** The user authorized filing
  directly ("you can file the issues. don't wait for me"), so the crew may
  run `gh issue create` for the Catalogue 2 batch on
  `MattGyverLee/flexicon` without pausing. `gh repo set-default
  MattGyverLee/flexicon` has been run in this clone. The authorization
  covers **filing only** -- it does not authorize closing #302/#261/#283/
  #259/#303/#309, and it does not relax the destructive-live-write stop
  condition. Catalogue 2's sibling issues are still drafted into
  `proposed-issues.md` first, so the filed text is reviewable.
  The `set-default` step is not optional: with no default, `gh`
  prefers `upstream` (`cdfarrow/flexlibs`), whose numbering tops out near
  #17, so every issue this project cites returns "Could not resolve to an
  issue", which reads exactly like "it does not exist."
- A live probe contradicts a binding ruling (C1-C14). Flip the ruling in
  `spec.md` **before** writing code against it -- that is the whole point of
  T2.1 gating C1.

On `status: feature_complete`, lex-lead also emits
`<promise>FEATURE COMPLETE</promise>` and the loop exits; report the final
approval to the user.

---

## 6. Two hazards already known, so nobody rediscovers them

- **Q2 / C11 -- `SetInflectionClass` is blocked.** An MSA is shared across
  bundles, so writing `msa.InflectionClassRA` through a bundle handle may
  mutate every sibling bundle. The read path and the copy loops proceed; the
  write path waits for a domain ruling backed by a live sharing count
  (T4.4). Do not "just implement the setter."
- **`compound_rule.py:220` and `:244` are NOT the #283 bug.** They read
  `LeftContextOA`/`RightContextOA` on `IMoEndoCompound`/`IMoExoCompound`,
  which carry **neither** the `...OA` nor the `...RA` form. A blind OA->RA
  sweep breaks them in both directions. They are Catalogue 2 row 25, a
  separate candidate bug, and stay out of this campaign.
