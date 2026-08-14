import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/clipmind-skill-tuner/scripts"
SCRIPT = SCRIPTS / "project_check.py"


class ProjectCheckTest(unittest.TestCase):
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
        sys.path.insert(0, str(SCRIPTS))
        try:
            spec = importlib.util.spec_from_file_location("project_check", SCRIPT)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            self.assertEqual([], module.run_checks(ROOT))
        finally:
            sys.path.remove(str(SCRIPTS))


if __name__ == "__main__":
    unittest.main()
