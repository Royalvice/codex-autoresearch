from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .base import AutoresearchScriptsTestBase


class AutoresearchHooksCtlTest(AutoresearchScriptsTestBase):
    maxDiff = None

    def hook_env(self, home: Path) -> dict[str, str]:
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["CODEX_HOME"] = str(home / ".codex")
        return env

    def installed_hook_path(self, home: Path, name: str) -> Path:
        return home / ".codex" / "autoresearch-hooks" / name

    def repo_hook_context_path(self, repo: Path) -> Path:
        return repo / "autoresearch-hook-context.json"

    def run_installed_hook(
        self,
        hook_path: Path,
        *,
        cwd: Path,
        payload: dict[str, object],
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
        )

    def write_transcript_marker(
        self,
        path: Path,
        text: str = "$codex-autoresearch\nResume the current run.\n",
    ) -> None:
        payload = {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            },
        }
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    def test_status_reports_platform_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            env = self.hook_env(home)
            status = self.run_script("autoresearch_hooks_ctl.py", "status", env=env)
            self.assertEqual(status["supported"], os.name != "nt")
            self.assertFalse(status["ready_for_future_sessions"])

    def test_install_refuses_on_windows(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows-only refusal path")
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            env = self.hook_env(home)
            completed = self.run_script_completed("autoresearch_hooks_ctl.py", "install", env=env)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("not supported on Windows yet", completed.stderr)

    def test_install_merges_existing_config_and_is_idempotent(self) -> None:
        if os.name == "nt":
            self.skipTest("Hooks install is intentionally unsupported on Windows")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            codex_home = home / ".codex"
            codex_home.mkdir(parents=True)
            env = self.hook_env(home)

            (codex_home / "config.toml").write_text(
                "[features]\nother_feature = true\n",
                encoding="utf-8",
            )
            (codex_home / "hooks.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "UserPromptSubmit": [
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "python3 /tmp/existing.py",
                                            "statusMessage": "existing",
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            installed = self.run_script("autoresearch_hooks_ctl.py", "install", env=env)
            self.assertTrue(installed["ready_for_future_sessions"])
            self.assertTrue(installed["feature_enabled"])
            self.assertTrue(installed["managed_scripts_present"])

            hooks_payload = json.loads((codex_home / "hooks.json").read_text(encoding="utf-8"))
            self.assertIn("UserPromptSubmit", hooks_payload["hooks"])
            self.assertEqual(len(hooks_payload["hooks"]["SessionStart"]), 1)
            self.assertEqual(len(hooks_payload["hooks"]["Stop"]), 1)

            reinstalled = self.run_script("autoresearch_hooks_ctl.py", "install", env=env)
            self.assertTrue(reinstalled["ready_for_future_sessions"])
            hooks_payload = json.loads((codex_home / "hooks.json").read_text(encoding="utf-8"))
            self.assertEqual(len(hooks_payload["hooks"]["SessionStart"]), 1)
            self.assertEqual(len(hooks_payload["hooks"]["Stop"]), 1)

            removed = self.run_script("autoresearch_hooks_ctl.py", "uninstall", env=env)
            self.assertEqual(removed["managed_groups_removed"], 2)
            hooks_payload = json.loads((codex_home / "hooks.json").read_text(encoding="utf-8"))
            self.assertNotIn("SessionStart", hooks_payload["hooks"])
            self.assertNotIn("Stop", hooks_payload["hooks"])
            self.assertIn("UserPromptSubmit", hooks_payload["hooks"])

    def test_foreground_pointer_file_restores_custom_paths_for_future_sessions(self) -> None:
        if os.name == "nt":
            self.skipTest("Hooks install is intentionally unsupported on Windows")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            env = self.hook_env(home)
            self.run_script("autoresearch_hooks_ctl.py", "install", env=env)
            hook_path = self.installed_hook_path(home, "session_start.py")

            repo = root / "foreground-repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            artifacts = repo / "artifacts"
            artifacts.mkdir(parents=True)
            custom_results = artifacts / "custom-results.tsv"
            custom_state = artifacts / "custom-state.json"

            self.run_script(
                "autoresearch_init_run.py",
                "--results-path",
                str(custom_results),
                "--state-path",
                str(custom_state),
                "--mode",
                "loop",
                "--session-mode",
                "foreground",
                "--goal",
                "Reduce failures",
                "--scope",
                "src/**/*.py",
                "--metric-name",
                "failure count",
                "--direction",
                "lower",
                "--verify",
                "pytest -q",
                "--baseline-metric",
                "10",
                "--baseline-commit",
                "base111",
                "--baseline-description",
                "baseline failures",
                env=env,
            )

            pointer_payload = json.loads(self.repo_hook_context_path(repo).read_text(encoding="utf-8"))
            self.assertTrue(pointer_payload["active"])
            self.assertEqual(pointer_payload["session_mode"], "foreground")
            self.assertEqual(pointer_payload["results_path"], "artifacts/custom-results.tsv")
            self.assertEqual(pointer_payload["state_path"], "artifacts/custom-state.json")

            transcript_path = root / "foreground-rollout.jsonl"
            self.write_transcript_marker(transcript_path)
            completed = self.run_installed_hook(
                hook_path,
                cwd=repo,
                payload={
                    "cwd": str(repo),
                    "source": "resume",
                    "transcript_path": str(transcript_path),
                },
                env=env,
            )
            completed.check_returncode()
            payload = json.loads(completed.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Record every completed experiment before starting the next one.", context)

    def test_stop_hook_only_blocks_for_autoresearch_sessions_and_marks_terminal_pointer_inactive(self) -> None:
        if os.name == "nt":
            self.skipTest("Hooks install is intentionally unsupported on Windows")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            env = self.hook_env(home)
            self.run_script("autoresearch_hooks_ctl.py", "install", env=env)
            hook_path = self.installed_hook_path(home, "stop.py")

            repo = root / "active-repo"
            repo.mkdir()
            self.run_script(
                "autoresearch_init_run.py",
                "--results-path",
                str(repo / "research-results.tsv"),
                "--state-path",
                str(repo / "autoresearch-state.json"),
                "--mode",
                "loop",
                "--goal",
                "Reduce failures",
                "--scope",
                "src/**/*.py",
                "--metric-name",
                "failure count",
                "--direction",
                "lower",
                "--verify",
                "pytest -q",
                "--baseline-metric",
                "10",
                "--baseline-commit",
                "base111",
                "--baseline-description",
                "baseline failures",
                env=env,
            )

            transcript_path = root / "foreground-rollout.jsonl"
            self.write_transcript_marker(transcript_path)
            completed = self.run_installed_hook(
                hook_path,
                cwd=repo,
                payload={
                    "cwd": str(repo),
                    "stop_hook_active": False,
                    "transcript_path": str(transcript_path),
                },
                env=env,
            )
            completed.check_returncode()
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("Do not rerun the wizard.", payload["reason"])

            terminal_repo = root / "terminal-repo"
            terminal_repo.mkdir()
            self.run_script(
                "autoresearch_init_run.py",
                "--results-path",
                str(terminal_repo / "research-results.tsv"),
                "--state-path",
                str(terminal_repo / "autoresearch-state.json"),
                "--mode",
                "loop",
                "--goal",
                "Reduce failures",
                "--scope",
                "src/**/*.py",
                "--metric-name",
                "failure count",
                "--direction",
                "lower",
                "--verify",
                "pytest -q",
                "--stop-condition",
                "stop when metric reaches 0",
                "--baseline-metric",
                "0",
                "--baseline-commit",
                "base000",
                "--baseline-description",
                "baseline failures",
                env=env,
            )

            completed = self.run_installed_hook(
                hook_path,
                cwd=terminal_repo,
                payload={
                    "cwd": str(terminal_repo),
                    "stop_hook_active": False,
                    "transcript_path": str(transcript_path),
                },
                env=env,
            )
            completed.check_returncode()
            self.assertEqual(completed.stdout, "")

            pointer_payload = json.loads(self.repo_hook_context_path(terminal_repo).read_text(encoding="utf-8"))
            self.assertFalse(pointer_payload["active"])
