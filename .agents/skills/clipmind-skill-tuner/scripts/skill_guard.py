#!/usr/bin/env python3
"""Validate that a tuned ClipMind transport Skill preserves its platform contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional


START = "<!-- CLIPMIND_DEFINITION_START -->"
END = "<!-- CLIPMIND_DEFINITION_END -->"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
JSON_FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
VARIABLE_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
RISKY_ACTION_RE = re.compile(r"自动(?:发布|评论|投放|发送|写入|保存)|改变(?:业务)?状态|直接(?:发布|投放|写库)")
SAFE_QUALIFIERS = ("不得", "不要", "禁止", "不能", "不可", "仅", "只", "等待人工", "人工确认")
COPY_ONLY_VISUAL_MARKERS = ("画面", "图片", "截图", "版式", "配图", "构图", "颜色", "字体", "留白", "视觉")


class ValidationResult:
    def __init__(self, errors: list[str] | None = None):
        self.errors = errors or []

    @property
    def ok(self) -> bool:
        return not self.errors


def split_definition(text: str) -> tuple[str, str, str]:
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("平台定义标记缺失或重复")
    before, rest = text.split(START, 1)
    definition, after = rest.split(END, 1)
    return before, definition, after


def heading_sequence(text: str) -> list[tuple[int, str]]:
    return [(len(level), title) for level, title in HEADING_RE.findall(text)]


def section(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^(?P<level>#{{1,6}})\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^#{{1,{6}}}\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(0) if match else None


def labeled_block(text: str, start_label: str, end_label: str) -> str | None:
    pattern = re.compile(
        rf"^{re.escape(start_label)}\s*$\n.*?(?=^{re.escape(end_label)}\s*$)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(0) if match else None


def json_shapes(text: str) -> list[Any]:
    shapes: list[Any] = []
    for raw in JSON_FENCE_RE.findall(text):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        shapes.append(shape_of(value))
    return shapes


def shape_of(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: shape_of(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        if not value:
            return []
        return [shape_of(value[0])]
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if value is None:
        return "null"
    return "str"


def contract_lines(text: str) -> Counter[str]:
    protected_markers = (
        "不得自动",
        "不得编造",
        "不得输出 final",
        "只生成草案",
        "人工确认",
        "requires_human_review",
        "no_final_business_status",
        "no_fabricated_business_ids",
    )
    lines = []
    for line in text.splitlines():
        normalized = line.strip()
        if normalized and any(marker in normalized for marker in protected_markers):
            lines.append(normalized)
    return Counter(lines)


def added_lines(original: str, candidate: str) -> list[str]:
    baseline = Counter(line.strip() for line in original.splitlines() if line.strip())
    revised = Counter(line.strip() for line in candidate.splitlines() if line.strip())
    added: list[str] = []
    for line, count in (revised - baseline).items():
        added.extend([line] * count)
    return added


def marked_lines(text: str, markers: tuple[str, ...]) -> Counter[str]:
    return Counter(
        line.strip()
        for line in text.splitlines()
        if line.strip() and any(marker in line for marker in markers)
    )


def validate_operator_scope(
    skill_dir: Path,
    project_root: Optional[Path],
    original: str,
    errors: list[str],
) -> None:
    if project_root is None:
        errors.append("缺少 Skill Forge 项目根目录，无法执行操盘手调优范围检查")
        return
    queue_path = project_root / "inventory/tuning-order.json"
    locks_path = project_root / "inventory/baseline-locks.json"
    if not queue_path.exists() or not locks_path.exists():
        errors.append("缺少操盘手调试队列或原始基线锁")
        return

    queue = json.loads(queue_path.read_text(encoding="utf-8"))["skills"]
    queue_ids = {item["skill_id"] for item in queue}
    skill_id = skill_dir.name
    if skill_id not in queue_ids:
        errors.append("当前 Skill 不在 32 个默认文案调试队列中，操盘手不得直接调优或打包")
        return

    lock_data = json.loads(locks_path.read_text(encoding="utf-8"))
    expected_hash = lock_data.get("skills", {}).get(skill_id)
    actual_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
    if not expected_hash:
        errors.append("当前 Skill 缺少原始基线锁")
    elif actual_hash != expected_hash:
        errors.append("references/original.md 原始基线与锁定版本不一致，禁止继续调优")


def validate_no_new_external_actions(original: str, candidate: str, errors: list[str]) -> None:
    for line in added_lines(original, candidate):
        if RISKY_ACTION_RE.search(line) and not any(qualifier in line for qualifier in SAFE_QUALIFIERS):
            errors.append("新增规则要求执行发布、投放、写入或状态变更，越过人工业务边界")
            break
        if re.search(r"\bpermissions?\b|必需工具|条件工具|调用工具", line, re.IGNORECASE):
            errors.append("新增规则涉及工具或权限变化，必须转工程任务")
            break


def first_body_paragraph(markdown_section: str | None) -> str | None:
    if markdown_section is None:
        return None
    lines = markdown_section.splitlines()[1:]
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line)
        elif current:
            paragraphs.append("\n".join(current))
            current = []
            break
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs[0] if paragraphs else None


def validate_common(original: str, candidate: str, errors: list[str]) -> tuple[str, str]:
    try:
        original_before, original_definition, original_after = split_definition(original)
        candidate_before, candidate_definition, candidate_after = split_definition(candidate)
    except ValueError as exc:
        errors.append(str(exc))
        return "", ""

    if (original_before, original_after) != (candidate_before, candidate_after):
        errors.append("平台定义之外的 Skill 封装被修改；用途、调用前提、输出契约和调优规则必须保持原样")
    if heading_sequence(original) != heading_sequence(candidate):
        errors.append("标题与大体结构发生变化；只能修改反馈涉及的既有板块")
    return original_definition, candidate_definition


def validate_agent(original: str, candidate: str, errors: list[str]) -> None:
    protected_pairs = [
        ("角色定位:", "适用场景:", "角色定位"),
        ("适用场景:", "必需输入:", "适用场景"),
        ("必需输入:", "处理步骤:", "必需输入"),
        ("输出结构:", "质量标准:", "输出结构"),
        ("边界与护栏:", "人工确认边界:", "边界与护栏"),
        ("人工确认边界:", "Skill 封装说明:", "人工确认边界"),
        ("Skill 封装说明:", "### 机器可核对的输入契约", "工具、权限与 Skill 身份"),
    ]
    for start_label, end_label, label in protected_pairs:
        baseline = labeled_block(original, start_label, end_label)
        revised = labeled_block(candidate, start_label, end_label)
        if baseline is not None and baseline != revised:
            errors.append(f"{label}属于平台契约，不得由操盘手调试修改")

    for title in ("机器可核对的输入契约", "机器可核对的输出契约", "护栏"):
        if section(original, title) != section(candidate, title):
            errors.append(f"{title}属于平台契约，不得修改")

    original_role = next((line for line in original.splitlines() if line.startswith("你是「")), None)
    candidate_role = next((line for line in candidate.splitlines() if line.startswith("你是「")), None)
    if original_role != candidate_role:
        errors.append("Skill 角色名称不得修改")
    if json_shapes(original) != json_shapes(candidate):
        errors.append("参考输入输出或机器契约的字段结构发生变化")
    if contract_lines(original) != contract_lines(candidate):
        errors.append("证据、禁止外部动作或人工确认语义发生变化")
    validate_no_new_external_actions(original, candidate, errors)


def validate_sop(original: str, candidate: str, errors: list[str]) -> None:
    for title in (
        "原始 Prompt 元数据",
        "机器可核对的输入契约",
        "机器可核对的输出契约",
        "输入契约",
        "输出契约",
    ):
        baseline = section(original, title)
        if baseline is not None and baseline != section(candidate, title):
            errors.append(f"{title}属于平台元数据或契约，不得修改")
    if Counter(VARIABLE_RE.findall(original)) != Counter(VARIABLE_RE.findall(candidate)):
        errors.append("Prompt 输入变量集合发生变化")
    if json_shapes(original) != json_shapes(candidate):
        errors.append("JSON 输出字段、类型或层级发生变化")
    if contract_lines(original) != contract_lines(candidate):
        errors.append("证据、禁止外部动作或人工确认语义发生变化")
    original_execution = first_body_paragraph(section(original, "原始执行正文"))
    candidate_execution = first_body_paragraph(section(candidate, "原始执行正文"))
    if original_execution is not None and original_execution != candidate_execution:
        errors.append("SOP 的角色和原始任务职责不得修改")
    validate_no_new_external_actions(original, candidate, errors)


def validate_image(original: str, candidate: str, errors: list[str]) -> None:
    pattern = re.compile(
        r"(?P<prefix>### 原始生图 Prompt\s*\n\s*```text\s*\n)(?P<prompt>.*?)(?P<suffix>\n```)",
        re.DOTALL,
    )
    original_match = pattern.search(original)
    candidate_match = pattern.search(candidate)
    if not original_match or not candidate_match:
        errors.append("无法识别原始生图 Prompt 板块")
        return
    original_shell = original[: original_match.start("prompt")] + "<PROMPT>" + original[original_match.end("prompt") :]
    candidate_shell = candidate[: candidate_match.start("prompt")] + "<PROMPT>" + candidate[candidate_match.end("prompt") :]
    if original_shell != candidate_shell:
        errors.append("生图 Skill 只能修改“原始生图 Prompt”正文；ID、类型、用途、尺寸和变量不得修改")
    if candidate_match.group("prompt").count("{subject}") != original_match.group("prompt").count("{subject}"):
        errors.append("生图 Prompt 必须保留原有 {subject} 变量")


def validate_skill_dir(
    skill_dir: Path,
    project_root: Optional[Path] = None,
    enforce_operator_scope: bool = False,
) -> ValidationResult:
    skill_dir = Path(skill_dir)
    candidate_path = skill_dir / "SKILL.md"
    original_path = skill_dir / "references/original.md"
    errors: list[str] = []
    if not candidate_path.exists() or not original_path.exists():
        return ValidationResult(["缺少 SKILL.md 或 references/original.md"])

    original = original_path.read_text(encoding="utf-8")
    candidate = candidate_path.read_text(encoding="utf-8")
    skill_id = skill_dir.name
    if enforce_operator_scope:
        validate_operator_scope(skill_dir, project_root, original, errors)

    if skill_id.startswith("clipmind-governance-"):
        if candidate != original:
            errors.append("治理 Skill 是 ClipMind 只读质量镜；操盘手调试不得修改，需输出工程变更建议单")
        return ValidationResult(errors)

    original_definition, candidate_definition = validate_common(original, candidate, errors)
    if not original_definition or not candidate_definition:
        return ValidationResult(errors)

    if skill_id.startswith("clipmind-agent-"):
        validate_agent(original_definition, candidate_definition, errors)
        if (
            skill_id == "clipmind-agent-xhs-graphic-note"
            and marked_lines(original_definition, COPY_ONLY_VISUAL_MARKERS)
            != marked_lines(candidate_definition, COPY_ONLY_VISUAL_MARKERS)
        ):
            errors.append("小红书图文 Skill 的视觉方法属于冻结结构；操盘手只能调整文字判断与表达")
    elif skill_id.startswith("clipmind-sop-"):
        validate_sop(original_definition, candidate_definition, errors)
    elif skill_id.startswith("clipmind-image-"):
        validate_image(original_definition, candidate_definition, errors)
    else:
        errors.append(f"未知 Skill 类型：{skill_id}")
    return ValidationResult(list(dict.fromkeys(errors)))


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Skill 调优是否越过 ClipMind 平台契约")
    parser.add_argument("skill_dir", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    result = validate_skill_dir(
        args.skill_dir,
        project_root=root,
        enforce_operator_scope=True,
    )
    if result.ok:
        print("PASS：改动位于允许调优范围，平台契约未发现变化。")
        return 0
    print("BLOCKED：本轮改动触碰不可修改边界：")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
