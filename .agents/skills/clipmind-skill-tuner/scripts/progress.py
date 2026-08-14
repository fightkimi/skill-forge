#!/usr/bin/env python3
"""Keep one-Skill-per-conversation tuning progress in a local ignored file."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


BUILTIN_FIXTURE_ID = "xiaoyue"
BUILTIN_FIXTURE_DIR = Path("fixtures/ip/小月")
CURRENT_PROFILE_HEADING = "# 小月 IP 档案"
LEGACY_PROFILE_HEADING = "# 赵玥玥 IP 档案"
PROFILE_FILES = ("PROFILE.md", "MATERIALS.md", "EVIDENCE-INDEX.md")
RAW_MATERIAL_FILES = (
    "01-人物访谈.md",
    "02-业务与产品.md",
    "03-用户访谈与评论.md",
    "04-案例记录.md",
    "05-表达语料.md",
    "06-历史内容样本.md",
    "07-内容表现数据.md",
    "08-阶段目标与选题池.md",
)
LEGACY_FIXTURE_SHA256 = {
    "PROFILE.md": "18b1fc4fa5dea41af7dd155d8e7b3d5489ca1eda5470c8e5ebe141f1d8d9b48e",
    "MATERIALS.md": "71e5d459a04186e23ccb3175a81ef5156cb939e74e73b7790d5df48b9e119c27",
    "EVIDENCE-INDEX.md": "b7290078595e13727368cff911d6a469f34c5c065c9b09103e7bf3e7872871ca",
    "原始材料/01-人物访谈.md": "1e0819f2ea5e8581e50c492c585962984c0dd523bc39b94fb004be45b6d7113e",
    "原始材料/02-业务与产品.md": "5ce03bfca3304a7763a7a84a1f83fbe3628a7f5aea600234ce9d79a82cdebd69",
    "原始材料/03-用户访谈与评论.md": "932486cee644a6520faab9ae8e64150f094326b9a8a5ab22cdba5793a1dbb2ca",
    "原始材料/04-案例记录.md": "ada0afd8dbda430cbce87e2bf3a61b4c80bdcd306a8a3ce8e95e3d9864e25840",
    "原始材料/05-表达语料.md": "2e78c6ef01a807952bba30db3fb171ec79374bf69337ad5ad6a7232b6c24b133",
    "原始材料/06-历史内容样本.md": "e44dbdf06bdaba43670b44aaa6ecb37a2e32f7be7e9809ef2eb678cf4c226328",
    "原始材料/07-内容表现数据.md": "b004941aa5adab4785ec6465a1de08432af574afa20a2966106574289c8e5e03",
    "原始材料/08-阶段目标与选题池.md": "71ac1ce91456afd8c880f1da3d4d551bca3a31096913bfddc613b5aa5b55bf6e",
}
LEGACY_FIXTURE_SHA256_ALIASES = {
    "原始材料/06-历史内容样本.md": {
        "7d795bdba70e03bdff18799d59e01b8456592772e178e11e6781c54118d39e43",
    },
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_order(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["skills"] if isinstance(data, dict) else data


def order_index(order: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["skill_id"]: item for item in order}


def incomplete_dependencies(
    state: dict[str, Any],
    item: dict[str, Any],
) -> list[str]:
    return [
        skill_id
        for skill_id in item.get("depends_on", [])
        if state["skills"].get(skill_id, {}).get("status") != "completed"
    ]


def accepted_output_path(state: dict[str, Any], skill_id: str) -> str:
    rounds = int(state["skills"].get(skill_id, {}).get("rounds", 0))
    return f"tuning-records/{skill_id}/round-{rounds:02d}-output.md"


def validate_accepted_output(
    records_root: Path,
    skill_id: str,
    expected_rounds: Optional[int] = None,
) -> list[str]:
    record_dir = records_root / skill_id
    acceptance_path = record_dir / "acceptance.json"
    if not acceptance_path.exists():
        return [f"{skill_id} 缺少操盘手确认凭据和已确认输出"]
    try:
        acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"{skill_id} 的操盘手确认凭据无法解析"]
    rounds = acceptance.get("rounds")
    if (
        acceptance.get("skill_id") != skill_id
        or acceptance.get("operator_confirmed") is not True
        or not isinstance(rounds, int)
        or rounds < 1
    ):
        return [f"{skill_id} 尚无有效的操盘手已确认输出"]
    if expected_rounds is not None and rounds != expected_rounds:
        return [
            f"{skill_id} 的操盘手确认轮数与进度不一致"
            f"（确认 {rounds}，进度 {expected_rounds}）"
        ]
    output_path = record_dir / f"round-{rounds:02d}-output.md"
    if not output_path.exists():
        return [f"{skill_id} 缺少第 {rounds} 轮已确认输出"]
    return []


def material_library_has_user_content(root: Path) -> bool:
    library = root / "IP素材库"
    if any((library / name).exists() for name in PROFILE_FILES):
        return True
    raw_materials = library / "原始材料"
    if not raw_materials.exists():
        return False
    return any(path.name != ".gitkeep" for path in raw_materials.iterdir())


def material_library_matches_builtin(root: Path, profile_heading: str) -> bool:
    library = root / "IP素材库"
    profile = library / "PROFILE.md"
    raw_materials = library / "原始材料"
    if not profile.exists() or not raw_materials.exists():
        return False
    profile_text = profile.read_text(encoding="utf-8")
    if not profile_text.startswith(profile_heading):
        return False
    if "MOCK 合成演练数据" not in "\n".join(profile_text.splitlines()[:4]):
        return False
    if not all((library / name).exists() for name in PROFILE_FILES):
        return False
    raw_names = {
        path.name
        for path in raw_materials.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    }
    return raw_names == set(RAW_MATERIAL_FILES)


def material_library_matches_legacy(root: Path) -> bool:
    library = root / "IP素材库"
    profile = library / "PROFILE.md"
    raw_materials = library / "原始材料"
    if not profile.exists() or not raw_materials.exists():
        return False
    profile_text = profile.read_text(encoding="utf-8")
    if not profile_text.startswith(LEGACY_PROFILE_HEADING):
        return False
    if "MOCK 合成演练数据" not in "\n".join(profile_text.splitlines()[:4]):
        return False
    if not all((library / name).exists() for name in PROFILE_FILES):
        return False
    raw_names = {
        path.name
        for path in raw_materials.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    }
    if not raw_names.issubset(set(RAW_MATERIAL_FILES)):
        return False
    existing = list(PROFILE_FILES) + [
        f"原始材料/{name}" for name in sorted(raw_names)
    ]
    for relative in existing:
        actual = hashlib.sha256((library / relative).read_bytes()).hexdigest()
        expected = LEGACY_FIXTURE_SHA256[relative]
        aliases = LEGACY_FIXTURE_SHA256_ALIASES.get(relative, set())
        if actual != expected and actual not in aliases:
            return False
    return True


def seed_builtin_fixture(root: Path, replace_legacy: bool = False) -> bool:
    fixture = root / BUILTIN_FIXTURE_DIR
    library = root / "IP素材库"
    if material_library_has_user_content(root):
        if not (
            replace_legacy
            and material_library_matches_legacy(root)
        ):
            return False
    missing = [name for name in PROFILE_FILES if not (fixture / name).exists()]
    raw_source = fixture / "原始材料"
    missing_raw = [name for name in RAW_MATERIAL_FILES if not (raw_source / name).exists()]
    if missing or missing_raw:
        incomplete = missing + missing_raw
        raise FileNotFoundError(f"内置小月演练资料不完整：{', '.join(incomplete)}")

    library.mkdir(parents=True, exist_ok=True)
    raw_target = library / "原始材料"
    raw_target.mkdir(parents=True, exist_ok=True)
    for name in PROFILE_FILES:
        shutil.copy2(fixture / name, library / name)
    for name in RAW_MATERIAL_FILES:
        shutil.copy2(raw_source / name, raw_target / name)
    return True


def reconcile_state(state: dict[str, Any], order: list[dict[str, Any]]) -> None:
    previous = state.get("skills", {})
    allowed_ids = [item["skill_id"] for item in order]
    state["skills"] = {
        skill_id: previous.get(
            skill_id,
            {"status": "pending", "rounds": 0, "completed_at": None},
        )
        for skill_id in allowed_ids
    }
    if state.get("active_skill") not in set(allowed_ids):
        state["active_skill"] = None


def load_or_initialize(
    state_path: Path,
    order: list[dict[str, Any]],
    project_root: Optional[Path] = None,
) -> dict[str, Any]:
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        state = {
            "version": 3,
            "ip_profile_status": "not_ready",
            "profile_mode": "unconfigured",
            "active_ip_fixture": None,
            "active_skill": None,
            "created_at": now(),
            "updated_at": now(),
            "skills": {},
        }

    reconcile_state(state, order)
    state["version"] = 3
    state.setdefault("profile_mode", "unconfigured")
    state.setdefault("active_ip_fixture", None)
    if project_root is not None:
        legacy_builtin = material_library_matches_legacy(project_root)
        seeded = seed_builtin_fixture(
            project_root,
            replace_legacy=legacy_builtin,
        )
        current_builtin = material_library_matches_builtin(
            project_root,
            CURRENT_PROFILE_HEADING,
        )
        if seeded or current_builtin:
            state["ip_profile_status"] = "ready"
            state["profile_mode"] = "builtin_fixture"
            state["active_ip_fixture"] = BUILTIN_FIXTURE_ID
        elif legacy_builtin:
            state["profile_mode"] = "user_material"
            state["active_ip_fixture"] = None
    save_state(state_path, state)
    return state


def save_state(state_path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = state_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(state_path)


def next_item(state: dict[str, Any], order: list[dict[str, Any]]) -> dict[str, Any] | None:
    active = state.get("active_skill")
    if active:
        return next((item for item in order if item["skill_id"] == active), None)
    for item in order:
        if (
            state["skills"].get(item["skill_id"], {}).get("status") != "completed"
            and not incomplete_dependencies(state, item)
        ):
            return item
    return None


def item_card(
    state: dict[str, Any],
    order: list[dict[str, Any]],
    item: dict[str, Any],
) -> dict[str, Any]:
    by_id = order_index(order)
    dependencies = []
    for dependency_id in item.get("depends_on", []):
        dependency = by_id[dependency_id]
        dependencies.append(
            {
                "skill_id": dependency_id,
                "name": dependency["name"],
                "status": state["skills"][dependency_id]["status"],
                "output_label": dependency["output_label"],
            }
        )
    upstream_outputs = []
    for dependency_id in item.get("consumes_outputs_from", []):
        dependency = by_id[dependency_id]
        upstream_outputs.append(
            {
                "skill_id": dependency_id,
                "name": dependency["name"],
                "output_label": dependency["output_label"],
                "path": accepted_output_path(state, dependency_id),
            }
        )
    return {
        "display_title": f"第 {item['order']}/{len(order)} 个 · {item['name']}",
        "order": item["order"],
        "total": len(order),
        "skill_id": item["skill_id"],
        "name": item["name"],
        "phase": item.get("phase"),
        "phase_name": item.get("phase_name"),
        "status": state["skills"][item["skill_id"]]["status"],
        "purpose": item.get("purpose", ""),
        "selection_reason": item["selection_reason"],
        "output_label": item["output_label"],
        "dependencies": dependencies,
        "upstream_outputs": upstream_outputs,
    }


def current_card(
    state: dict[str, Any],
    order: list[dict[str, Any]],
) -> dict[str, Any] | None:
    active = state.get("active_skill")
    if not active:
        return None
    item = order_index(order).get(active)
    return item_card(state, order, item) if item else None


def mark_started(
    state: dict[str, Any],
    order: list[dict[str, Any]],
    skill_id: str,
    records_root: Optional[Path] = None,
) -> None:
    active = state.get("active_skill")
    if active and active != skill_id:
        raise ValueError(f"已有正在调试的 Skill：{active}。请先完成它，不能在同一对话串入 {skill_id}。")
    if skill_id not in state["skills"]:
        raise ValueError(f"未知 Skill：{skill_id}")
    item = order_index(order).get(skill_id)
    if item is None:
        raise ValueError(f"Skill 不在当前调试顺序中：{skill_id}")
    missing = incomplete_dependencies(state, item)
    if missing:
        by_id = order_index(order)
        labels = [f"{by_id[dependency_id]['name']}（{dependency_id}）" for dependency_id in missing]
        raise ValueError(f"当前 Skill 尚未解锁；请先完成：{'、'.join(labels)}")
    if records_root is not None:
        errors = []
        for dependency_id in item.get("consumes_outputs_from", []):
            expected_rounds = int(state["skills"][dependency_id].get("rounds", 0))
            errors.extend(
                validate_accepted_output(
                    records_root,
                    dependency_id,
                    expected_rounds=expected_rounds,
                )
            )
        if errors:
            raise ValueError("无法读取上游已确认输出：" + "；".join(errors))
    state["active_skill"] = skill_id
    state["skills"][skill_id]["status"] = "in_progress"


def mark_completed(
    state: dict[str, Any],
    skill_id: str,
    rounds: int,
    records_root: Optional[Path] = None,
) -> None:
    if state.get("active_skill") != skill_id:
        active = state.get("active_skill") or "无"
        raise ValueError(f"当前正在调试 {active}，不能完成 {skill_id}")
    if skill_id not in state["skills"]:
        raise ValueError(f"未知 Skill：{skill_id}")
    if records_root is not None:
        errors = validate_accepted_output(
            records_root,
            skill_id,
            expected_rounds=rounds,
        )
        if errors:
            raise ValueError("当前 Skill 缺少已确认输出：" + "；".join(errors))
    state["skills"][skill_id] = {
        "status": "completed",
        "rounds": rounds,
        "completed_at": now(),
    }
    state["active_skill"] = None


def summary(state: dict[str, Any], order: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"pending": 0, "in_progress": 0, "completed": 0}
    for item in order:
        status = state["skills"][item["skill_id"]]["status"]
        counts[status] = counts.get(status, 0) + 1
    return {
        **counts,
        "total": len(order),
        "active_skill": state.get("active_skill"),
        "current_skill": current_card(state, order),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description="读取或更新 Skill Forge 本地调试进度")
    parser.add_argument(
        "command",
        choices=("init", "next", "start", "complete", "status", "current", "profile-ready"),
    )
    parser.add_argument("skill_id", nargs="?")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--order", type=Path, default=root / "inventory/tuning-order.json")
    parser.add_argument("--state", type=Path, default=root / ".skill-forge/progress.json")
    args = parser.parse_args()

    order = load_order(args.order)
    state = load_or_initialize(args.state, order, project_root=root)
    try:
        if args.command == "profile-ready":
            state["ip_profile_status"] = "ready"
            if state.get("profile_mode") != "builtin_fixture":
                state["profile_mode"] = "user_material"
                state["active_ip_fixture"] = None
            save_state(args.state, state)
        elif args.command == "start":
            if not args.skill_id:
                parser.error("start 需要 skill_id")
            mark_started(
                state,
                order,
                args.skill_id,
                records_root=root / "tuning-records",
            )
            save_state(args.state, state)
            print(json.dumps(current_card(state, order), ensure_ascii=False, indent=2))
            return 0
        elif args.command == "complete":
            if not args.skill_id:
                parser.error("complete 需要 skill_id")
            mark_completed(
                state,
                args.skill_id,
                args.rounds,
                records_root=root / "tuning-records",
            )
            save_state(args.state, state)
        elif args.command == "next":
            item = next_item(state, order)
            if item:
                print(json.dumps(item_card(state, order, item), ensure_ascii=False, indent=2))
            elif all(
                state["skills"][entry["skill_id"]]["status"] == "completed"
                for entry in order
            ):
                print("ALL_DONE")
            else:
                print("BLOCKED：仍有 Skill 未完成，但其依赖关系尚未满足。", file=sys.stderr)
                return 2
            return 0
        elif args.command == "current":
            card = current_card(state, order)
            if card is None:
                print("BLOCKED：当前没有正在调试的 Skill。", file=sys.stderr)
                return 2
            print(json.dumps(card, ensure_ascii=False, indent=2))
            return 0
        elif args.command in ("init", "status"):
            pass
        print(json.dumps(summary(state, order), ensure_ascii=False, indent=2))
        return 0
    except ValueError as exc:
        print(f"BLOCKED：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
