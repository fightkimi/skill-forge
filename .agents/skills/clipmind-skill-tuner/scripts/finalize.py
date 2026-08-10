#!/usr/bin/env python3
"""Create a local merge package after the operator explicitly accepts a Skill."""

from __future__ import annotations

import argparse
import difflib
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from skill_guard import END, START, validate_skill_dir


def extract_definition(text: str) -> str:
    return text.split(START, 1)[1].split(END, 1)[0].strip() + "\n"


def build_package(root: Path, skill_id: str, rounds: int) -> tuple[Path | None, list[str]]:
    skill_dir = root / "skills" / skill_id
    result = validate_skill_dir(skill_dir)
    if not result.ok:
        return None, result.errors
    if skill_id.startswith("clipmind-governance-"):
        return None, ["治理 Skill 只读，请生成工程变更建议单而不是最终校正 Skill"]

    candidate_path = skill_dir / "SKILL.md"
    original_path = skill_dir / "references/original.md"
    candidate = candidate_path.read_text(encoding="utf-8")
    original = original_path.read_text(encoding="utf-8")
    output_dir = root / "merge-packages" / skill_id
    output_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(candidate_path, output_dir / "SKILL.md")
    shutil.copy2(skill_dir / "references/source-map.md", output_dir / "source-map.md")
    (output_dir / "mergeable-definition.md").write_text(extract_definition(candidate), encoding="utf-8")
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            candidate.splitlines(keepends=True),
            fromfile="references/original.md",
            tofile="SKILL.md",
        )
    )
    (output_dir / "baseline-vs-final.diff").write_text(diff or "# 与初始基线无差异\n", encoding="utf-8")
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (output_dir / "validation.md").write_text(
        "# 验证结果\n\n"
        f"- Skill：`{skill_id}`\n"
        f"- 调试轮数：{rounds}\n"
        f"- 收口时间（UTC）：{timestamp}\n"
        "- 不可修改边界：通过\n"
        "- 原始基线：未修改\n"
        "- 上线状态：未上线；需开发按 source-map 定位真实源文件并使用生产模型复测\n",
        encoding="utf-8",
    )
    return output_dir, []


def main() -> int:
    default_root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description="生成操盘手确认后的 Skill 回收包")
    parser.add_argument("skill_id")
    parser.add_argument("--rounds", type=int, required=True)
    parser.add_argument("--root", type=Path, default=default_root, help=argparse.SUPPRESS)
    args = parser.parse_args()

    output_dir, errors = build_package(args.root, args.skill_id, args.rounds)
    if errors:
        print("BLOCKED：不能生成回收包。", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2 if args.skill_id.startswith("clipmind-governance-") else 1
    print(output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
