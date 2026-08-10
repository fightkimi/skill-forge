import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/clipmind-skill-tuner/scripts"
SCRIPT = SCRIPTS / "finalize.py"


class FinalizeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(SCRIPTS))
        spec = importlib.util.spec_from_file_location("finalize", SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(str(SCRIPTS))

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="skill-finalize-test-")
        self.temp_root = Path(self.temp_dir.name)
        (self.temp_root / "skills").mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def copy_skill(self, skill_id: str):
        shutil.copytree(ROOT / "skills" / skill_id, self.temp_root / "skills" / skill_id)

    def test_builds_complete_package_for_tuneable_skill(self):
        skill_id = "clipmind-agent-xhs-graphic-note"
        self.copy_skill(skill_id)
        output, errors = self.module.build_package(self.temp_root, skill_id, 2)
        self.assertEqual([], errors)
        self.assertIsNotNone(output)
        for name in ("SKILL.md", "source-map.md", "mergeable-definition.md", "baseline-vs-final.diff", "validation.md"):
            self.assertTrue((output / name).exists(), name)

    def test_refuses_governance_package(self):
        skill_id = "clipmind-governance-ip-consistency-v1"
        self.copy_skill(skill_id)
        output, errors = self.module.build_package(self.temp_root, skill_id, 1)
        self.assertIsNone(output)
        self.assertTrue(any("只读" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
