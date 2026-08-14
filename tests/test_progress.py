import importlib.util
import inspect
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/clipmind-skill-tuner/scripts/progress.py"


def load_progress_module():
    spec = importlib.util.spec_from_file_location("progress", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ProgressTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.progress = load_progress_module()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="skill-progress-test-")
        self.state_path = Path(self.temp_dir.name) / "progress.json"
        self.order = [
            {"order": 1, "skill_id": "skill-a", "mode": "tune", "name": "A"},
            {"order": 2, "skill_id": "skill-b", "mode": "review", "name": "B"},
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_project_root(self) -> Path:
        project_root = Path(self.temp_dir.name) / "project"
        shutil.copytree(
            ROOT / "fixtures/ip/赵玥玥",
            project_root / "fixtures/ip/赵玥玥",
        )
        (project_root / "IP素材库/原始材料").mkdir(parents=True)
        return project_root

    def test_seeds_builtin_fixture_into_empty_material_library(self):
        project_root = self.make_project_root()
        self.assertTrue(hasattr(self.progress, "seed_builtin_fixture"))

        seeded = self.progress.seed_builtin_fixture(project_root)

        self.assertTrue(seeded)
        for relative in ("PROFILE.md", "MATERIALS.md", "EVIDENCE-INDEX.md"):
            expected = (project_root / "fixtures/ip/赵玥玥" / relative).read_text(
                encoding="utf-8"
            )
            actual = (project_root / "IP素材库" / relative).read_text(encoding="utf-8")
            self.assertEqual(expected, actual)
        self.assertTrue((project_root / "IP素材库/原始材料/01-人物访谈.md").exists())

    def test_does_not_seed_over_existing_user_material(self):
        project_root = self.make_project_root()
        user_material = project_root / "IP素材库/原始材料/我的真实资料.md"
        user_material.write_text("用户资料", encoding="utf-8")
        self.assertTrue(hasattr(self.progress, "seed_builtin_fixture"))

        seeded = self.progress.seed_builtin_fixture(project_root)

        self.assertFalse(seeded)
        self.assertEqual("用户资料", user_material.read_text(encoding="utf-8"))
        self.assertFalse((project_root / "IP素材库/PROFILE.md").exists())
        self.assertFalse((project_root / "IP素材库/原始材料/01-人物访谈.md").exists())

    def test_initial_state_marks_builtin_fixture_ready(self):
        project_root = self.make_project_root()
        self.assertIn(
            "project_root",
            inspect.signature(self.progress.load_or_initialize).parameters,
        )

        state = self.progress.load_or_initialize(
            self.state_path,
            self.order,
            project_root=project_root,
        )

        self.assertEqual("ready", state["ip_profile_status"])
        self.assertEqual("builtin_fixture", state["profile_mode"])
        self.assertEqual("zhao-yueyue", state["active_ip_fixture"])

    def test_existing_state_is_reconciled_to_current_queue(self):
        existing = {
            "version": 1,
            "ip_profile_status": "ready",
            "active_skill": "removed-skill",
            "skills": {
                "skill-a": {"status": "completed", "rounds": 2, "completed_at": "x"},
                "removed-skill": {"status": "in_progress", "rounds": 1, "completed_at": None},
            },
        }
        self.state_path.write_text(json.dumps(existing), encoding="utf-8")

        state = self.progress.load_or_initialize(self.state_path, self.order)

        self.assertIsNone(state["active_skill"])
        self.assertNotIn("removed-skill", state["skills"])
        self.assertEqual("completed", state["skills"]["skill-a"]["status"])
        self.assertIn("skill-b", state["skills"])

    def test_initialize_and_advance(self):
        state = self.progress.load_or_initialize(self.state_path, self.order)
        self.assertEqual("skill-a", self.progress.next_item(state, self.order)["skill_id"])

        self.progress.mark_started(state, "skill-a")
        self.progress.save_state(self.state_path, state)
        reloaded = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual("in_progress", reloaded["skills"]["skill-a"]["status"])

        self.progress.mark_completed(reloaded, "skill-a", 3)
        self.assertEqual("skill-b", self.progress.next_item(reloaded, self.order)["skill_id"])
        self.assertEqual(3, reloaded["skills"]["skill-a"]["rounds"])

    def test_cannot_start_two_skills_at_once(self):
        state = self.progress.load_or_initialize(self.state_path, self.order)
        self.progress.mark_started(state, "skill-a")
        with self.assertRaises(ValueError):
            self.progress.mark_started(state, "skill-b")


if __name__ == "__main__":
    unittest.main()
