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
FIXTURE_MARKDOWN_FILES = (
    "README.md",
    "MATERIALS.md",
    "PROFILE.md",
    "EVIDENCE-INDEX.md",
    "原始材料/01-人物访谈.md",
    "原始材料/02-业务与产品.md",
    "原始材料/03-用户访谈与评论.md",
    "原始材料/04-案例记录.md",
    "原始材料/05-表达语料.md",
    "原始材料/06-历史内容样本.md",
    "原始材料/07-内容表现数据.md",
    "原始材料/08-阶段目标与选题池.md",
)


def check_builtin_fixture(root: Path, queue_ids: set[str]) -> list[str]:
    errors: list[str] = []
    fixture = root / "fixtures/ip/赵玥玥"
    for relative in FIXTURE_MARKDOWN_FILES:
        path = fixture / relative
        if not path.exists():
            errors.append(f"内置赵玥玥演练资料缺少 {relative}")
            continue
        opening = "\n".join(path.read_text(encoding="utf-8").splitlines()[:4])
        if "MOCK 合成演练数据" not in opening:
            errors.append(f"内置演练资料未声明 MOCK：{relative}")

    scenarios_path = fixture / "scenarios.json"
    if not scenarios_path.exists():
        errors.append("内置赵玥玥演练资料缺少 scenarios.json")
        return errors
    try:
        scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"内置场景 JSON 无法解析：{exc}")
        return errors

    mapped_ids = set(scenarios.get("skills", {}))
    if mapped_ids != queue_ids:
        errors.append("内置场景与 32 个操盘手文案 Skill 不一致")
    for skill_id, scenario in scenarios.get("skills", {}).items():
        if not str(scenario.get("task", "")).strip():
            errors.append(f"{skill_id} 缺少固定演练任务")
        materials = scenario.get("materials", [])
        if not materials:
            errors.append(f"{skill_id} 缺少固定演练材料")
        for relative in materials:
            if not (fixture / relative).exists():
                errors.append(f"{skill_id} 引用了不存在的演练材料：{relative}")
    return errors


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
    errors.extend(check_builtin_fixture(root, order_ids))

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
