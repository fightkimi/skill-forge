#!/usr/bin/env python3
"""Create a local merge package after the operator explicitly accepts a Skill."""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from skill_guard import END, START, validate_skill_dir


def extract_definition(text: str) -> str:
    return text.split(START, 1)[1].split(END, 1)[0].strip() + "\n"


def validate_operator_acceptance(root: Path, skill_id: str, rounds: int) -> list[str]:
    acceptance_path = root / "tuning-records" / skill_id / "acceptance.json"
    if not acceptance_path.exists():
        return ["缺少操盘手确认凭据；只有明确回复 OK 后才能生成最终回收包"]
    try:
        acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["操盘手确认凭据无法解析"]
    if acceptance.get("skill_id") != skill_id or acceptance.get("operator_confirmed") is not True:
        return ["操盘手确认凭据与当前 Skill 不一致或尚未确认"]
    if acceptance.get("rounds") != rounds:
        return ["操盘手确认凭据的调试轮数与本次打包不一致"]
    return []


def build_package(root: Path, skill_id: str, rounds: int) -> tuple[Path | None, list[str]]:
    skill_dir = root / "skills" / skill_id
    if skill_id.startswith("clipmind-governance-"):
        return None, ["治理 Skill 只读，请生成工程变更建议单而不是最终校正 Skill"]
    result = validate_skill_dir(
        skill_dir,
        project_root=root,
        enforce_operator_scope=True,
    )
    if not result.ok:
        return None, result.errors
    acceptance_errors = validate_operator_acceptance(root, skill_id, rounds)
    if acceptance_errors:
        return None, acceptance_errors

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
    lock_data = json.loads(
        (root / "inventory/baseline-locks.json").read_text(encoding="utf-8")
    )
    baseline_hash = lock_data["skills"][skill_id]
    (output_dir / "validation.md").write_text(
        "# 验证结果\n\n"
        f"- Skill：`{skill_id}`\n"
        f"- 调试轮数：{rounds}\n"
        f"- 收口时间（UTC）：{timestamp}\n"
        "- 不可修改边界：通过\n"
        f"- 原始基线：未修改（SHA-256: `{baseline_hash}`）\n"
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
