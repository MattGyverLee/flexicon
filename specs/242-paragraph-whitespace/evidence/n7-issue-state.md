# N7 -- Did the `closes #242` keyword in commit 066bab0 fire?

Investigation date: 2026-09-08. Branch: `spec/242-gate-and-name-field-identity`.
Method: read-only `gh` / `git` queries. No issue, PR, or ref was modified.

## Bottom line

**The keyword fired. #242 was auto-closed by commit `066bab0` on 2026-09-07 at
19:25:16Z.** The `gh issue view 242` failure from the earlier session was a
*wrong-repository* artifact, not evidence that the issue does not exist.

And the blast radius is larger than N7 as scoped: **the same push also
auto-closed flexicon#243**, whose campaign record says it was
"deliberately left OPEN". That closure is the more serious of the two.

---

## 1. Repository identity -- the source of the earlier ambiguity

Two remotes are configured (`git remote -v`):

```
origin   https://github.com/MattGyverLee/flexicon.git (fetch)
origin   https://github.com/MattGyverLee/flexicon.git (push)
upstream https://github.com/cdfarrow/flexlibs.git (fetch)
upstream https://github.com/cdfarrow/flexlibs.git (push)
```

No default repo is set:

```
$ gh repo set-default --view
X No default remote repository has been set.
```

(`.git/config` contains no `gh-resolved` key -- confirmed by grep.)

With no default set and multiple remotes, `gh` prefers the remote named
`upstream`. So `gh` was talking to the **wrong** repo:

```
$ gh repo view --json nameWithOwner,isPrivate,defaultBranchRef
{"defaultBranchRef":{"name":"main"},"isPrivate":false,"nameWithOwner":"cdfarrow/flexlibs"}
```

`cdfarrow/flexlibs` is the ancestor project this library was forked from. Its
numbering tops out around #17:

```
$ gh issue list --repo cdfarrow/flexlibs --state all --limit 5 --json number,state,title
15 OPEN    Support getting custom list field values without h
14 CLOSED  AllProjectNames() returns invalid projects
11 CLOSED  Can't get it to work with FLEx 9.1.18
...
$ gh pr list --repo cdfarrow/flexlibs --state all --limit 3    ->  17, 16, 13
```

So #242 is simply **out of range** in `cdfarrow/flexlibs` -- which is precisely
the benign-looking explanation the task anticipated, and it is *true of that
repo* while being irrelevant to the actual question. `MattGyverLee/flexicon`
is at #268 with 23 open issues.

**This is a latent trap for every future session**: any bare `gh issue` /
`gh pr` command in this working copy silently queries the fork parent. See the
recommendation.

## 2. Auth status -- not a factor

```
$ gh auth status
github.com
  - Logged in to github.com account MattGyverLee (keyring)
  - Active account: true
  - Token scopes: 'gist', 'project', 'read:org', 'repo', 'workflow'
```

Authenticated as the repo owner with full `repo` scope. `MattGyverLee/flexicon`
is reachable and every query below succeeded. `cdfarrow/flexlibs` reports
`"isPrivate":false`. Neither auth nor visibility explains the earlier failure.

## 3. Does #242 exist, and what is its state?

Yes, in `MattGyverLee/flexicon`:

```
$ gh issue view 242 --repo MattGyverLee/flexicon --json number,state,stateReason,closedAt,title,url
{"closedAt":"2026-09-07T19:25:16Z",
 "number":242,
 "state":"CLOSED",
 "stateReason":"COMPLETED",
 "title":"Paragraph/Segment text writers silently strip leading/trailing whitespace",
 "url":"https://github.com/MattGyverLee/flexicon/issues/242"}
```

242 is **not** a PR number:

```
$ gh pr view 242 --repo MattGyverLee/flexicon
GraphQL: Could not resolve to a PullRequest with the number of 242. (repository.pullRequest)
```

### Who closed it, and via which commit

The issue timeline names the closing commit explicitly:

```
$ gh api repos/MattGyverLee/flexicon/issues/242/timeline \
    --jq '.[] | select(.event=="closed" or .event=="referenced") | {event, actor: .actor.login, created_at, commit_id}'
{"event":"referenced","actor":"MattGyverLee","commit_id":"8629d257...","created_at":"2026-09-07T19:25:14Z"}
{"event":"referenced","actor":"MattGyverLee","commit_id":"b0e3d144...","created_at":"2026-09-07T19:25:15Z"}
{"event":"closed",    "actor":"MattGyverLee","commit_id":"066bab0e8c38569cbe04046e45d6edb3eeaf9c37","created_at":"2026-09-07T19:25:16Z"}
{"event":"referenced","actor":"MattGyverLee","commit_id":"ed428f73...","created_at":"2026-09-07T19:25:16Z"}
{"event":"referenced","actor":"MattGyverLee","commit_id":"249863d2...","created_at":"2026-09-07T19:25:16Z"}
```

The `closed` event carries `commit_id` = `066bab0` -- the commit whose body
begins `closes #242 (Checkpoint 3, T1+T2)`. The cluster of timestamps within
three seconds is the signature of a single `git push` of a batch of commits,
GitHub walking them in order. This is a keyword auto-close, not a manual one.

## 4. Could the keyword fire? Yes -- the commits are on the pushed default branch

Both preconditions hold. `066bab0` is on `main`, and `main` is fully pushed:

```
$ git branch -a --contains 066bab0
  main
* spec/242-gate-and-name-field-identity
  remotes/origin/HEAD -> origin/main
  remotes/origin/main

$ git merge-base --is-ancestor 066bab0 main        -> YES: ancestor of local main
$ git merge-base --is-ancestor 066bab0 origin/main -> YES: ancestor of origin/main

$ git rev-list --count origin/main..main
0
$ git log origin/main..main --oneline
(no output)
```

The repo's default branch is `main` (`"defaultBranchRef":{"name":"main"}`), and
`066bab0` is an ancestor of `origin/main` with zero unpushed commits. So the
"cleanest possible answer" -- commits never pushed, keyword inert -- is
**ruled out**. The keyword reached the default branch and executed.

## 5. Every cited issue number resolves in `MattGyverLee/flexicon`

The specs are **not** citing a different repository. All fifteen resolve:

| # | state | reason | title (truncated) |
|---|---|---|---|
| 242 | CLOSED | COMPLETED | Paragraph/Segment text writers silently strip whitespace |
| 243 | CLOSED | COMPLETED | Rollback destroys the non-undoable session envelope |
| 250 | **OPEN** | -- | WritingSystemOperations.Exists scans the whole store |
| 251 | CLOSED | COMPLETED | MSAOperations has no Get/ApplySyncableProperties |
| 252 | CLOSED | COMPLETED | POSOperations.GetSyncableProperties never captures Default... |
| 253 | **OPEN** | -- | PhonemeOperations.__ApplyFeatures silently skips unresolvable |
| 254 | CLOSED | COMPLETED | WfiMorphBundleOperations.GetMorphType returns the IMoForm |
| 256 | CLOSED | COMPLETED | MakeFeatStruc cannot attach to an MSA |
| 239 | MERGED | -- | feat(textswords): optional guid= on Create |
| 240 | **OPEN** | -- | flexlibs2 is still the default runtime path internally |
| 241 | MERGED | -- | Rename flexlibs2 package to flexicon |
| 22 | CLOSED | COMPLETED | TextOperations.Create accesses non-existent TextsOC |
| 175 | CLOSED | COMPLETED | Framework-wide gap: 393/411 write methods, no transaction |
| 204 | MERGED | -- | Framework-wide transaction coverage (#175) |
| 234 | CLOSED | COMPLETED | _transaction_depth incremented before __enter__ |

(#239 / #241 / #204 resolve as PRs, hence `MERGED`.)

## 6. The policy the closure violated

`specs/tier1-silent-data-loss/.crew-handoff.json`, `items_done`:

- index 1, `243-closeproject-save-guard`, issues `[243]`:
  > "flexicon#243 **deliberately left OPEN**. The crew files and closes nothing;
  > lex-lead recommends keeping it open to carry the unexplained .fwdata half
  > rather than closing and depending on a follow-up being written."
- index 2, `242-paragraph-whitespace`, issues `[242]`:
  > "flexicon#242 left as-is. The crew files and closes nothing."

Both statements are now false on GitHub.

## 7. Blast radius -- #243 is the worse case

Scanning every commit in the campaign window for GitHub closing keywords:

```
$ git log origin/main --since=2026-09-05 --format='%h|%ad|%s' --date=short   (+ per-commit body grep)
608200c 2026-09-07 [Fixes #242 ] :: fix(segment-operations): AppendSentence join boundary may insert, never delete
066bab0 2026-09-07 [closes #242 ] :: fix(paragraph-whitespace)!: preserve caller payload at four writer sites
b0e3d14 2026-09-07 [close #243 ] :: test(243): pin the SaveChanges fail-open branch; close #243's crew review (T9)
cfbfd43 2026-09-07 [Closes #254 ] :: fix(morph-bundle)!: GetMorphType returned the allomorph, not the morph type
```

`b0e3d14`'s **subject line** reads `... close #243's crew review (T9)`. The
author meant "close the crew review of #243"; GitHub's parser sees the prefix
`close #243` and closes the issue. Confirmed:

```
$ gh issue view 243 --repo MattGyverLee/flexicon --json number,state,stateReason,closedAt
{"closedAt":"2026-09-07T19:25:15Z","number":243,"state":"CLOSED","stateReason":"COMPLETED", ...}

$ gh api repos/MattGyverLee/flexicon/issues/243/timeline --jq '.[] | select(.event=="closed")'
{"actor":"MattGyverLee","created_at":"2026-09-07T19:25:15Z","commit_id":"b0e3d144eac22f651f4ac860cf4eaf6e2aae041a"}
```

This is the same failure mode the task flagged for `608200c`'s
`Fixes #242's P8 anomaly` -- a possessive `'s` after the number does **not**
protect the keyword. `b0e3d14` is the case where it actually mattered, because
#243 was closed against an explicit, reasoned recommendation to keep it open,
and its record states the unexplained `.fwdata` replacement (C10) is **not
fixed**. #243 is now marked `COMPLETED` while carrying unresolved substance.

`cfbfd43`'s `Closes #254` appears deliberate and consistent (#254 is a
straightforward fix); no concern noted.

### Note on `608200c`

`608200c` does **not** appear anywhere in #242's timeline -- the timeline holds
exactly one `closed` and four `referenced` events, none of them this commit:

```
$ gh api repos/MattGyverLee/flexicon/issues/242/timeline --jq '.[] | .event' | sort | uniq -c
      1 closed
      4 referenced
```

Because #242 was already closed by `066bab0` one second earlier in the same
push, this session **cannot determine** whether GitHub declined to parse
`Fixes #242's` or merely suppressed a redundant event on an already-closed
issue. Treat the possessive form as unsafe regardless -- `b0e3d14` proves the
pattern fires.

## 8. Was the #242 closure at least substantively right?

Partly, and this is why #242 is the lesser problem. The fix did land and was
live-verified (`066bab0` cites `run_mode: live`, 7/7 probe tests; `608200c`
cites 9/9 prediction rows). But the campaign's own record lists untouched
residuals under `not_claimed`:

> "The owner's field figures (44/104 paragraph contents, 41/86 segment
> baselines, Ejagham Mini -> Target) were NOT reproduced; Checkpoint 4 was
> DECLINED, not deferred (C13). ... The 8 sibling sites (Q-242A),
> CheckOperations' total non-str payload loss (Q-242B) and coercion policy
> (Q-242C) are untouched."

Per `next_entry`, Q-242A/B/C "sit in QUEUE.md" and were never filed as issues --
and Q-242B is characterised as "Tier-1 silent data loss on its own merits".
So closing #242 as `COMPLETED` discarded the one tracked artifact that pointed
at that unfiled work. The reporter's original field-scale claim was never
reproduced either.

## 9. Contributing cause (not an excuse)

`closes #N` is the long-standing house convention here -- a scan of all of
`origin/main` returns well over a hundred such trailers (`closes #11`,
`closes #22`, `Closes #55`, `Closes #117`, ...). The campaign's
"files and closes nothing" policy was a *local exception* to an ingrained
habit, with nothing mechanical enforcing it. That is how it slipped, twice, in
one push.

---

## RECOMMENDATION

Not "no action needed". Two things need a human, and one is a cheap safeguard
this session deliberately did not perform (read-only mandate).

### A human must do X

1. **Reopen flexicon#243** (highest priority). It was closed by keyword against
   an explicit lex-lead recommendation to keep it open, and its own record says
   the unexplained `.fwdata` half (C10) is not fixed. It currently reads
   `COMPLETED`, which is wrong on the record's own terms. Reopening restores
   the intended state; a one-line comment noting the accidental keyword close
   would prevent a future reader re-litigating it.

2. **Decide #242 deliberately** -- reopen or ratify. The fix is real and
   live-verified, so leaving it closed is defensible *if* the residuals get a
   home first. Concretely, either:
   - file Q-242A / Q-242B / Q-242C as issues (Q-242B especially -- described as
     Tier-1 silent data loss) and note Checkpoint 4 was DECLINED, then leave
     #242 closed; **or**
   - reopen #242 to carry those residuals, matching the reasoning applied to
     #243.

   The one option to avoid is leaving it closed *and* leaving Q-242A/B/C only
   in QUEUE.md -- that is the exact failure the #243 ruling warned against
   ("rather than closing and depending on a follow-up being written").

3. **Fix the `gh` remote resolution in this working copy.** Run
   `gh repo set-default MattGyverLee/flexicon`. Until then, every bare
   `gh issue` / `gh pr` command here silently queries `cdfarrow/flexlibs` and
   returns "Could not resolve" for any number above ~17 -- which already cost
   one session a wrong conclusion about whether #242 exists.

4. **Reconcile the campaign record.** The two `github` fields in
   `specs/tier1-silent-data-loss/.crew-handoff.json` assert a state that no
   longer matches GitHub. Update them to describe what actually happened once
   1 and 2 are settled.

### Prevention

The `b0e3d14` case shows prose is not safe: a keyword followed by `'s` in a
subject line still fires. Under a "close nothing" policy, the only reliable
forms are `#242` bare, or `re #242` / `refs #242` / `see #242` -- never
`close` / `fix` / `resolve` adjacent to the number in any grammatical form. A
`commit-msg` hook rejecting `(clos|fix|resolv)\w*\s+#\d+` while a campaign
policy is active would enforce mechanically what the handoff only stated in
prose.

## Undetermined / out of scope

- Whether `608200c`'s `Fixes #242's` would have fired on its own -- masked by
  `066bab0` closing #242 one second earlier in the same push (see section 7).
- Whether the substantive right answer for #242 is "reopen" or "ratify + file
  follow-ups". That is a scope judgement for the owner, not a fact this
  session can settle.
- No remediation was attempted: per the read-only mandate, no issue was
  reopened, commented on, or edited, and nothing was committed or pushed.
