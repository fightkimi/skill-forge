import importlib.util
import json
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
