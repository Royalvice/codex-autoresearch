# Installation

`codex-autoresearch` is a Markdown-first Codex skill package with bundled helper scripts. No build step, no runtime dependencies.

## Install

### Via Skill Installer (recommended)

In Codex, run:

```text
$skill-installer install https://github.com/leo-lilinxiao/codex-autoresearch
```

Restart Codex after installation.

### Option A: Clone into a repository

```bash
git clone https://github.com/leo-lilinxiao/codex-autoresearch.git
cp -r codex-autoresearch your-project/.agents/skills/codex-autoresearch
```

### Option B: Install for all projects (user scope)

```bash
git clone https://github.com/leo-lilinxiao/codex-autoresearch.git
cp -r codex-autoresearch ~/.agents/skills/codex-autoresearch
```

### Option C: Symlink for live development

```bash
git clone https://github.com/leo-lilinxiao/codex-autoresearch.git
ln -s $(pwd)/codex-autoresearch your-project/.agents/skills/codex-autoresearch
```

Codex supports symlinked skill folders. Edits to the source repo take effect immediately.

## Skill Discovery Locations

Codex scans these directories for skills:

| Scope | Location | Use case |
|-------|----------|----------|
| Repo (CWD) | `$CWD/.agents/skills/` | Skills for the current working directory |
| Repo (parent) | `$CWD/../.agents/skills/` | Shared skills in a parent folder (monorepo) |
| Repo (root) | `$REPO_ROOT/.agents/skills/` | Root skills available to all subfolders |
| User | `~/.agents/skills/` | Personal skills across all projects |
| Admin | `/etc/codex/skills/` | Machine-wide defaults for all users |
| System | Bundled with Codex | Built-in skills by OpenAI |

## Verify Installation

Open Codex in the target repo and verify:

1. Type `$` and confirm `codex-autoresearch` appears in the skill list.
2. Invoke the skill:

```text
$codex-autoresearch
I want to reduce my failing tests to zero
```

Expected behavior:

- Codex recognizes the skill,
- loads `SKILL.md`,
- loads the relevant workflow for the request,
- and collects any missing fields via the wizard.

## Optional User-Level Hooks

`codex-autoresearch` also ships an optional user-level hook installer for long-running background workflows:

```bash
python3 <skill-root>/scripts/autoresearch_hooks_ctl.py status
python3 <skill-root>/scripts/autoresearch_hooks_ctl.py install
python3 <skill-root>/scripts/autoresearch_hooks_ctl.py uninstall
```

Behavior:

- Hooks are installed into the current `CODEX_HOME`, not into an individual repo.
- The managed hook payload consists of `SessionStart` and `Stop` handlers plus a small manifest under `CODEX_HOME/autoresearch-hooks/`.
- Active repos expose their current run through `autoresearch-hook-context.json`, which lets future Codex sessions recover the right results/state/launch/runtime paths.
- Windows intentionally refuses `install` and `uninstall` today. The main runtime/controller features still work on Windows without these hooks.

## Updating

If installed by copy: re-clone and replace the installed folder.

If installed by symlink: `git pull` in the source repo. Changes are live immediately.

If an update does not appear, restart Codex.

## Disable Without Deleting

Use `~/.codex/config.toml`:

```toml
[[skills.config]]
path = "/absolute/path/to/codex-autoresearch/SKILL.md"
enabled = false
```

Restart Codex after changing the config.
