#!/usr/bin/env python3
"""Generate the ClipMind business-ordered tuning queue from the exported inventory."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


PHASES = {
    1: "IP 建档与定位基线",
    2: "策略与内容计划",
    3: "研究、素材与用户洞察",
    4: "爆款拆解与选题",
    5: "内容生产与表达",
    6: "转化承接与 Agent 交付",
    7: "发布、监控、复盘与方法",
    8: "视觉内容与生图",
    9: "共享质量组件（高影响面）",
    10: "治理质量镜（只读验收）",
}

AGENT_PHASE = {
    "研究与洞察": 3,
    "爆款拆解": 4,
    "选题与计划": 4,
    "短视频脚本": 5,
    "表达与改写": 5,
    "图文与笔记": 5,
    "转化承接": 6,
    "发布与投放": 7,
    "复盘与汇报": 7,
}

PROMPT_PHASE = {
    "客户建档": 1,
    "IP 档案与策略": 1,
    "内容策略": 2,
    "内容计划": 2,
    "素材观点": 3,
    "内容生产": 5,
    "Agent 工作台": 6,
    "IP 陪跑": 7,
    "投放": 7,
    "数据反馈": 7,
    "复盘": 7,
    "方法库": 7,
    "爆款方法库": 7,
    "视觉内容": 8,
    "全局质量底线": 9,
    "全局质量规范": 9,
}

PROMPT_PRIORITY = [
    "ip/s01_profile_extract",
    "ip/s01_profile_extract_aux",
    "ip/s01_profile_draft",
    "ip/s01_5_ip_breakdown",
    "ip/s02_diagnosis",
    "ip/s_language_extract",
    "ip/s03_stage_advice",
    "ip/s03_strategy_suggestion",
    "ip/s04_content_plan_suggestion",
    "ip/s04_content_topic_suggestion",
    "viewpoint/s06_1_collect",
    "viewpoint/s06_2_extract",
    "production/s06_3_match_positioning",
    "production/s06_4_match_emotion",
    "production/s06_5_script",
    "production/s06_6_review",
    "production/s06_7_reshoot",
    "agent_studio/title_summary",
    "agent_studio/s06_semantic_review",
    "agent_studio/s06_semantic_refine",
    "companion/briefing",
    "launch/s07_publish_suggestion",
    "feedback/s07_monitor_analysis",
    "retrospect/s09_summary",
    "method/s09_2_video_breakdown",
    "method/s09_method_extract",
    "method/s10_method_underlying_logic",
    "visual/cognition_viewpoints",
    "visual/cognition_refine",
    "visual/cognition_poster",
    "visual/cognition_visual_adjust",
    "core/s06_quality_floor",
    "core/s06_ondemand_language_gate",
    "core/s06_ondemand_persona_story",
    "core/s06_ondemand_script_rules",
    "core/s06_ondemand_chat_format",
    "core/s06_ondemand_deliverable",
    "core/s06_ondemand_structured_output",
    "core/s06_ondemand_touch_score",
    "core/s06_ondemand_low_effort_handoff",
]
PROMPT_PRIORITY_MAP = {key: index for index, key in enumerate(PROMPT_PRIORITY)}


def classify(item: dict) -> tuple[int, str, str]:
    item_type = item["类型"]
    category = item["分类"]
    if item_type == "agent":
        return AGENT_PHASE[category], "tune", "同一 IP、同一任务、同一材料前后对比"
    if item_type == "prompt":
        if item["原始标识"].startswith("core/"):
            return 9, "component_tune", "至少用 3 个宿主任务复测，避免影响其他内容能力"
        return PROMPT_PHASE[category], "tune", "同一 IP、同一任务、同一材料前后对比"
    if item_type == "image":
        return 8, "visual_tune", "同一主题与素材生成候选图，人工检查画面和文字"
    if item_type == "governance":
        return 10, "review_only", "只评审候选内容；不改治理定义，问题转工程建议单"
    raise ValueError(f"未知类型：{item_type}")


def sort_key(item: dict) -> tuple:
    phase, _, _ = classify(item)
    if item["类型"] == "prompt":
        priority = PROMPT_PRIORITY_MAP.get(item["原始标识"], 999)
    else:
        priority = 999
    return phase, priority, item["分类"], item["中文名称"], item["技术ID"]


def generate(root: Path) -> None:
    inventory = json.loads((root / "inventory/skills.json").read_text(encoding="utf-8"))["skills"]
    ordered = []
    for order, item in enumerate(sorted(inventory, key=sort_key), start=1):
        phase, mode, test_policy = classify(item)
        ordered.append(
            {
                "order": order,
                "phase": phase,
                "phase_name": PHASES[phase],
                "mode": mode,
                "skill_id": item["技术ID"],
                "name": item["中文名称"],
                "source_type": item["类型"],
                "source_id": item["原始标识"],
                "category": item["分类"],
                "purpose": item["使用用途"],
                "test_policy": test_policy,
            }
        )

    counts = Counter(item["mode"] for item in ordered)
    payload = {
        "total": len(ordered),
        "counts": dict(sorted(counts.items())),
        "phases": [{"phase": key, "name": value} for key, value in PHASES.items()],
        "skills": ordered,
    }
    (root / "inventory/tuning-order.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# ClipMind Skill 调试顺序",
        "",
        "顺序按真实业务链路安排，不按文件名排序。每个 Skill 单独开一个 Codex 对话。",
        "",
        f"- 可直接循环调优：{counts['tune']} 个。",
        f"- 生图循环调优：{counts['visual_tune']} 个。",
        f"- 共享组件受控调优：{counts['component_tune']} 个。",
        f"- 治理质量镜只读验收：{counts['review_only']} 个。",
        "",
        "> 治理 Skill 不直接生产业务内容，也不会注入运行时 Prompt。发现问题时生成工程变更建议单，不能由操盘手在本项目内直接改。",
    ]
    current_phase = None
    for item in ordered:
        if item["phase"] != current_phase:
            current_phase = item["phase"]
            lines.extend(["", f"## {current_phase}. {item['phase_name']}", "", "| 顺序 | 中文名称 | 类型 | 调试方式 |", "| ---: | --- | --- | --- |"])
        mode_label = {
            "tune": "内容循环调优",
            "visual_tune": "看图循环调优",
            "component_tune": "3 个宿主任务回归后调优",
            "review_only": "只读评审",
        }[item["mode"]]
        lines.append(f"| {item['order']} | {item['name']} | {item['source_type']} | {mode_label} |")
    (root / "调试顺序.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[4])
