#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from autoresearch_helpers import AutoresearchError, utc_now


def append_lesson(
    *,
    lessons_path: Path,
    kind: str,
    title: str,
    insight: str,
    context: str,
    iteration: str | None,
) -> dict[str, Any]:
    lessons_path.parent.mkdir(parents=True, exist_ok=True)
    existing = lessons_path.read_text(encoding="utf-8") if lessons_path.exists() else ""
    entry_lines = [
        f"## {title}",
        f"- kind: {kind}",
        f"- iteration: {iteration or '-'}",
        f"- timestamp: {utc_now()}",
        f"- context: {context}",
        f"- insight: {insight}",
        "",
    ]
    content = existing
    if content and not content.endswith("\n"):
        content += "\n"
    content += "\n".join(entry_lines)
    lessons_path.write_text(content, encoding="utf-8")
    return {
        "lessons_path": str(lessons_path),
        "kind": kind,
        "title": title,
        "iteration": iteration or "-",
    }


def parse_lesson_entries(lessons_path: Path) -> list[dict[str, str]]:
    if not lessons_path.exists():
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in lessons_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if current is not None:
                entries.append(current)
            current = {"title": line[3:].strip()}
            continue
        if current is None or not line.startswith("- "):
            continue
        if ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        current[key.strip()] = value.strip()
    if current is not None:
        entries.append(current)
    return entries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Append or inspect structured autoresearch lessons."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    append = subparsers.add_parser("append")
    append.add_argument("--lessons-path", default="autoresearch-lessons.md")
    append.add_argument("--kind", choices=["positive", "pivot", "summary"], required=True)
    append.add_argument("--title", required=True)
    append.add_argument("--insight", required=True)
    append.add_argument("--context", required=True)
    append.add_argument("--iteration")

    show = subparsers.add_parser("list")
    show.add_argument("--lessons-path", default="autoresearch-lessons.md")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "append":
        print(
            json.dumps(
                append_lesson(
                    lessons_path=Path(args.lessons_path),
                    kind=args.kind,
                    title=args.title,
                    insight=args.insight,
                    context=args.context,
                    iteration=args.iteration,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "list":
        print(json.dumps(parse_lesson_entries(Path(args.lessons_path)), indent=2, sort_keys=True))
        return 0
    raise AutoresearchError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AutoresearchError as exc:
        raise SystemExit(f"error: {exc}")
