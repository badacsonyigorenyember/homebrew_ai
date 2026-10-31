# Claude Code setup for the app only

Skills in `app/.claude/skills/` are offered to Claude only while it works on files under `app/`,
so they never trigger on the recipe workflow (n8n, SQL, Python).

| Skill | Source | Path in source | Hash when copied (2026-10-31) |
|---|---|---|---|
| `vercel-composition-patterns` | `vercel-labs/agent-skills` | `skills/composition-patterns/SKILL.md` | `575757e3e25761c8c562d6e395d29f0b76c98b1273c0bd72d88e6ab1bc9c7d42` |
| `web-design-guidelines` | `vercel-labs/agent-skills` | `skills/web-design-guidelines/SKILL.md` | `f3bc47f890f42a44db1007ab390709ec368e4b8c089baee6b0007182236ac474` |

They are not in the root `skills-lock.json` on purpose: `npx skills` restores and updates into the
root `.claude/skills/`, where they would apply to the whole repo. To update one, install it again
with `npx skills add vercel-labs/agent-skills -s <name> -a claude-code -y`, move the folder from
`.claude/skills/` to here, and revert the change it makes to `skills-lock.json`.

`web-design-guidelines` downloads its rules from
`raw.githubusercontent.com/vercel-labs/web-interface-guidelines` each time it runs; that content is
not kept in this repo.

Plugins cannot be limited to a folder, so the app's plugins are enabled for the whole project in
the root `.claude/settings.json`: `typescript-lsp`, `csharp-lsp`, `microsoft-docs`,
`dotnet-aspnetcore`, `dotnet-data` and `dotnet-ai`. Their skills only match TypeScript or .NET
work. `dotnet-test` is installed but disabled, because its skills claim all test work, pytest
included; enable it only for an app testing session and disable it afterwards:

```bash
claude plugin enable dotnet-test@dotnet-agent-skills --scope project
```
