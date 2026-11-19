# hermes-grok-cli

[![ci](https://github.com/nrylov/hermes-grok-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/nrylov/hermes-grok-cli/actions/workflows/ci.yml)

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill for delegating coding
tasks to the Grok CLI (`grok`), with a stdlib helper that runs one headless task and
reports the result and git diff.

| Skill | What it does | Helper |
|---|---|---|
| [`grok-cli`](skills/grok-cli) | Headless and interactive Grok coding sessions, diff review | `grok_run.py` (stdlib) |

## Install

```bash
cp -r skills/grok-cli ~/.hermes/skills/autonomous-ai-agents/
```

## Try it

```bash
python3 -m unittest discover tests -v
python3 scripts/validate_skills.py
```

## Requirements

- `grok` CLI on PATH (tested with 1.0.89) and signed in.
- Target directory must be a git repo.

## Safety

The helper defaults to `acceptEdits`, which does not edit in headless mode. Use
`bypassPermissions` only in an isolated worktree or scratch repo.

MIT licensed.
