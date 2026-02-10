---
name: codex-headless
description: "Run OpenAI Codex in headless mode (`codex exec`) on macOS. Use when the user asks to run Codex programmatically, execute headless prompts, use `codex exec`, get structured JSON output, auto-approve commands with --full-auto or sandbox policies, pipe output, create commits via CLI, integrate Codex into scripts, cron jobs, and CI/CD workflows on macOS, or asks about Codex CLI features, flags, sandbox policies, SDK, or configuration."
argument-hint: "[prompt or flags]"
---

# OpenAI Codex Headless (macOS)

Use the locally installed **OpenAI Codex** CLI (`codex exec`) in headless (non-interactive) mode on **macOS**.

> This skill is for driving the `codex` CLI programmatically via `codex exec`, not the OpenAI API directly.

## Environment checks

```bash
# Verify codex is installed
which codex
codex --version

# Quick smoke test
codex exec "Return only the single word OK."
```

If `codex` is not found, install via:
```bash
npm install -g @openai/codex
```

---

## Headless mode basics

Use `codex exec` to run non-interactively. The prompt can be passed as a positional argument or via stdin.

### Simple prompt

```bash
codex exec "What does the auth module do?"
```

### Run in a specific directory

```bash
codex exec --cd /path/to/repo "Summarize this project"
```

### Pipe prompt from stdin

```bash
echo "Explain this codebase" | codex exec
```

---

## PTY wrapper (macOS-specific)

Codex may hang without a TTY in certain environments. On **macOS (BSD)**, use `script` to allocate a pseudo-terminal:

```bash
# macOS BSD syntax (different from Linux!)
script -q /dev/null codex exec "Your prompt here"
```

**Do NOT use Linux syntax** (`script -q -c "cmd" /dev/null`) -- it will fail on macOS.

A wrapper script is provided that handles this automatically:

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  "Your prompt here"
```

---

## Key CLI flags for `codex exec`

| Flag | Short | Description |
|------|-------|-------------|
| `PROMPT` | | Initial instructions (positional arg or stdin) |
| `--model` | `-m` | Model to use (e.g. `o4-mini`, `codex-mini-latest`) |
| `--sandbox` | `-s` | Sandbox policy: `read-only`, `workspace-write`, `danger-full-access` |
| `--full-auto` | | Convenience: `-a on-request --sandbox workspace-write` |
| `--profile` | `-p` | Configuration profile from `config.toml` |
| `--cd` | `-C` | Working directory for the agent |
| `--image` | `-i` | Attach image(s) to the initial prompt |
| `--json` | | Print events to stdout as JSONL |
| `--output-last-message` | `-o` | Write last agent message to a file |
| `--output-schema` | | Path to JSON Schema for structured final response |
| `--ephemeral` | | Run without persisting session files |
| `--skip-git-repo-check` | | Allow running outside a Git repository |
| `--add-dir` | | Additional writable directories |
| `--color` | | Color settings for output |
| `--oss` | | Use an open-source provider |
| `--local-provider` | | Local provider (`lmstudio` or `ollama`) |
| `--dangerously-bypass-approvals-and-sandbox` / `--yolo` | | Skip all prompts and sandboxing (use with extreme caution) |

---

## Structured output

### JSONL event stream

```bash
codex exec --json "Summarize this project"
```

### Write last message to file

```bash
codex exec -o result.txt "Explain the auth module"
cat result.txt
```

### JSON Schema (typed output)

```bash
codex exec --output-schema schema.json "Extract function names from auth.py"
```

Where `schema.json` contains:
```json
{
  "type": "object",
  "properties": {
    "functions": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["functions"]
}
```

---

## Sandbox policies

Control what commands the agent can execute:

| Policy | Description |
|--------|-------------|
| `read-only` | No file writes or destructive commands |
| `workspace-write` | Can write within the workspace directory |
| `danger-full-access` | Full system access (use with caution) |

```bash
# Safe read-only analysis
codex exec --sandbox read-only "Analyze and propose a plan"

# Allow workspace writes (recommended for most tasks)
codex exec --sandbox workspace-write "Refactor the auth module"

# Full auto mode (workspace-write + auto-approve)
codex exec --full-auto "Run tests and fix failures"
```

---

## Session management

### Resume a session

```bash
codex exec resume <SESSION_ID>

# Resume the most recent session
codex exec resume --last

# Resume last session with a new prompt
codex exec resume --last "Continue working on the fix"
```

### Fork a session

```bash
# Fork creates a new independent session with the same conversation history
codex fork <SESSION_ID>
codex fork --last
```

---

## Model selection

```bash
# Use a specific model
codex exec -m o4-mini "Quick code review"

# Use open-source provider
codex exec --oss "Analyze this code"

# Use local provider
codex exec --local-provider ollama -m llama3 "Explain this function"
```

---

## macOS-specific integrations

### Copy output to clipboard (pbcopy)

```bash
codex exec -o /dev/stdout "Summarize this project" | pbcopy
```

### Paste clipboard as input (pbpaste)

```bash
pbpaste | codex exec "Review this code"
```

### Desktop notification on completion (osascript)

```bash
codex exec --full-auto "Run all tests and fix failures"; \
  osascript -e 'display notification "Codex task finished" with title "Codex"'
```

### Combine: run, notify, and copy result

```bash
codex exec -o result.txt "Summarize this project"; \
  cat result.txt | pbcopy; \
  osascript -e 'display notification "Result copied to clipboard" with title "Codex"'
```

---

## Interactive mode (tmux)

For long-running tasks that need monitoring, use the Python wrapper with tmux:

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --mode interactive \
  --tmux-session my-session \
  --sandbox workspace-write \
  "Your interactive prompt here"
```

Monitor:
```bash
tmux attach -t my-session
```

---

## Common recipes

### Git commit from staged changes

```bash
codex exec --full-auto "Look at my staged changes and create an appropriate commit"
```

### Code review a PR

```bash
gh pr diff 123 | codex exec "Review this PR for bugs and security issues"
```

### Fix test failures

```bash
codex exec --full-auto "Run the test suite and fix any failures"
```

### Explain + Plan first, then implement

```bash
# Step 1: plan (read-only)
codex exec --sandbox read-only "Analyze the auth system and propose improvements"

# Step 2: implement
codex exec --full-auto "Implement the improvements to the auth system"
```

### Batch processing with a loop

```bash
for file in src/**/*.py; do
  codex exec --sandbox workspace-write "Add type hints to $file"
done
```

### Pipe build errors for diagnosis

```bash
npm run build 2>&1 | codex exec "Explain the root cause and suggest a fix"
```

### Attach images for context

```bash
codex exec -i screenshot.png "What UI issues do you see in this screenshot?"
```

### Run without git repo

```bash
codex exec --skip-git-repo-check "Analyze the files in this directory"
```

### Use with additional writable directories

```bash
codex exec --full-auto --add-dir /tmp/output "Generate reports and save to /tmp/output"
```

---

## TypeScript SDK (programmatic usage)

For deeper integration, use the Codex TypeScript SDK:

```typescript
import { Codex } from "@openai/codex-sdk";

const codex = new Codex();
const thread = codex.startThread();
const turn = await thread.run("Diagnose the test failure and propose a fix");

console.log(turn.finalResponse);
console.log(turn.items);
```

---

## Background mode (non-blocking)

Run tasks in the background — the wrapper returns immediately with PID and log path.

```bash
# Fire-and-forget with notification when done
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --background --notify \
  --full-auto "Run all tests and fix failures"

# Custom log directory
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --background --log-dir /tmp/codex-logs \
  --sandbox workspace-write "Refactor the auth module"
```

Output:
```
Background process started:
  PID:  12345
  Log:  ~/.claude/logs/headless/codex-20260210-143022.log
  Tail: tail -f ~/.claude/logs/headless/codex-20260210-143022.log
  Stop: kill 12345
```

| Flag | Description |
|------|-------------|
| `--background` / `--bg` | Run in background, return immediately |
| `--log-dir <path>` | Log directory (default: `~/.claude/logs/headless`) |
| `--notify` | macOS notification when background task finishes |

---

## Best practices

1. **Start with `--sandbox read-only`** for analysis, then switch to `--full-auto` for implementation
2. **Use `--full-auto`** as the default for trusted tasks (workspace-write + auto-approve)
3. **Avoid `--yolo`** unless running inside an externally sandboxed environment (Docker, VM)
4. **Use `--json`** for machine-readable event streams in automation pipelines
5. **Use `-o`** to capture the final agent message to a file for post-processing
6. **Use `--output-schema`** when you need structured, typed responses
7. **Pipe liberally** -- treat `codex exec` as a Unix utility
8. **Use `--cd`** to set the working directory instead of `cd`-ing first
9. **Use `--ephemeral`** for one-off tasks where session persistence isn't needed
10. **Capture session IDs** via `--json` output when you need to resume or fork later

---

## Looking up Codex documentation via DeepWiki

When encountering unfamiliar flags, features, sandbox policies, SDK usage, or any Codex topic not covered above, query the official repository documentation using the DeepWiki MCP server.

### Query the repo

```
mcp__deepwiki__ask_question
  repoName: "openai/codex"
  question: "<specific question about Codex>"
```

### Example queries

```
"What CLI flags are available for codex exec headless mode?"
"How does the sandbox system work? What are all sandbox policies and their permissions?"
"How to configure Codex with config.toml profiles?"
"How does session management work? How to resume and fork sessions?"
"How to use the Codex TypeScript SDK programmatically?"
"How to use Codex with local providers (ollama, lmstudio)?"
"How does --output-schema work for structured responses?"
"How to use Codex with open-source models via --oss flag?"
```

### Browse available topics

```
mcp__deepwiki__read_wiki_structure
  repoName: "openai/codex"
```

Use this to discover which documentation sections exist before asking a targeted question.

### When to query DeepWiki

- A flag or option is not documented in this skill
- The user asks about SDK integration, custom providers, or advanced configuration
- Troubleshooting unexpected behavior or error messages
- Verifying the latest syntax or available options
- Any Codex feature beyond basic headless mode usage
