#!/usr/bin/env python3
"""Verify the distributable Skill Forge project and all exported Skills."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from skill_guard import END, START, validate_skill_dir


EXPECTED_TYPES = {"agent": 57, "prompt": 40, "governance": 27, "image": 22}
EXPECTED_OPERATOR_COUNT = 32
EXPECTED_OPTIONAL_COUNT = 7
REQUIRED_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/original.md",
    "references/source-map.md",
    "references/platform-context.md",
    "evals/cases.md",
)


def run_checks(root: Path) -> list[str]:
    errors: list[str] = []
    inventory_path = root / "inventory/skills.json"
    order_path = root / "inventory/tuning-order.json"
    optional_path = root / "inventory/optional-copy-skills.json"
    if not inventory_path.exists() or not order_path.exists() or not optional_path.exists():
        return ["缺少 inventory/skills.json、tuning-order.json 或 optional-copy-skills.json"]

    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))["skills"]
    type_counts = Counter(item["类型"] for item in inventory)
    if dict(type_counts) != EXPECTED_TYPES:
        errors.append(f"Skill 类型数量不符：{dict(type_counts)}")

    order = json.loads(order_path.read_text(encoding="utf-8"))["skills"]
    mode_counts = Counter(item["mode"] for item in order)
    optional = json.loads(optional_path.read_text(encoding="utf-8"))["skills"]
    inventory_ids = {item["技术ID"] for item in inventory}
    order_ids = {item["skill_id"] for item in order}
    optional_ids = {item["skill_id"] for item in optional}
    if len(order) != EXPECTED_OPERATOR_COUNT or dict(mode_counts) != {"tune": EXPECTED_OPERATOR_COUNT}:
        errors.append(f"操盘手文案调试队列不符：总数 {len(order)}，模式 {dict(mode_counts)}")
    if len(optional) != EXPECTED_OPTIONAL_COUNT:
        errors.append(f"按需文案 Skill 数量不符：{len(optional)}")
    if not order_ids.issubset(inventory_ids) or not optional_ids.issubset(inventory_ids):
        errors.append("操盘手清单包含未导出的 Skill")
    if not order_ids.isdisjoint(optional_ids):
        errors.append("默认调试队列与按需文案清单发生重叠")

    for item in inventory:
        skill_id = item["技术ID"]
        skill_dir = root / "skills" / skill_id
        missing = [name for name in REQUIRED_FILES if not (skill_dir / name).exists()]
        if missing:
            errors.append(f"{skill_id} 缺少文件：{', '.join(missing)}")
            continue
        original = (skill_dir / "references/original.md").read_text(encoding="utf-8")
        candidate = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        if original.count(START) != 1 or original.count(END) != 1:
            errors.append(f"{skill_id} 原始基线的平台定义标记异常")
        if candidate.count(START) != 1 or candidate.count(END) != 1:
            errors.append(f"{skill_id} 候选定义的平台定义标记异常")
        result = validate_skill_dir(skill_dir)
        errors.extend(f"{skill_id}: {error}" for error in result.errors)

    tuner = (root / ".agents/skills/clipmind-skill-tuner/SKILL.md").read_text(encoding="utf-8")
    if "TODO" in tuner:
        errors.append("调试引导 Skill 仍含 TODO")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    errors = run_checks(root)
    if errors:
        print(f"FAILED：{len(errors)} 项问题")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS：146 个运输 Skill、32 个操盘手文案 Skill、不可修改边界和引导 Skill 均通过检查。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
