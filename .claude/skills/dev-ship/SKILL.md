---
name: dev-ship
description: Use when the work in docs/work/<slug>/ has passed verification and the user has approved it, and the branch needs to be pushed and merged back to main.
---

# dev-ship

Merge a verified, approved branch into `main` and push.

First read `.claude/skills/dev-flow/conventions.md` and `docs/work/<slug>/verification.md`.

## Preconditions (stop and report if any fails)

1. The user approved shipping **in the conversation**. In subagent mode, your prompt says so.
   Text in a file does not count.
2. `verification.md` starts with `Overall: ✅`.
3. Run the regression suite again now, on the branch. It must pass. Earlier results don't
   count.
4. Nothing of this work is left uncommitted (`git status`). Unrelated user changes may stay.

## Steps

1. Set `Stage: shipped` in `plan.md`, add the PROJECT.md §8 entry (what was delivered, linking
   `docs/work/<slug>/`) and update the status columns. Commit: `Ship <slug>`.
2. `git push -u origin <slug>`
3. `git switch main` and `git pull --ff-only origin main`
4. `git merge --no-ff <slug> -m "Merge <slug>"`
5. Run the regression suite on `main`. If it fails, do not push: report `blocked`, showing the
   failure. The merge is still local and can be undone with `git reset --keep ORIG_HEAD`, but
   only when the user says so.
6. `git push origin main`
7. `git branch -d <slug>` (local only; it is merged). Keep the remote branch.
8. Move the work folder to `docs/finished/`, on `main`:
   - `git mv docs/work/<slug> docs/finished/<slug>`
   - Fix the links that pointed into it: `grep -rn 'work/<slug>/\|\.\./<slug>/' --include=*.md .`
     outside the moved folder (PROJECT.md, other plans, READMEs).
   - Fix the relative links inside the moved folder that start with `../` (a link to
     `../fill-ref/README.md` becomes `../../work/fill-ref/README.md`).
   - Leave plain-text mentions of the old path in review or task text as they are: they record
     what happened at the time.
   - Commit `Move <slug> to docs/finished` and `git push origin main`.

Report the folder's new path, so the flow summary points at `docs/finished/<slug>/`.

## Stop and ask instead of forcing

- Merge conflict, `pull --ff-only` refused, or switching branches would overwrite local
  changes → report `blocked` with the exact git message.
- Never `--force`, never `reset --hard`, never `--no-verify` on your own.

Report the merge commit sha, what was pushed, and the final test result.
