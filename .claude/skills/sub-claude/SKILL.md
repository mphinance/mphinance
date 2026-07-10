---
name: sub-claude
description: "Batch-process data (CSV/JSONL) by spawning parallel Claude agents (`claude -p`). Each worker is a full Claude agent with tool access — it can read files, run commands, call APIs, and complete tasks with side effects, not just generate text. Use this instead of subagents when processing 10+ items where you need fine-grained control over concurrency, model, retries, cost budget, or structured output. Trigger on: batch processing, process each row, parallel claude calls, bulk create issues/tickets, batch execute tasks, bulk classify/translate/extract, or scripting claude CLI."
---

# Sub-Claude — Batch Agent Orchestration

`sub_claude.py` spawns parallel Claude agents to process data rows. The script adds batch orchestration on top: concurrency control, checkpoint/resume, output mapping, cost tracking, and retry logic.

## Provenance & Safety (mphinance note)

Vendored from [six-ddc/skills](https://github.com/six-ddc/skills) (`skills/sub-claude`, commit `ff306e8`) **with the author's permission**. The upstream repo has **no license file** — this copy lives here by explicit grant to Michael, not a public re-license. Keep the credit if you move it.

**Safety:** each worker runs `claude -p ... --dangerously-skip-permissions`, so every spawned agent has full tool access with no per-action prompt. Only run it against inputs and prompts you trust. For pure text tasks (translate/classify/extract) pass `-- --tools ""` to strip tool access entirely and save cost.

## Worker = Full Claude Agent

Each worker is spawned via `claude -p` — **the same runtime as a subagent**. This means every worker has:

| Capability | Example |
|------------|---------|
| **Read files** | Read a migration guide, parse a config, inspect source code |
| **Write/Edit files** | Create tickets, patch code, generate reports |
| **Run bash commands** | `git`, `curl`, `jq`, `npm`, compile, lint, test |
| **Call external APIs** | REST endpoints, CLI tools (`gh`, `jira`, `aws`) |
| **Multi-step reasoning** | Read context → decide strategy → execute → verify |

**Mental model**: don't think of a worker as "an LLM that returns text". Think of it as **a junior dev who receives a task description and has a terminal open**. Write prompts accordingly — describe the goal and point to resources, don't micro-manage every shell command.

### Prompt design principle

❌ Pre-process data in Python, then ask the worker to "translate this text"
✅ Give the worker raw data + a pointer to the rules file, let it figure out the steps

```
# Bad: you do the work, worker just generates text
python3 prepare_data.py && python sub_claude.py ...

# Good: worker does everything end-to-end
python sub_claude.py data.jsonl \
  --prompt "Read the rules at {_work_dir}/rules.md, then process: {raw_data}. Return the result ID." \
  --concurrency 5
```

For **pure text tasks** (translation, classification, extraction) where tools add overhead, pass `-- --tools ""` to disable them.

## When to Use What

| Volume | Recommended | Why |
|--------|-------------|-----|
| 1 item | `claude -p` directly | No orchestration needed |
| 2-10 items | subagent (Agent tool) | Simple, no script setup needed |
| 10-500 items | **sub_claude.py** (this skill) | Fine-grained concurrency, model, retry, budget control |
| 500+ items, not urgent | Anthropic Batch API | 50% discount, returns within 24h |

## Quick Start

### Example 1: Batch Create Tickets

Each worker reads a template, generates content, and calls a CLI to create a ticket:

```bash
python sub_claude.py tasks.jsonl \
  --prompt "Read the rules at {_work_dir}/ticket-template.md, then create a ticket for: {title}. Description context: {details}. Return only the created ticket ID." \
  --output-map "id={id}" "ticket={_.result}" \
  --output results.jsonl \
  --work-dir /path/to/project \
  --concurrency 5 \
  -- --model sonnet --effort high
```

### Example 2: Batch Code Migration

Each worker autonomously migrates a file according to a guide:

```bash
python sub_claude.py files.jsonl \
  --prompt "Migrate {file_path} from v1 to v2 per {_work_dir}/migration-guide.md. Apply changes and return a summary." \
  --output-map "file={file_path}" "summary={_.result}" \
  --output migration_log.jsonl \
  --work-dir /path/to/project \
  --concurrency 3 \
  -- --model sonnet --effort high
```

### Example 3: Simple Translation (No Tools Needed)

For pure text tasks, disable tools to save cost and time:

```bash
python sub_claude.py products.csv \
  --prompt "Translate this product description to English: {description}" \
  --output-column english_desc \
  --output results.csv \
  -- --model haiku --effort low --tools ""
```

### Example 4: Structured Extraction

```bash
python sub_claude.py resumes.csv \
  --prompt "Extract resume info: {raw_text}" \
  --output-map \
    "id={id}" \
    "name={_.structured.name}" \
    "email={_.structured.email}" \
    "years={_.structured.years_of_exp}" \
  --output results.csv \
  --concurrency 5 \
  -- --model sonnet --tools "" --json-schema '{"type":"object","properties":{"name":{"type":"string"},"email":{"type":"string"},"years_of_exp":{"type":"number"}},"required":["name","email","years_of_exp"]}'
```

## mphinance use case — fan out one worker per ticker

The natural fit here is a basket scan: one worker per name, each doing the full read-decide-verify loop, results collected to a single file you can rank.

```bash
# watchlist.txt -> one line per ticker; convert to jsonl first, or use a csv with a `ticker` column
python .claude/skills/sub-claude/scripts/sub_claude.py basket.csv \
  --prompt "Grade {ticker} against the A-grade bullish-pullback rules in {_work_dir}/MOMENTUM_SQUEEZE_GUIDE.md. Pull data via the TDPro/alpaca MCP tools. Return: grade, entry, stop, one-line thesis." \
  --output-map "ticker={ticker}" "read={_.result}" "cost={_.total_cost_usd}" \
  --output basket_scan.csv \
  --work-dir "$(pwd)" \
  --concurrency 4 \
  -- --model sonnet --effort high
```

Remember: **agents draft, humans trade.** This produces a ranking table for Michael to act on — it never places orders.

## Writing Prompts

Write the prompt like you're briefing a colleague — give context, point to resources, describe the desired outcome:

```
You are a bug report filing agent. Your task:

1. Read the filing rules at {_work_dir}/templates/bug-report.md
2. Create a bug report for this error:
   - Module: {module}
   - Error: {error_message}
   - Stack trace: {stacktrace}
3. Return only the created ticket ID (e.g., BUG-1234)
```

### Prompt from File

For complex multi-line prompts, write the template to a file and pass the path:

```bash
cat > prompt.txt << 'EOF'
You are a code review agent. For this commit:
- Hash: {short_hash}
- Changes: {changes}

1. Read the review rules at {_work_dir}/rules.md
2. Generate a summary and create a ticket
3. Return only the ticket ID
EOF

python sub_claude.py commits.jsonl \
  --prompt prompt.txt \
  --output results.jsonl \
  --concurrency 10
```

The `--prompt` argument auto-detects file paths (`.txt`, `.md`, `.prompt` extensions).

Key principles:
- **Point to files** rather than embedding rules: use `{_work_dir}/path/to/rules.md` so the worker reads them at runtime. This avoids placeholder conflicts with `{` `}` in JSON/code.
- **Describe the outcome**, not every micro-step. The worker is a full agent — let it figure out the details.
- **Keep data in the prompt, instructions in files**: pass row-specific data via `{column}` placeholders, but put static rules/templates in external files the worker reads.
- For pure text tasks where tools aren't needed, pass `--tools ""` to save cost and time.

### Placeholders and Curly Braces

The prompt template tries to replace `{...}` with column values or builtins. If a `{...}` doesn't match any known column or builtin, it's kept as-is — so JSON, wiki markup, and other literal curly braces work without escaping.

## Placeholders

Placeholders use `{...}` syntax. There are two contexts with different rules:

**In `--prompt`** — reference input data and built-in context:

| Placeholder | Description |
|-------------|-------------|
| `{column_name}` | CSV column or JSONL field from input data |
| `{nested.field}` | Dot-path into nested JSONL objects (e.g. `{user.name}`) |
| `{_index}` | Current row index (0-based) |
| `{_work_dir}` | Working directory (`--work-dir` or cwd) |
| `{_input_file}` | Input file path |

**In `--output-map`** — reference both input data and CLI output. The `_.` prefix distinguishes them:

- **No prefix** → input field pass-through (copied as-is for correlation): `{id}`, `{name}`
- **`_.` prefix** → CLI output field (Claude's response metadata): `{_.result}`, `{_.total_cost_usd}`

```bash
--output-map "original_id={id}" "result={_.result}" "cost={_.total_cost_usd}"
```

Available `_.` output fields include: `{_.result}`, `{_.is_error}`, `{_.subtype}`, `{_.stop_reason}`, `{_.duration_ms}`, `{_.num_turns}`, `{_.total_cost_usd}`, `{_.usage.input_tokens}`, `{_.usage.output_tokens}`, `{_.session_id}`, `{_.model}`, and `{_.structured.field}` (requires `--json-schema`).

## CLI Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `INPUT_FILE` | Input file (.csv / .jsonl) | (required) |
| `--prompt` | Prompt template string, or path to a `.txt`/`.md`/`.prompt` file | (required) |
| `--output` | Output file path | (required) |
| `--output-map` | Output mapping `"col={placeholder}"` | `ai_result={_.result}` |
| `--output-column` | Shorthand, equivalent to `--output-map "COL={_.result}"` | — |
| `--concurrency` | Max concurrency | `3` |
| `--work-dir` | Claude working directory + `{_work_dir}` placeholder | cwd |
| `--retry` | Max retries per row on recoverable errors (exp. backoff 1s, 2s, 4s…) | `0` |
| `--limit` | Only process the first N rows (useful for testing) | all |
| `--dry-run` | Preview mode, no execution | — |

**Passthrough Parameters** (after `--`): passed directly to `claude -p`. Common ones: `--model`, `--effort`, `--system-prompt`, `--json-schema`, `--max-budget-usd`, `--bare`, `--tools ""`, `--fallback-model`.

## Checkpoint & Resume

The script writes each completed row to the output file immediately, tagged with a `_src_index` column. If interrupted (Ctrl+C, crash, network loss), **re-run the same command** — it reads the existing output, skips rows whose `_src_index` already exists, and only processes the remainder. Rows may land out of order; sort by `_src_index` to restore input order.

## Error Handling

A single row failure does not abort the batch. Failed rows are still written, with `_error` populated and `{_.is_error}` set to `true`. Filter by `_error` to re-process failures. Non-recoverable errors (auth, invalid model, 4xx) are not retried; transient ones (429/500/timeout) are, up to `--retry`.
