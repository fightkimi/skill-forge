#!/usr/bin/env python3
"""Keep one-Skill-per-conversation tuning progress in a local ignored file."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_order(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["skills"] if isinstance(data, dict) else data


def load_or_initialize(state_path: Path, order: list[dict[str, Any]]) -> dict[str, Any]:
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    state = {
        "version": 1,
        "ip_profile_status": "not_ready",
        "active_skill": None,
        "created_at": now(),
        "updated_at": now(),
        "skills": {
            item["skill_id"]: {"status": "pending", "rounds": 0, "completed_at": None}
            for item in order
        },
    }
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
        if state["skills"].get(item["skill_id"], {}).get("status") != "completed":
            return item
    return None


def mark_started(state: dict[str, Any], skill_id: str) -> None:
    active = state.get("active_skill")
    if active and active != skill_id:
        raise ValueError(f"已有正在调试的 Skill：{active}。请先完成它，不能在同一对话串入 {skill_id}。")
    if skill_id not in state["skills"]:
        raise ValueError(f"未知 Skill：{skill_id}")
    state["active_skill"] = skill_id
    state["skills"][skill_id]["status"] = "in_progress"


def mark_completed(state: dict[str, Any], skill_id: str, rounds: int) -> None:
    if state.get("active_skill") not in (None, skill_id):
        raise ValueError(f"当前正在调试 {state['active_skill']}，不能完成 {skill_id}")
    if skill_id not in state["skills"]:
        raise ValueError(f"未知 Skill：{skill_id}")
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
    return {**counts, "total": len(order), "active_skill": state.get("active_skill")}


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description="读取或更新 Skill Forge 本地调试进度")
    parser.add_argument("command", choices=("init", "next", "start", "complete", "status", "profile-ready"))
    parser.add_argument("skill_id", nargs="?")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--order", type=Path, default=root / "inventory/tuning-order.json")
    parser.add_argument("--state", type=Path, default=root / ".skill-forge/progress.json")
    args = parser.parse_args()

    order = load_order(args.order)
    state = load_or_initialize(args.state, order)
    try:
        if args.command == "profile-ready":
            state["ip_profile_status"] = "ready"
            save_state(args.state, state)
        elif args.command == "start":
            if not args.skill_id:
                parser.error("start 需要 skill_id")
            mark_started(state, args.skill_id)
            save_state(args.state, state)
        elif args.command == "complete":
            if not args.skill_id:
                parser.error("complete 需要 skill_id")
            mark_completed(state, args.skill_id, args.rounds)
            save_state(args.state, state)
        elif args.command == "next":
            item = next_item(state, order)
            print(json.dumps(item, ensure_ascii=False, indent=2) if item else "ALL_DONE")
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
