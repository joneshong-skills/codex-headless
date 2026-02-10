[English](README.md) | [繁體中文](README.zh.md)

# codex-headless

在 macOS 上以 headless 模式（`codex exec`）執行 OpenAI Codex。

## 說明

一個 Claude Code 技能，用於在 macOS 上以程式化、非互動方式使用 [OpenAI Codex CLI](https://github.com/openai/codex)。提供 Python 封裝器處理 PTY 分配（透過 macOS BSD `script`）、背景執行、tmux 互動工作階段、剪貼簿整合和桌面通知。

當您需要程式化執行 Codex、執行 headless 提示、取得結構化 JSON 輸出、使用沙箱政策自動核准命令、管線輸出、透過 CLI 建立提交，或將 Codex 整合到腳本、排程任務和 CI/CD 工作流程時使用此技能。

## 功能特色

- 透過 BSD `script(1)` 封裝偽終端，在 macOS 上可靠執行 `codex exec`
- 支援 **headless 模式**（非互動式，`codex exec`）和 **互動模式**（tmux 工作階段）
- 支援 **背景執行**，含日誌記錄、PID 追蹤和可選桌面通知
- 提供 macOS 專屬整合：剪貼簿（`pbcopy`/`pbpaste`）、通知（`osascript`）和暫存目錄處理
- 透傳所有 Codex CLI 旗標：`--model`、`--sandbox`、`--full-auto`、`--json`、`--output-schema`、`--image` 等
- 自動偵測非 Git 倉庫環境並自動添加 `--skip-git-repo-check`

## 安裝

1. **安裝 Codex CLI**（若尚未安裝）：

   ```bash
   npm install -g @openai/codex
   ```

2. **放置技能**到 Claude 技能目錄：

   ```
   ~/.claude/skills/codex-headless/
   ├── SKILL.md
   ├── README.md
   └── scripts/
       └── codex_headless.py
   ```

3. **驗證**設定：

   ```bash
   codex --version
   python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py --help
   ```

## 使用方式

### 基本 headless 執行

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py "Summarize this project"
```

### 搭配沙箱和模型選擇

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --full-auto -m o4-mini "Run tests and fix failures"
```

### 背景模式

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --background --notify --full-auto "Refactor the auth module"
```

### 互動模式（tmux）

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --mode interactive --tmux-session my-session "Your prompt here"
```

### 結構化 JSON 輸出

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --json "Analyze this codebase"
```

### 複製結果到剪貼簿

```bash
python3 ~/.claude/skills/codex-headless/scripts/codex_headless.py \
  --clipboard "Explain the auth module"
```

## 主要旗標

| 旗標 | 說明 |
|------|------|
| `--mode headless\|interactive` | 執行模式（預設：headless） |
| `-m, --model` | 使用的模型（例如 `o4-mini`） |
| `-s, --sandbox` | 沙箱政策：`read-only`、`workspace-write`、`danger-full-access` |
| `--full-auto` | 自動核准 + workspace-write 沙箱 |
| `--background` | 背景執行，立即回傳 PID 和日誌路徑 |
| `--notify` | 完成時發送 macOS 桌面通知 |
| `--clipboard` | 透過 `pbcopy` 複製輸出到剪貼簿 |
| `--json` | JSONL 事件串流輸出 |
| `-o, --output-file` | 將最後一則代理訊息寫入檔案 |
| `--output-schema` | 用於結構化回應的 JSON Schema |
| `--cd` | 代理的工作目錄 |
| `--tmux-session` | tmux 工作階段名稱（互動模式） |

## 授權

本技能以現狀提供，供 Claude Code 使用。
