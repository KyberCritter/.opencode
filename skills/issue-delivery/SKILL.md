---
name: issue-delivery
description: 'Use when asked to resolve, implement, or fix a GitHub issue by number or URL. Fetches the issue title, body, comments, metadata, and linked items from the current repository, then implements it on a new branch in an isolated worktree, commits and pushes incrementally, and opens a pull request containing Closes #<issue>.'
---

# Issue Delivery

Deliver one GitHub issue end to end: understand it fully, implement it on an isolated
branch, push as you go, and open a PR that closes it.

**Definition of done:** the branch is pushed, the PR is open against the repository's
default branch, and the PR body contains the exact phrase `Closes #<N>` on its own line.
Do not merge the PR, close the issue manually, or rewrite pushed history.

## 1. Resolve the issue and repository

Accept a bare number (`42`), `#42`, or a full issue URL. If the target is ambiguous, ask
before doing work.

```powershell
gh repo view --json nameWithOwner,defaultBranchRef
```

Then fetch the issue with every field that can carry requirements or linkage:

```powershell
gh issue view 42 --json number,title,state,stateReason,url,author,labels,assignees,milestone,issueType,parent,subIssues,subIssuesSummary,blockedBy,blocking,closedByPullRequestsReferences,projectItems,body
gh issue view 42 --comments
```

Read the **entire** body and every comment. Comments routinely contain scope changes,
reproduction steps, and decisions that contradict the original body.

Then pull the timeline and any linked work:

```powershell
gh api --paginate "repos/{owner}/{repo}/issues/42/timeline"
```

- Follow cross-references to related issues, PRs, discussions, and external docs.
- Read parent, sub-issues, `blockedBy`, and `blocking` entries when present.
- If `closedByPullRequestsReferences` contains an open PR, do not duplicate the work;
  report it and ask whether to take over or review it.
- If the issue is already closed, stop and report unless the user wants a follow-up change.

Also read the repository's working agreements before editing: `AGENTS.md`, `CLAUDE.md`,
`README`, `CONTRIBUTING`, `docs/`, test instructions, and any PR template.

## 2. Create the branch and worktree

Never implement in a checkout that has uncommitted user changes, and never stash, reset,
or discard those changes. Use a sibling worktree so the primary checkout stays untouched.

```powershell
git fetch origin
$root = git rev-parse --show-toplevel
$repo = Split-Path -Leaf $root
$base = gh repo view --json defaultBranchRef --jq .defaultBranchRef.name
$slug = "42-short-kebab-summary"        # derive from the issue title
$branch = "issue/$slug"
$path = Join-Path (Split-Path -Parent $root) "$repo-issue-42"

git worktree add -b $branch $path "origin/$base"
```

- Keep the slug short and lowercase (`issue/42-printer-power-switch`).
- If the local branch already exists, inspect it instead of resetting it.
- If the remote branch exists, fetch it and check for an open PR; continue that PR rather
  than creating a competing branch.
- If the harness provides a worktree tool, prefer it, then move the session into the
  returned directory and rename the branch to the convention above if needed.
- Confirm the new worktree is clean and based on the default branch before editing.

## 3. Plan against acceptance criteria

Write a short checklist from the title, body, comments, and linked items: expected
behavior, edge cases, and what must not regress. Locate the relevant code, reproduce the
bug or observe the current behavior, and trace the affected call paths.

If a requirement is genuinely ambiguous or needs a product decision, ask now. Do not
invent scope that the issue does not request.

## 4. Implement in reviewable commits

Make focused changes that follow the surrounding structure, naming, and style. After each
coherent unit:

1. Run the most relevant tests, lint, typecheck, or build.
2. Commit with an imperative subject, for example
   `fix(printer): allow power switch to toggle (refs #42)`.
3. Push the first commit with `git push -u origin HEAD`; push again after later commits.

Keep the issue reference in commit messages as `refs #42`. Reserve `Closes #42` for the PR
body so the issue closes exactly once, when the PR merges.

Do not amend, rebase, or force-push after review has started unless the user explicitly
approves.

## 5. Verify the delivered behavior

- Run the full relevant test suite and production build from the worktree.
- Test the actual acceptance criteria, including the edge cases from step 3. Passing tests
  alone are not proof.
- Review the complete diff against the base: `git diff --stat origin/$base...HEAD`.
- Confirm no secrets, debug output, generated artifacts, or unrelated formatting changes
  are included.
- Confirm the worktree is clean: `git status --short`.

## 6. Open the pull request

Push the final state, then create the PR with a body file or stdin. When the repository has
a PR template, preserve its headings and add the closing line to it.

```powershell
gh pr create --base $base --head $branch --title "Allow the printer power switch to toggle" --body @"
## Summary

Implements the requested behavior from #42.

## Changes

- ...

## Testing

- `npm test`
- Manually verified ...

Closes #42
"@
```

- The PR title should describe the user-visible outcome, not just repeat the issue number.
- Summarize the approach, call out tradeoffs or follow-ups, and list the commands you ran.
- Link related issues or PRs mentioned in the issue.
- If the change is incomplete or needs review before merge, open it with `--draft` and say
  so; never claim it closes the issue if the acceptance criteria are not met.
- Return the PR URL and confirm which issue it closes.

## Guardrails

- One issue per branch and PR unless the issue explicitly requires a combined change.
- Do not commit or push unrelated changes from the primary checkout.
- Do not delete a worktree that contains uncommitted work.
- If blocked by permissions, missing credentials, failing infrastructure, or an unanswered
  product question, push safe progress, report the exact blocker, and ask for direction.
- Never use `Closes` in a commit message or close the issue by hand; the PR body is the
  single source of the closing link.
