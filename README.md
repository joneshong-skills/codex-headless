# codex-headless

Run OpenAI Codex in headless mode (`codex exec`) on macOS.

## Description

A Claude Code skill that enables programmatic, non-interactive use of the [OpenAI Codex CLI](https://github.com/openai/codex) on macOS. It provides a Python wrapper that handles PTY allocation (via macOS BSD `script`), background execution, tmux-based interactive sessions, clipboard integration, and desktop notifications.

Use this skill when you need to run Codex programmatically, execute headless prompts, get structured JSON output, auto-approve commands with sandbox policies, pipe output, create commits via CLI, or integrate Codex into scripts, cron jobs, and CI/CD workflows on macOS.

## What It Does

- Runs `codex exec` reliably on macOS by wrapping it with a pseudo-terminal via BSD `script(1)`
- Supports **headless mode** (non-interactive, `codex exec`) and **interactive mode** (tmux sessions)
- Supports **background execution** with logging, PID tracking, and optional desktop notifications
- Provides macOS-specific integrations: clipboard (`pbcopy`/`pbpaste`), notifications (`osascript`), and temp directory handling
- Passes through all Codex CLI flags: `--model`, `--sandbox`, `--full-auto`, `--json`, `--output-schema`, `--image`, and more
- Auto-detects when running outside a Git repo and adds `--skip-git-repo-check` automatically

## Installation

1. **Install the Codex CLI** (if not already installed):

   ```bash
   npm install -g @openai/codex
   ```

2. **Place the skill** in your Claude skills directory:

   ```
   ~/.claude/skills/codex-headless/
   ├── SKILL.md
   ├── README.md
   └── scripts/
       └── codex_headless.py
   ```

3. **Verify** the setup:

   ```bash
   codex --version
   python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py --help
   ```

## Usage

### Basic headless execution

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py "Summarize this project"
```

### With sandbox and model selection

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --full-auto -m o4-mini "Run tests and fix failures"
```

### Background mode

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --background --notify --full-auto "Refactor the auth module"
```

### Interactive mode (tmux)

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --mode interactive --tmux-session my-session "Your prompt here"
```

### Structured JSON output

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --json "Analyze this codebase"
```

### Copy result to clipboard

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --clipboard "Explain the auth module"
```

## Key Flags

| Flag | Description |
|------|-------------|
| `--mode headless\|interactive` | Execution mode (default: headless) |
| `-m, --model` | Model to use (e.g., `o4-mini`) |
| `-s, --sandbox` | Sandbox policy: `read-only`, `workspace-write`, `danger-full-access` |
| `--full-auto` | Auto-approve + workspace-write sandbox |
| `--background` | Run in background, return immediately with PID and log path |
| `--notify` | macOS desktop notification on completion |
| `--clipboard` | Copy output to clipboard via `pbcopy` |
| `--json` | JSONL event stream output |
| `-o, --output-file` | Write last agent message to a file |
| `--output-schema` | JSON Schema for structured responses |
| `--cd` | Working directory for the agent |
| `--tmux-session` | tmux session name (interactive mode) |

## License

This skill is provided as-is for use with Claude Code.
