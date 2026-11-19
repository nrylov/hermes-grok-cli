---
name: grok-cli
description: Delegate coding tasks to the Grok CLI, headless or not.
version: 0.1.0
author: Nikolai Rylov (nrylov), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coding-agent, grok, xai, headless, code-edit]
    related_skills: [coding-agents]
---

# Grok CLI

Run the `grok` binary (Grok Build, version 1.0.x tested) as a delegated coding
agent. Use it when the user asks for Grok specifically, or for a well-scoped
edit that a second coding agent should make in an isolated repo.

## When to Use

- User asks for Grok / "grok CLI" by name.
- A bounded change with clear acceptance criteria (fix a bug, add a test, refactor one module).

Do not use for vague exploration. Hermes reviews every diff before it is accepted.

## Prerequisites

- `grok --version` works (tested: `grok 1.0.89`). Binary lives at `~/.grok/bin/grok`, linked into `~/.local/bin`.
- Signed in: `grok login` (or `grok inspect` to see the config it discovers).
- Target directory is a git repo root. Grok refuses to edit outside a repo; `git init` scratch dirs first.

## Headless one-shot (preferred)

Use `terminal` with the helper, which handles JSON parsing and reports the diff:

```
terminal(command="python3 skills/grok-cli/scripts/grok_run.py /tmp/task.txt --cwd /path/to/repo --permission-mode bypassPermissions --max-turns 10")
```

Write the prompt to a file first (`write_file`), not a shell heredoc.

Or call `grok` directly:

```
grok -p "Fix add() in calc.py so it adds" --permission-mode bypassPermissions --output-format json --max-turns 5 --no-subagents
```

Output JSON fields: `text`, `stopReason`, `sessionId`, `num_turns`, `total_cost_usd`,
`usage`, `modelUsage`.

## Permission modes (verified)

| Mode | Headless result |
|---|---|
| `default`, `acceptEdits` | Edit is refused: stderr says "a headless run cannot ask for approval". The run ends with no change. |
| `bypassPermissions` | Edits applied. Use this for headless work in a scratch or worktree repo. |

Only use `bypassPermissions` inside an isolated git worktree or a scratch repo, and review the diff afterwards.

## Interactive sessions

For multi-turn work, run `grok` in tmux or a PTY (`terminal(background=true, pty=true)`) and drive it with `process(action="submit")`. Use `--always-approve` only inside an isolated worktree.

## Parallel work

```
git worktree add -b grok/task-1 /tmp/task-1 main
grok -p "$(cat /tmp/task-1.txt)" --cwd /tmp/task-1 --permission-mode bypassPermissions --output-format json --max-turns 10 --no-subagents
```

## Verification (always)

1. `git diff --stat` in the repo; confirm only the intended files changed.
2. Run the project's tests yourself. Do not trust Grok's claim that tests pass.
3. Read the diff before committing or merging.

## Pitfalls

- Default permission mode does not edit in headless runs. Silent no-op: exit 0, `stopReason: cancelled`, file unchanged. Check the diff.
- `--output-format json` is the only machine-readable option. Parse `stopReason`; `cancelled` means the run did not finish.
- Each headless run costs money (about $0.03 to $0.07 per small fix in testing). Set `--max-turns`.
- A shell-style prompt containing `-e` or `-c` may trigger approval prompts. Use `--prompt-file` for long prompts.
- `grok agent` is a separate subcommand; `grok -p` is the headless path used here.
- `agent` in `~/.local/bin` is a symlink to the same Grok binary, not Cursor's CLI.
