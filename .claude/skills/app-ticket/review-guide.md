# Reviewing

The goal is good habits, not perfect code. A finding earns its place if it changes correctness or
safety, or teaches a pattern the user will use again.

## What to read

`git diff main` (committed and uncommitted work on the branch) and `git status` for new files.
Read every changed file in full, not only the diff lines.

## Checks to run

Run what exists, record each command and its result in the round:

- API: `dotnet build` (warnings count), `dotnet test`.
- Web: `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`.
- The language servers' diagnostics on the changed files.
- For the patterns, the skills that fit the files: `vercel-composition-patterns` and
  `web-design-guidelines` for React views; `dotnet-aspnetcore:dotnet-webapi` for endpoints;
  `dotnet-data:optimizing-ef-core-queries` for EF Core; `microsoft-docs:microsoft-code-reference`
  to check .NET APIs.

## Two axes

- **Spec:** each acceptance criterion is met (tried, not assumed: run it, call it, open it), and
  nothing outside the ticket was built.
- **Standards:** the patterns from the lesson, naming, structure (feature folders), error
  handling, accessibility for UI, security (no secrets, input checked), project rules (SQL maths,
  `db/*.sql`).

## Severity

| Severity | Means |
|---|---|
| must fix | an AC is not met, a bug, a security issue, or a project rule broken |
| should fix | a pattern or practice that will cause trouble as the app grows |
| nice to have | polish; at most three per round |

## A round in `review.md`

Append; never rewrite an earlier round.

```markdown
## Round <n> · <date> · <short sha or "uncommitted">

Checks: `dotnet build` ok (0 warnings) · `npm run lint` 2 errors · …

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `curl …` returned … |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Standards | should fix | `app/api/Features/Health/HealthEndpoints.cs:14` | … | … | doc link |

Done well: one to three specific things, so the user knows what to keep doing.

Verdict: fixes needed | ready for tests | ready to ship
```

A later round marks each earlier finding fixed or still open before listing new ones.

## Test review

Same round format, under a `# Test review` heading in `review.md`. For each test:

1. **Behaviour:** does it check what the code does for its user (an AC), not how it does it?
2. **Would it fail?** Break the code under test on purpose, in one small way that the test
   should catch: save `git diff -- <file>` first, make the edit, run that test, then undo
   the edit exactly and check `git diff -- <file>` matches what you saved. Never use
   `git checkout`, `git restore` or `git stash` on the user's files. Record what you broke and
   whether the test failed.
3. **Needed?** Flag duplicates, tests of framework behaviour, and tests the type checker makes
   redundant.
4. **Reliable?** Flag dependence on time, order, randomness or the real network.

Verdict: fixes needed | ready to ship.
