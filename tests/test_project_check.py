import importlib.util
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/clipmind-skill-tuner/scripts"
SCRIPT = SCRIPTS / "project_check.py"


class ProjectCheckTest(unittest.TestCase):
    def test_operator_docs_describe_copy_only_fixture_workflow(self):
        docs = {
            "README.md": (ROOT / "README.md").read_text(encoding="utf-8"),
            "开始调试.md": (ROOT / "开始调试.md").read_text(encoding="utf-8"),
            "调试顺序.md": (ROOT / "调试顺序.md").read_text(encoding="utf-8"),
            "tuner": (
                ROOT / ".agents/skills/clipmind-skill-tuner/SKILL.md"
            ).read_text(encoding="utf-8"),
        }
        for name, text in docs.items():
            self.assertIn("32", text, name)
            self.assertIn("赵玥玥", text, name)
        self.assertIn("scenarios.json", docs["tuner"])
        self.assertIn("同一任务和材料", docs["tuner"])
        self.assertNotIn("88 个内容 Skill", docs["README.md"])
        self.assertNotIn("22 个生图 Skill", docs["README.md"])
        self.assertNotIn("治理 Skill 是例外", docs["开始调试.md"])

    def load_project_check(self):
        sys.path.insert(0, str(SCRIPTS))
        spec = importlib.util.spec_from_file_location("project_check", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_project_check_detects_incomplete_fixture(self):
        module = self.load_project_check()
        try:
            self.assertTrue(hasattr(module, "check_builtin_fixture"))
            with tempfile.TemporaryDirectory(prefix="skill-fixture-check-") as temp:
                temp_root = Path(temp)
                shutil.copytree(
                    ROOT / "fixtures/ip/赵玥玥",
                    temp_root / "fixtures/ip/赵玥玥",
                )
                (temp_root / "fixtures/ip/赵玥玥/scenarios.json").unlink()
                errors = module.check_builtin_fixture(temp_root, {"skill-a"})
                self.assertTrue(any("scenarios.json" in error for error in errors), errors)
        finally:
            sys.path.remove(str(SCRIPTS))

    def test_project_check_detects_baseline_drift(self):
        module = self.load_project_check()
        try:
            self.assertTrue(hasattr(module, "check_baseline_locks"))
            skill_id = "clipmind-agent-xhs-graphic-note"
            source = ROOT / "skills" / skill_id / "references/original.md"
            expected = hashlib.sha256(source.read_bytes()).hexdigest()
            with tempfile.TemporaryDirectory(prefix="skill-lock-check-") as temp:
                temp_root = Path(temp)
                original = temp_root / "skills" / skill_id / "references/original.md"
                original.parent.mkdir(parents=True)
                original.write_text(
                    source.read_text(encoding="utf-8") + "\n基线漂移",
                    encoding="utf-8",
                )
                inventory = temp_root / "inventory"
                inventory.mkdir()
                (inventory / "baseline-locks.json").write_text(
                    json.dumps({"algorithm": "sha256", "skills": {skill_id: expected}}),
                    encoding="utf-8",
                )

                errors = module.check_baseline_locks(temp_root, {skill_id})

                self.assertTrue(any("原始基线" in error for error in errors), errors)
        finally:
            sys.path.remove(str(SCRIPTS))

    def test_builtin_fixture_is_complete_synthetic_and_mapped_to_queue(self):
        fixture = ROOT / "fixtures/ip/赵玥玥"
        required_markdown = [
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
        ]
        for relative in required_markdown:
            path = fixture / relative
            self.assertTrue(path.exists(), relative)
            opening = "\n".join(path.read_text(encoding="utf-8").splitlines()[:4])
            self.assertIn("MOCK 合成演练数据", opening, relative)

        scenarios_path = fixture / "scenarios.json"
        self.assertTrue(scenarios_path.exists())
        scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
        queue = json.loads(
            (ROOT / "inventory/tuning-order.json").read_text(encoding="utf-8")
        )
        queue_ids = {item["skill_id"] for item in queue["skills"]}
        self.assertEqual("zhao-yueyue", scenarios["fixture_id"])
        self.assertEqual(queue_ids, set(scenarios["skills"]))
        for skill_id, scenario in scenarios["skills"].items():
            self.assertTrue(scenario["task"].strip(), skill_id)
            self.assertTrue(scenario["materials"], skill_id)
            for relative in scenario["materials"]:
                self.assertTrue((fixture / relative).exists(), f"{skill_id}: {relative}")

    def test_operator_queue_contains_only_approved_copy_skills(self):
        data = json.loads(
            (ROOT / "inventory/tuning-order.json").read_text(encoding="utf-8")
        )
        queue = data["skills"]
        expected_source_orders = {
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
            17, 18, 28, 32, 33, 34, 35, 36,
            39, 43, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
        }

        self.assertEqual(32, data["total"])
        self.assertEqual({"tune": 32}, data["counts"])
        self.assertEqual(32, len(queue))
        self.assertEqual(
            expected_source_orders,
            {item.get("source_order") for item in queue},
        )
        self.assertEqual(list(range(1, 33)), [item["order"] for item in queue])

    def test_optional_copy_skills_are_separate_and_disabled(self):
        optional_path = ROOT / "inventory/optional-copy-skills.json"
        self.assertTrue(optional_path.exists())
        optional = json.loads(optional_path.read_text(encoding="utf-8"))
        default = json.loads(
            (ROOT / "inventory/tuning-order.json").read_text(encoding="utf-8")
        )
        expected_source_orders = {26, 30, 44, 60, 62, 63, 64}
        default_ids = {item["skill_id"] for item in default["skills"]}
        optional_ids = {item["skill_id"] for item in optional["skills"]}

        self.assertFalse(optional["enabled_by_default"])
        self.assertEqual(7, optional["total"])
        self.assertEqual(
            expected_source_orders,
            {item.get("source_order") for item in optional["skills"]},
        )
        self.assertTrue(default_ids.isdisjoint(optional_ids))

    def test_distributable_project_is_consistent(self):
        module = self.load_project_check()
        try:
            self.assertEqual([], module.run_checks(ROOT))
        finally:
            sys.path.remove(str(SCRIPTS))


if __name__ == "__main__":
    unittest.main()
