#!/usr/bin/env python3
# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.
"""Run every agent example against a live Agentspan server and report status.

"Works fine" means:
  * PASS  — process exits 0 within the timeout (no compile/import/runtime error,
            no hang).
  * ERROR — non-zero exit: import/compile error, traceback, AgentAPIError,
            SpawnSafetyError, etc.
  * HUNG  — did not finish within the per-example timeout (a stuck/never-ending
            agent). The whole process group is killed so spawned tool workers
            don't linger.
  * SKIP  — deliberately not run: interactive (reads stdin), a long-running
            daemon by design (serve / schedule-forever / kafka / dashboard), or
            requires external infra we don't provide (MCP server, Docker,
            Jupyter, Slack, non-configured LLM provider).

Runs up to N examples concurrently (default 4). Emits an ASCII table to stdout
and a color-coded HTML report.

Usage:
    python run_all_examples.py [--jobs 4] [--timeout 180] [--dry-run] \
        [--only PATTERN] [--out report.html]

Env (with sensible defaults for the local dev server on :6767):
    CONDUCTOR_SERVER_URL / AGENTSPAN_SERVER_URL  server API base
    AGENTSPAN_LLM_MODEL                          model steered to a working provider
"""
from __future__ import annotations

import argparse
import concurrent.futures
import html
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]  # examples/agents -> examples -> repo root

DEFAULT_SERVER = "http://localhost:6767/api"
DEFAULT_MODEL = "openai/gpt-4o-mini"

# ── Skip lists (judgment) ────────────────────────────────────────────────
# Long-running by design or interactive — would legitimately never terminate.
DAEMON_SKIP = {
    "12_long_running.py": "long-running by design",
    "63b_serve.py": "serve() worker daemon (blocks forever)",
    "63d_serve_from_package.py": "serve() worker daemon (blocks forever)",
    "63e_run_monitoring.py": "live monitoring loop",
    "77_kafka_consumer_agent.py": "kafka consumer daemon (+ needs Kafka)",
    "79_agent_message_bus.py": "message-bus daemon",
    "80_live_dashboard.py": "interactive live dashboard",
    "81_chat_repl.py": "interactive REPL",
    "82b_coding_agent_tui.py": "interactive TUI",
    "hello_world_every_second.py": "schedules every 1s + polls forever",
    "72_client_reconnect.py": "reconnect demo: run_once waits for a manual approval/resume flow",
}
# Require external infra / providers not available in this environment.
INFRA_SKIP = {
    "04_mcp_weather.py": "needs an MCP server",
    "04_http_and_mcp_tools.py": "needs an MCP server",
    "16f_credentials_mcp_tool.py": "needs an MCP server",
    "107_pac_mcp_proof.py": "needs an MCP server",
    "39a_docker_code_execution.py": "needs Docker",
    "39b_jupyter_code_execution.py": "needs a Jupyter kernel",
    "39c_serverless_code_execution.py": "needs a serverless code sandbox",
    "91_slack_autofix_agent.py": "needs Slack + webhook",
    "16k_credentials_google_adk.py": "needs Google ADK / Gemini creds",
    "16f_credentials_mcp_tool.py": "needs an MCP server",
    "97_openai_runner_sandbox.py": "needs a Docker sandbox",
    "61a_github_coding_agent_claude_code.py": "needs the claude-code-sdk package",
    "116_ocg_subagent.py": "needs an OCG instance (OCG_INSTANCE_URL)",
    "117_ocg_direct_tools.py": "needs an OCG instance (OCG_INSTANCE_URL)",
    "100_issue_fixer_agent.py": "requires CLI arguments",
    "70_ce_support_agent.py": "requires CLI arguments (ticket id)",
    "33_external_workers.py": "needs external worker processes (referenced via @tool(external=True))",
    "61_github_coding_agent_chained.py": "needs GitHub + an external trigger from another terminal",
    "63c_run_by_name.py": "needs 63b_serve.py workers running in another terminal",
}
# Not examples (helpers, tests, utilities).
NOT_EXAMPLES = {
    "run_all_examples.py",
    "settings.py",
    "kitchen_sink_helpers.py",
    "dump_agent_configs.py",
    "testing_multi_agent_correctness.py",
    "_issue_fixer_tools.py",
    "_issue_fixer_instructions.py",
}

STATUS_ORDER = {"ERROR": 0, "HUNG": 1, "PASS": 2, "SKIP": 3}


@dataclass
class Result:
    name: str
    status: str  # PASS | ERROR | HUNG | SKIP
    duration: float
    detail: str = ""


def discover() -> list[Path]:
    files = []
    for p in sorted(HERE.glob("*.py")):
        if p.name in NOT_EXAMPLES or p.name.startswith("_") or p.name.startswith("test_"):
            continue
        files.append(p)
    return files


def classify_skip(path: Path) -> str | None:
    if path.name in DAEMON_SKIP:
        return DAEMON_SKIP[path.name]
    if path.name in INFRA_SKIP:
        return INFRA_SKIP[path.name]
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        src = ""
    # Interactive: reads from stdin at runtime.
    if re.search(r"(?<![\w.])input\s*\(", src):
        return "interactive (reads stdin)"
    return None


_ERR_RE = re.compile(
    r"^(?:\w[\w.]*(?:Error|Exception|Failure)|Traceback \(most recent call last\)):?.*",
)


def extract_error(output: str) -> str:
    """Return a short signature of the failure from captured output."""
    lines = [ln.rstrip() for ln in output.splitlines() if ln.strip()]
    # Prefer the last "SomethingError: msg" line (the actual raised exception).
    for ln in reversed(lines):
        m = re.match(r"^([\w.]*(?:Error|Exception|Failure))\b:?\s*(.*)$", ln.strip())
        if m:
            return (ln.strip())[:200]
    # Fall back to the last non-empty line.
    return (lines[-1][:200] if lines else "non-zero exit, no output")


def run_one(path: Path, env: dict, timeout: int) -> Result:
    skip = classify_skip(path)
    if skip:
        return Result(path.name, "SKIP", 0.0, skip)

    start = time.monotonic()
    try:
        proc = subprocess.Popen(
            [sys.executable, str(path)],
            cwd=str(HERE),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,  # own process group -> kill children on timeout
        )
    except Exception as e:  # pragma: no cover
        return Result(path.name, "ERROR", 0.0, f"launch failed: {e}")

    try:
        out, _ = proc.communicate(timeout=timeout)
        dur = time.monotonic() - start
        if proc.returncode == 0:
            return Result(path.name, "PASS", dur)
        return Result(path.name, "ERROR", dur, extract_error(out or ""))
    except subprocess.TimeoutExpired:
        dur = time.monotonic() - start
        # Kill the whole process group (agent + spawned tool workers).
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass
        try:
            proc.communicate(timeout=10)
        except Exception:
            pass
        return Result(path.name, "HUNG", dur, f"no exit within {timeout}s")


def write_html(results: list[Result], out: Path, meta: dict) -> None:
    counts = {s: sum(1 for r in results if r.status == s) for s in ("PASS", "ERROR", "HUNG", "SKIP")}
    colors = {"PASS": "#1a7f37", "ERROR": "#cf222e", "HUNG": "#bc4c00", "SKIP": "#57606a"}
    bg = {"PASS": "#eaf6ec", "ERROR": "#ffebe9", "HUNG": "#fff1e5", "SKIP": "#f6f8fa"}
    rows = []
    for r in sorted(results, key=lambda r: (STATUS_ORDER[r.status], r.name)):
        rows.append(
            f'<tr style="background:{bg[r.status]}">'
            f'<td class="mono">{html.escape(r.name)}</td>'
            f'<td><span class="badge" style="background:{colors[r.status]}">{r.status}</span></td>'
            f'<td class="num">{r.duration:.1f}s</td>'
            f'<td class="mono detail">{html.escape(r.detail)}</td></tr>'
        )
    total = len(results)
    summary = " · ".join(
        f'<span class="pill" style="border-color:{colors[s]};color:{colors[s]}">{s}: {counts[s]}</span>'
        for s in ("PASS", "ERROR", "HUNG", "SKIP")
    )
    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Agent examples — run report</title>
<style>
 body{{font:14px -apple-system,Segoe UI,Roboto,sans-serif;margin:24px;color:#1f2328}}
 h1{{font-size:20px;margin:0 0 4px}} .meta{{color:#57606a;margin-bottom:14px}}
 .pill{{border:1px solid;border-radius:999px;padding:2px 10px;margin-right:6px;font-weight:600}}
 table{{border-collapse:collapse;width:100%;margin-top:14px}}
 th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid #d0d7de}}
 th{{font-size:12px;text-transform:uppercase;color:#57606a}}
 .mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}
 .num{{text-align:right;white-space:nowrap}} .detail{{color:#57606a;font-size:12px}}
 .badge{{color:#fff;border-radius:6px;padding:1px 8px;font-size:12px;font-weight:700}}
</style></head><body>
<h1>Agent examples — run report</h1>
<div class="meta">{html.escape(meta['when'])} · server <span class="mono">{html.escape(meta['server'])}</span>
 · model <span class="mono">{html.escape(meta['model'])}</span>
 · jobs {meta['jobs']} · timeout {meta['timeout']}s · {total} examples · {meta['wall']:.0f}s wall</div>
<div>{summary}</div>
<table><thead><tr><th>Example</th><th>Status</th><th>Duration</th><th>Detail</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body></html>"""
    out.write_text(doc, encoding="utf-8")


def print_table(results: list[Result]) -> None:
    width = max((len(r.name) for r in results), default=20)
    print(f"\n{'EXAMPLE':<{width}}  {'STATUS':<6}  {'DUR':>7}  DETAIL")
    print("-" * (width + 40))
    for r in sorted(results, key=lambda r: (STATUS_ORDER[r.status], r.name)):
        print(f"{r.name:<{width}}  {r.status:<6}  {r.duration:>6.1f}s  {r.detail[:70]}")
    counts = {s: sum(1 for r in results if r.status == s) for s in ("PASS", "ERROR", "HUNG", "SKIP")}
    print("-" * (width + 40))
    print(f"TOTAL {len(results)}  |  " + "  ".join(f"{s}={counts[s]}" for s in ("PASS", "ERROR", "HUNG", "SKIP")))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default=None, help="substring filter on filename")
    ap.add_argument("--out", default=str(HERE / "run_report.html"))
    args = ap.parse_args()

    server = os.environ.get("CONDUCTOR_SERVER_URL") or os.environ.get("AGENTSPAN_SERVER_URL") or DEFAULT_SERVER
    model = os.environ.get("AGENTSPAN_LLM_MODEL", DEFAULT_MODEL)

    env = dict(os.environ)
    env["CONDUCTOR_SERVER_URL"] = server
    env["AGENTSPAN_SERVER_URL"] = server
    env["AGENTSPAN_LLM_MODEL"] = model
    env["PYTHONPATH"] = os.pathsep.join([str(REPO / "src"), str(HERE), env.get("PYTHONPATH", "")])
    env["PYTHONUNBUFFERED"] = "1"

    examples = discover()
    if args.only:
        examples = [p for p in examples if args.only in p.name]

    if args.dry_run:
        run, skip = [], []
        for p in examples:
            s = classify_skip(p)
            (skip if s else run).append((p.name, s))
        print(f"WOULD RUN ({len(run)}):")
        for n, _ in run:
            print(f"  run   {n}")
        print(f"\nWOULD SKIP ({len(skip)}):")
        for n, why in skip:
            print(f"  skip  {n:<40} {why}")
        return 0

    print(f"Running {len(examples)} examples · jobs={args.jobs} · timeout={args.timeout}s · server={server} · model={model}")
    wall_start = time.monotonic()
    results: list[Result] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(run_one, p, env, args.timeout): p for p in examples}
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            results.append(r)
            done += 1
            print(f"[{done}/{len(examples)}] {r.status:<6} {r.name} ({r.duration:.0f}s) {r.detail[:60]}")

    wall = time.monotonic() - wall_start
    print_table(results)
    meta = {
        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        "server": server, "model": model, "jobs": args.jobs,
        "timeout": args.timeout, "wall": wall,
    }
    out = Path(args.out)
    write_html(results, out, meta)
    print(f"\nHTML report: {out}")
    # Exit non-zero if anything genuinely failed or hung.
    bad = sum(1 for r in results if r.status in ("ERROR", "HUNG"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
