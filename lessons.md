# Codex Headless — Lessons Learned

### 2026-02-13 — Git repo check blocks execution outside repos
- **Friction**: Running `codex exec` outside a git repository fails with "Not inside a trusted directory and --skip-git-repo-check was not specified"
- **Fix**: Add `--skip-git-repo-check` flag when running outside a git repo
- **Rule**: When the working directory is not a git repo (e.g., `~`), always add `--skip-git-repo-check`. Updated SKILL.md with a caveat section.

### 2026-02-13 — Armenian text glitch in code comments
- **Friction**: Codex (GPT-5.3) produced a comment in Armenian (`# վերdelays իdelays palindrome bounds`) instead of English
- **Fix**: N/A — this is a model-level tokenizer/multilingual behavior, not controllable via CLI flags
- **Rule**: Be aware that Codex may occasionally produce comments in unexpected languages. Review generated code comments for correctness.
