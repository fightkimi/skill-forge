#!/usr/bin/env python3
"""Verify the distributable Skill Forge project and all exported Skills."""

from __future__ import annotations

import json
import hashlib
import re
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
MIN_FIXTURE_CHARACTERS = {
    "README.md": 1500,
    "MATERIALS.md": 1800,
    "PROFILE.md": 3500,
    "EVIDENCE-INDEX.md": 3500,
    "原始材料/01-人物访谈.md": 3000,
    "原始材料/02-业务与产品.md": 3500,
    "原始材料/03-用户访谈与评论.md": 3500,
    "原始材料/04-案例记录.md": 4500,
    "原始材料/05-表达语料.md": 3500,
    "原始材料/06-历史内容样本.md": 5000,
    "原始材料/07-内容表现数据.md": 3500,
    "原始材料/08-阶段目标与选题池.md": 4000,
}
FIXTURE_SERIES = {
    "EVIDENCE-INDEX.md": (r"^\| XY-E(\d{2}) \|", {f"{index:02d}" for index in range(1, 36)}),
    "原始材料/03-用户访谈与评论.md": (
        r"^### U(\d{2})\｜",
        {f"{index:02d}" for index in range(1, 13)},
    ),
    "原始材料/04-案例记录.md": (r"^## CASE-([A-E])\｜", set("ABCDE")),
    "原始材料/06-历史内容样本.md": (
        r"^## S(\d{2})\｜",
        {f"{index:02d}" for index in range(1, 13)},
    ),
    "原始材料/07-内容表现数据.md": (
        r"^\| D(\d{2}) \|",
        {f"{index:02d}" for index in range(1, 25)},
    ),
}


def check_builtin_fixture(root: Path, queue_ids: set[str]) -> list[str]:
    errors: list[str] = []
    fixture = root / "fixtures/ip/小月"
    for relative in FIXTURE_MARKDOWN_FILES:
        path = fixture / relative
        if not path.exists():
            errors.append(f"内置小月演练资料缺少 {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        opening = "\n".join(text.splitlines()[:4])
        if "MOCK 合成演练数据" not in opening:
            errors.append(f"内置演练资料未声明 MOCK：{relative}")
        if "小月" not in text:
            errors.append(f"内置演练资料未使用小月显示名：{relative}")
        if len(text.strip()) < MIN_FIXTURE_CHARACTERS[relative]:
            errors.append(
                f"内置小月演练资料过薄：{relative} "
                f"（{len(text.strip())} < {MIN_FIXTURE_CHARACTERS[relative]} 字符）"
            )
        if relative in FIXTURE_SERIES:
            pattern, expected = FIXTURE_SERIES[relative]
            actual = set(re.findall(pattern, text, flags=re.MULTILINE))
            if actual != expected:
                errors.append(
                    f"内置小月演练资料样本序列不完整：{relative} "
                    f"（缺少 {sorted(expected - actual)}，多出 {sorted(actual - expected)}）"
                )

    evidence_path = fixture / "EVIDENCE-INDEX.md"
    if evidence_path.exists():
        evidence_text = evidence_path.read_text(encoding="utf-8")
        defined_evidence = set(
            re.findall(r"^\| (XY-E\d{2}) \|", evidence_text, flags=re.MULTILINE)
        )
        used_evidence: set[str] = set()
        for relative in FIXTURE_MARKDOWN_FILES:
            path = fixture / relative
            if path.exists():
                used_evidence.update(
                    re.findall(r"XY-E\d{2}", path.read_text(encoding="utf-8"))
                )
        undefined_evidence = used_evidence - defined_evidence
        if undefined_evidence:
            errors.append(f"内置小月演练资料引用了未定义证据：{sorted(undefined_evidence)}")

    scenarios_path = fixture / "scenarios.json"
    if not scenarios_path.exists():
        errors.append("内置小月演练资料缺少 scenarios.json")
        return errors
    try:
        scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"内置场景 JSON 无法解析：{exc}")
        return errors

    mapped_ids = set(scenarios.get("skills", {}))
    if scenarios.get("fixture_id") != "xiaoyue":
        errors.append("内置演练 fixture_id 必须为 xiaoyue")
    if scenarios.get("fixture_name") != "小月":
        errors.append("内置演练显示名必须为小月")
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


def check_baseline_locks(root: Path, queue_ids: set[str]) -> list[str]:
    errors: list[str] = []
    locks_path = root / "inventory/baseline-locks.json"
    if not locks_path.exists():
        return ["缺少 inventory/baseline-locks.json 原始基线锁"]
    try:
        lock_data = json.loads(locks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"原始基线锁无法解析：{exc}"]
    if lock_data.get("algorithm") != "sha256":
        errors.append("原始基线锁算法必须为 sha256")
    locks = lock_data.get("skills", {})
    if set(locks) != queue_ids:
        errors.append("原始基线锁与 32 个操盘手文案 Skill 不一致")
    for skill_id in queue_ids:
        original_path = root / "skills" / skill_id / "references/original.md"
        if not original_path.exists():
            errors.append(f"{skill_id} 缺少 references/original.md 原始基线")
            continue
        actual = hashlib.sha256(original_path.read_bytes()).hexdigest()
        if locks.get(skill_id) != actual:
            errors.append(f"{skill_id} 的原始基线与锁定哈希不一致")
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
    errors.extend(check_baseline_locks(root, order_ids))

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
