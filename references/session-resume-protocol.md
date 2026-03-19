# Session Resume Protocol

Detect and recover from interrupted runs. Resumes from the last consistent state instead of restarting from scratch.

## JSON State File

The primary recovery source is `autoresearch-state.json`, an atomic-write state snapshot updated every iteration. Schema:

```json
{
  "version": 1,
  "run_tag": "<run-tag>",
  "mode": "loop",
  "config": {
    "goal": "<goal text>",
    "scope": "<glob pattern>",
    "metric": "<metric name>",
    "direction": "lower | higher",
    "verify": "<verify command>",
    "guard": "<guard command or null>"
  },
  "state": {
    "iteration": 15,
    "baseline_metric": 47,
    "best_metric": 28,
    "best_iteration": 12,
    "current_metric": 31,
    "last_commit": "a1b2c3d",
    "keeps": 8,
    "discards": 5,
    "crashes": 1,
    "consecutive_discards": 2,
    "pivot_count": 0,
    "last_status": "discard"
  },
  "updated_at": "2026-03-19T08:15:32Z"
}
```

Write protocol: write to `autoresearch-state.json.tmp`, then rename to `autoresearch-state.json` (atomic). Never commit this file to git.

## Detection Signals

At the start of every invocation, check for prior run artifacts in this order:

| Priority | Signal | File / Command | Weight |
|----------|--------|---------------|--------|
| 1 | **JSON state** | `autoresearch-state.json` exists and is valid JSON with `version` field | **primary** |
| 2 | Results log | `research-results.tsv` exists and has data rows | strong |
| 3 | Lessons file | `autoresearch-lessons.md` exists | moderate |
| 4 | Git history | Recent commits with `experiment:` prefix | moderate |
| 5 | Output dirs | `debug/`, `fix/`, `security/`, `ship/` directories with timestamped subdirectories | weak |

If none of these signals are present, proceed with a fresh run (normal wizard flow).

## Recovery Priority Matrix

When at least one signal is detected, apply this priority cascade:

| # | Condition | Decision |
|---|-----------|----------|
| 1 | JSON valid + TSV row count matches `state.iteration` | **Full resume** (skip wizard) |
| 2 | JSON valid + TSV row count mismatches | **Mini-wizard** (1-round confirmation) |
| 3 | JSON missing + TSV exists | **TSV fallback** (legacy recovery, see below) |
| 4 | JSON corrupt / unparseable | Rename to `.bak`, fall back to TSV recovery |
| 5 | Neither JSON nor TSV exists | **Fresh start** |

### Priority 1: Full Resume (JSON + TSV consistent)

When JSON state is present, valid, and the TSV row count (excluding comments and header) matches `state.iteration`:

1. Restore all loop variables from the JSON `state` and `config` objects.
2. Print resume banner:
   ```
   Resuming from iteration {state.iteration}, best metric: {state.best_metric} (iteration {state.best_iteration}).
   {state.keeps} kept, {state.discards} discarded, {state.crashes} crashed so far.
   Source: autoresearch-state.json (cross-validated with TSV)
   ```
3. Skip the wizard entirely.
4. Read the lessons file if present.
5. Run the verify command to establish the current metric as a sanity check.
6. If the current metric matches `state.current_metric` (within tolerance), continue from iteration N+1.
7. If the metric has drifted, log a `drift` entry and recalibrate baseline before continuing.

### Priority 2: Mini-Wizard (JSON valid, TSV inconsistent)

When JSON state is valid but the TSV row count does not match `state.iteration`:

1. Print what was detected:
   ```
   Found JSON state (iteration {state.iteration}, best: {state.best_metric}).
   TSV row count mismatch ({tsv_rows} rows vs expected {state.iteration}).
   ```
2. Ask a single confirmation:
   - "Resume from JSON state?" (re-confirm scope, metric, verify)
   - "Start fresh?" (ignore previous run)
3. If resuming, use the JSON `config` as the authoritative source and re-validate all config fields in one round.
4. If starting fresh, rename both files with `.prev` / `.prev.json` suffixes and proceed normally.

### Priority 3: TSV Fallback (no JSON, TSV exists)

Backward-compatible recovery when JSON state is not available. This is the legacy path:

1. Parse `research-results.tsv`:
   - Extract the last iteration number.
   - Extract the metric direction comment.
   - Extract the best metric value and its iteration.
   - Extract the current metric value (last row).
   - Count keeps, discards, crashes.
   - Identify the run tag if present.

2. Validate Git State:
   - Check if the commit hash from the last log entry matches a real commit.
   - Check if HEAD is at or after the last logged commit.
   - Check `git status --porcelain` for uncommitted changes.

3. Validate Verify Command:
   - Extract the verify command from the results log context or recent git history.
   - Attempt a dry run to confirm it still works.

4. Apply the TSV Resume Decision Matrix:

| Results Log | Git Consistent | Verify Works | Decision |
|-------------|---------------|--------------|----------|
| valid | yes | yes | **Full resume** |
| valid | no (diverged) | yes | **Mini-wizard** |
| valid | yes | no (broken) | **Mini-wizard** |
| valid | no | no | **Fresh start** |
| corrupt | - | - | **Fresh start** (rename corrupt log) |

### Priority 4: Corrupt JSON Recovery

If `autoresearch-state.json` exists but cannot be parsed as valid JSON:

1. Rename to `autoresearch-state.json.bak`.
2. Log a warning: `JSON state file corrupt, falling back to TSV recovery.`
3. Proceed with Priority 3 (TSV fallback) if a TSV exists, otherwise fresh start.

## Fresh Start

When no prior run is detected or the user chooses to start fresh:

1. Proceed with the normal wizard flow.
2. If a previous results log exists, rename it to `research-results.prev.tsv`.
3. If a previous JSON state exists, rename it to `autoresearch-state.prev.json`.
4. If a previous lessons file exists, keep it (lessons carry across runs).

## Edge Cases

### Multiple Previous Runs

If multiple `.prev` results files exist, keep the lessons file but do not attempt to merge results logs. Each run has its own log and its own JSON state.

### Corrupted Results Log

If the results log exists but is unparseable:
1. Rename to `research-results.corrupt.tsv`.
2. Proceed as fresh start.
3. Preserve the lessons file if it is independently valid.

### Different Goal

If the detected previous run has a clearly different goal than the current request:
1. Treat as a fresh start.
2. Rename the old results log with `.prev` suffix.
3. Rename the old JSON state with `.prev.json` suffix.
4. Keep the lessons file (cross-goal learning is valid).

## Integration Points

- **autonomous-loop-protocol.md (Phase 0):** Session resume check runs before safety checks. JSON state is written after wizard completion.
- **autonomous-loop-protocol.md (Phase 8):** JSON state is atomically updated after each iteration log.
- **exec-workflow.md:** Exec mode skips all session resume logic. Prior `autoresearch-state.json` and `research-results.tsv` are renamed to `.prev` suffixes. Exec mode does not write or update the JSON state file.
- **lessons-protocol.md:** Lessons file is a detection signal and is preserved across runs.
- **results-logging.md:** Results log is cross-validated against JSON state. TSV serves as a fallback when JSON is unavailable.
- **interaction-wizard.md:** Mini-wizard is a reduced version of the full wizard (1 round max). See the Mini-Wizard section in interaction-wizard.md.
- **SKILL.md:** Load order includes session resume check before wizard.
