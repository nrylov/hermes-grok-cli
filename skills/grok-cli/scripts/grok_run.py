#!/usr/bin/env python3
"""Run one headless Grok CLI task and print a compact JSON summary.

Stdlib only; written for Python 3.9+. Wraps `grok -p ... --output-format json`
so the calling agent gets stopReason, text, turns, cost and a git diff stat
instead of raw transcript output.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

PERMISSION_MODES = ["default", "acceptEdits", "auto", "dontAsk", "bypassPermissions", "plan"]


def build_command(prompt, permission_mode, max_turns, model=None):
    cmd = ["grok", "-p", prompt, "--output-format", "json",
           "--permission-mode", permission_mode, "--no-subagents"]
    if max_turns:
        cmd += ["--max-turns", str(max_turns)]
    if model:
        cmd += ["-m", model]
    return cmd


def summarize(raw_stdout):
    """Reduce grok's JSON output to the fields an orchestrating agent needs."""
    data = json.loads(raw_stdout)
    usage = data.get("usage", {}) or {}
    return {
        "text": data.get("text", ""),
        "stop_reason": data.get("stopReason"),
        "session_id": data.get("sessionId"),
        "num_turns": data.get("num_turns"),
        "total_cost_usd": data.get("total_cost_usd"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
    }


def git_diff_stat(cwd):
    try:
        out = subprocess.run(["git", "-C", cwd, "diff", "--stat"], capture_output=True,
                             text=True, timeout=30)
        untracked = subprocess.run(["git", "-C", cwd, "ls-files", "--others", "--exclude-standard"],
                                   capture_output=True, text=True, timeout=30)
        return {"diff_stat": out.stdout.strip(),
                "untracked": [l for l in untracked.stdout.splitlines() if l]}
    except (OSError, subprocess.SubprocessError):
        return {"diff_stat": None, "untracked": []}


def run(prompt, cwd, permission_mode="acceptEdits", max_turns=10, timeout=600, model=None):
    if not shutil.which("grok"):
        return {"ok": False, "error": "grok binary not found on PATH"}
    if not os.path.isdir(os.path.join(cwd, ".git")):
        return {"ok": False, "error": "cwd is not a git repo root: %s" % cwd}
    cmd = build_command(prompt, permission_mode, max_turns, model)
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timed out after %ss" % timeout}
    result = {"ok": False, "exit_code": proc.returncode,
              "stderr_tail": proc.stderr.strip().splitlines()[-3:]}
    try:
        result.update(summarize(proc.stdout))
        # A run that was cancelled (e.g. a blocked edit) still exits 0; only end_turn is success.
        result["ok"] = proc.returncode == 0 and result.get("stop_reason") == "end_turn"
    except ValueError:
        result["error"] = "could not parse grok JSON output"
        result["raw_tail"] = proc.stdout[-500:]
    result.update(git_diff_stat(cwd))
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("prompt_file", help="file containing the task prompt")
    p.add_argument("--cwd", required=True, help="git repo root to work in")
    p.add_argument("--permission-mode", default="acceptEdits", choices=PERMISSION_MODES)
    p.add_argument("--max-turns", type=int, default=10)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--model")
    args = p.parse_args(argv)
    with open(args.prompt_file) as f:
        prompt = f.read().strip()
    result = run(prompt, os.path.abspath(args.cwd), args.permission_mode,
                 args.max_turns, args.timeout, args.model)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
