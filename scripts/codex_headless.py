#!/usr/bin/env python3
"""Run OpenAI Codex (codex CLI) reliably on macOS.

Default mode is *auto*:
- If --mode interactive is specified, start a session in tmux.
- Otherwise run headless (codex exec) through macOS BSD `script(1)` for a pseudo-terminal.

Why this wrapper exists:
- Codex can hang when run without a TTY in some environments.
- CI / automation environments are often non-interactive.
- macOS BSD `script` has different syntax from Linux GNU `script`.

macOS-specific features:
- BSD `script -q /dev/null cmd args...` (not Linux `script -q -c "cmd" /dev/null`)
- Desktop notifications via osascript
- Clipboard integration via pbcopy / pbpaste
- $TMPDIR for temp files (not /tmp)

Docs: https://github.com/openai/codex
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_CODEX = os.environ.get("CODEX_BIN", "")
DEFAULT_LOG_DIR = os.path.expanduser("~/.claude/logs/headless")


def is_inside_git_repo(path: str | None = None) -> bool:
    """Check if the given path (or cwd) is inside a Git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path or os.getcwd(),
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def which(name: str) -> str | None:
    """Find an executable on PATH."""
    for p in os.environ.get("PATH", "").split(":"):
        cand = Path(p) / name
        try:
            if cand.is_file() and os.access(cand, os.X_OK):
                return str(cand)
        except OSError:
            pass
    return None


def resolve_codex_bin(explicit: str) -> str | None:
    """Resolve the codex binary path."""
    if explicit and Path(explicit).exists():
        return explicit
    # Try common locations
    for name in ("codex",):
        found = which(name)
        if found:
            return found
    # Try npx as fallback
    npx = which("npx")
    if npx:
        return npx  # Will need special handling
    return None


def notify_macos(title: str, message: str) -> None:
    """Send a macOS desktop notification via osascript."""
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
    except Exception:
        pass


def copy_to_clipboard(text: str) -> None:
    """Copy text to macOS clipboard via pbcopy."""
    try:
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        proc.communicate(input=text.encode("utf-8"), timeout=5)
    except Exception:
        pass


def build_headless_cmd(args: argparse.Namespace) -> list[str]:
    """Build the codex exec command for headless mode."""
    cmd: list[str] = [args.codex_bin, "exec"]

    if args.model:
        cmd += ["-m", args.model]
    if args.sandbox:
        cmd += ["--sandbox", args.sandbox]
    if args.full_auto:
        cmd.append("--full-auto")
    if args.profile:
        cmd += ["-p", args.profile]
    if args.cd:
        cmd += ["--cd", args.cd]
    if args.image:
        for img in args.image:
            cmd += ["-i", img]
    if args.json_output:
        cmd.append("--json")
    if args.output_file:
        cmd += ["-o", args.output_file]
    if args.output_schema:
        cmd += ["--output-schema", args.output_schema]
    if args.ephemeral:
        cmd.append("--ephemeral")
    if args.skip_git_repo_check:
        cmd.append("--skip-git-repo-check")
    if args.add_dir:
        for d in args.add_dir:
            cmd += ["--add-dir", d]
    if args.yolo:
        cmd.append("--yolo")
    if args.oss:
        cmd.append("--oss")
    if args.local_provider:
        cmd += ["--local-provider", args.local_provider]
    if args.color:
        cmd += ["--color", args.color]
    if args.extra:
        cmd += args.extra

    # Prompt goes last as positional argument
    if args.prompt:
        cmd.append(args.prompt)

    return cmd


def run_background(cmd: list[str], cwd: str | None, log_dir: str, notify: bool = False) -> int:
    """Run a command in the background (non-blocking), returning immediately.

    Writes stdout/stderr to a timestamped log file and prints the PID
    and log path so the caller can monitor progress later.
    """
    os.makedirs(log_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(log_dir, f"codex-{timestamp}.log")

    with open(log_file, "w") as lf:
        lf.write(f"# Command: {' '.join(shlex.quote(c) for c in cmd)}\n")
        lf.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        lf.write(f"# CWD: {cwd or os.getcwd()}\n\n")
        lf.flush()

        script_bin = which("script")
        if script_bin:
            full_cmd = [script_bin, "-q", "/dev/null"] + cmd
        else:
            full_cmd = cmd

        proc = subprocess.Popen(
            full_cmd,
            cwd=cwd,
            stdout=lf,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    print(f"Background process started:")
    print(f"  PID:  {proc.pid}")
    print(f"  Log:  {log_file}")
    print(f"  Tail: tail -f {shlex.quote(log_file)}")
    print(f"  Stop: kill {proc.pid}")

    if notify:
        watcher_script = (
            f"while kill -0 {proc.pid} 2>/dev/null; do sleep 2; done; "
            f"osascript -e 'display notification \"Background task finished (PID {proc.pid})\" "
            f"with title \"Codex\"'"
        )
        subprocess.Popen(
            ["bash", "-c", watcher_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    return 0


def run_with_pty(cmd: list[str], cwd: str | None) -> int:
    """Run a command with a pseudo-terminal via macOS BSD script(1).

    macOS syntax:  script -q /dev/null cmd arg1 arg2 ...
    Linux syntax:  script -q -c "cmd arg1 arg2" /dev/null  (DO NOT use on macOS)
    """
    script_bin = which("script")
    if not script_bin:
        # Fallback: run directly without PTY
        proc = subprocess.run(cmd, cwd=cwd)
        return proc.returncode

    # macOS BSD: script -q /dev/null <command> [args...]
    full_cmd = [script_bin, "-q", "/dev/null"] + cmd
    proc = subprocess.run(full_cmd, cwd=cwd)
    return proc.returncode


# --- tmux interactive mode ---

def tmux_cmd(*args: str) -> list[str]:
    """Build a tmux command."""
    return ["tmux", *args]


def tmux_capture(target: str, lines: int = 200) -> str:
    """Capture tmux pane content."""
    return subprocess.check_output(
        tmux_cmd("capture-pane", "-p", "-J", "-t", target, "-S", f"-{lines}"),
        text=True,
    )


def tmux_wait_for_text(
    target: str, pattern: str, timeout_s: int = 30, poll_s: float = 0.5
) -> bool:
    """Wait for text to appear in a tmux pane."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            buf = tmux_capture(target, lines=200)
            if pattern in buf:
                return True
        except subprocess.CalledProcessError:
            pass
        time.sleep(poll_s)
    return False


def run_interactive_tmux(args: argparse.Namespace) -> int:
    """Start Codex interactively inside a tmux session."""
    if not which("tmux"):
        print("Error: tmux not found. Install via: brew install tmux", file=sys.stderr)
        return 2

    session = args.tmux_session
    target = f"{session}:0.0"

    # Kill existing session if any
    subprocess.run(
        tmux_cmd("kill-session", "-t", session),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(tmux_cmd("new", "-d", "-s", session, "-n", "codex"))

    cwd = args.cd or os.getcwd()

    # Build the codex launch command (interactive TUI, not exec)
    codex_parts = [args.codex_bin]
    if args.model:
        codex_parts += ["-m", args.model]
    if args.sandbox:
        codex_parts += ["--sandbox", args.sandbox]
    if args.full_auto:
        codex_parts.append("--full-auto")
    if args.profile:
        codex_parts += ["-p", args.profile]
    if args.extra:
        codex_parts += args.extra

    launch = f"cd {shlex.quote(cwd)} && " + " ".join(
        shlex.quote(p) for p in codex_parts
    )
    subprocess.check_call(
        tmux_cmd("send-keys", "-t", target, "-l", "--", launch)
    )
    subprocess.check_call(tmux_cmd("send-keys", "-t", target, "Enter"))

    # Wait for codex to be ready, then send prompt
    time.sleep(3)

    if args.prompt:
        for line in (ln for ln in args.prompt.splitlines() if ln.strip()):
            subprocess.check_call(
                tmux_cmd("send-keys", "-t", target, "-l", "--", line)
            )
            subprocess.check_call(tmux_cmd("send-keys", "-t", target, "Enter"))
            time.sleep(args.interactive_send_delay_ms / 1000.0)

    print(f"Interactive Codex started in tmux session: {session}")
    print(f"  Attach:   tmux attach -t {shlex.quote(session)}")
    print(f"  Snapshot: tmux capture-pane -p -J -t {shlex.quote(target)} -S -200")

    # Optional: wait and snapshot
    if args.interactive_wait_s > 0:
        time.sleep(args.interactive_wait_s)
        try:
            snap = tmux_capture(target, lines=200)
            print("\n--- tmux snapshot (last 200 lines) ---\n")
            print(snap)
        except subprocess.CalledProcessError:
            pass

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run OpenAI Codex reliably on macOS (headless or interactive via tmux)"
    )

    ap.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Prompt text for codex exec.",
    )
    ap.add_argument(
        "--mode",
        choices=["headless", "interactive"],
        default="headless",
        help="Execution mode. 'headless' uses codex exec, 'interactive' uses tmux.",
    )
    ap.add_argument(
        "-m", "--model",
        default=None,
        help="Model to use (e.g. o4-mini, codex-mini-latest)",
    )
    ap.add_argument(
        "-s", "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access"],
        default=None,
        help="Sandbox policy for shell commands",
    )
    ap.add_argument(
        "--full-auto",
        action="store_true",
        help="Convenience: auto-approve + workspace-write sandbox",
    )
    ap.add_argument(
        "-p", "--profile",
        default=None,
        help="Configuration profile from config.toml",
    )
    ap.add_argument(
        "--cd", "-C",
        default=None,
        help="Working directory for the agent",
    )
    ap.add_argument(
        "-i", "--image",
        action="append",
        default=None,
        help="Attach image(s) to the initial prompt (can be repeated)",
    )
    ap.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print events to stdout as JSONL",
    )
    ap.add_argument(
        "-o", "--output-file",
        default=None,
        help="Write last agent message to this file",
    )
    ap.add_argument(
        "--output-schema",
        default=None,
        help="Path to JSON Schema for structured final response",
    )
    ap.add_argument(
        "--ephemeral",
        action="store_true",
        help="Run without persisting session files",
    )
    ap.add_argument(
        "--skip-git-repo-check",
        action="store_true",
        help="Allow running outside a Git repository",
    )
    ap.add_argument(
        "--add-dir",
        action="append",
        default=None,
        help="Additional writable directories (can be repeated)",
    )
    ap.add_argument(
        "--yolo",
        action="store_true",
        help="Skip all prompts and sandboxing (use with extreme caution)",
    )
    ap.add_argument(
        "--oss",
        action="store_true",
        help="Use an open-source provider",
    )
    ap.add_argument(
        "--local-provider",
        default=None,
        choices=["lmstudio", "ollama"],
        help="Local provider to use",
    )
    ap.add_argument(
        "--color",
        default=None,
        help="Color settings for output",
    )
    # background options
    ap.add_argument(
        "--background", "--bg",
        action="store_true",
        help="Run in background (non-blocking). Returns immediately with PID and log path.",
    )
    ap.add_argument(
        "--log-dir",
        default=DEFAULT_LOG_DIR,
        help=f"Directory for background log files (default: {DEFAULT_LOG_DIR})",
    )

    ap.add_argument(
        "--codex-bin",
        default=DEFAULT_CODEX,
        help="Path to codex binary. Or set CODEX_BIN env var.",
    )
    ap.add_argument(
        "--notify",
        action="store_true",
        help="Send a macOS desktop notification on completion",
    )
    ap.add_argument(
        "--clipboard",
        action="store_true",
        help="Copy output to macOS clipboard via pbcopy",
    )

    # tmux options
    ap.add_argument("--tmux-session", default="codex", help="tmux session name")
    ap.add_argument(
        "--interactive-wait-s",
        type=int,
        default=0,
        help="Wait N seconds then print a tmux output snapshot",
    )
    ap.add_argument(
        "--interactive-send-delay-ms",
        type=int,
        default=800,
        help="Delay (ms) between sending lines in interactive mode",
    )

    ap.add_argument("extra", nargs=argparse.REMAINDER, help="Extra args passed to codex (after --)")

    args = ap.parse_args()

    # Strip leading '--' from extra args
    extra = args.extra
    if extra and extra[0] == "--":
        extra = extra[1:]
    args.extra = extra

    # Resolve codex binary
    resolved = resolve_codex_bin(args.codex_bin)
    if not resolved:
        print("Error: codex binary not found.", file=sys.stderr)
        print("Install: npm install -g @openai/codex", file=sys.stderr)
        print("Or set CODEX_BIN=/path/to/codex", file=sys.stderr)
        return 2
    args.codex_bin = resolved

    # Auto-detect: if not in a git repo, automatically add --skip-git-repo-check
    workdir = args.cd or os.getcwd()
    if not args.skip_git_repo_check and not is_inside_git_repo(workdir):
        print(
            f"Note: {workdir} is not a Git repository. "
            "Automatically adding --skip-git-repo-check.",
            file=sys.stderr,
        )
        args.skip_git_repo_check = True

    if args.background and args.mode != "interactive":
        cmd = build_headless_cmd(args)
        return run_background(cmd, cwd=args.cd, log_dir=args.log_dir, notify=args.notify)

    if args.mode == "interactive":
        rc = run_interactive_tmux(args)
    else:
        cmd = build_headless_cmd(args)
        if args.clipboard:
            # Capture output for clipboard
            proc = subprocess.run(
                ["script", "-q", "/dev/null"] + cmd,
                cwd=args.cd,
                capture_output=True,
                text=True,
            )
            print(proc.stdout, end="")
            if proc.stderr:
                print(proc.stderr, end="", file=sys.stderr)
            copy_to_clipboard(proc.stdout)
            rc = proc.returncode
        else:
            rc = run_with_pty(cmd, cwd=args.cd)

    # Optional notification
    if args.notify:
        status = "completed" if rc == 0 else f"failed (exit {rc})"
        notify_macos("Codex", f"Headless task {status}")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
