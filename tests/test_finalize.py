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
        (self.temp_root / "inventory").mkdir()
        for name in ("tuning-order.json", "baseline-locks.json"):
            shutil.copy2(
                ROOT / "inventory" / name,
                self.temp_root / "inventory" / name,
            )

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

    def test_refuses_nonqueued_content_package(self):
        skill_id = "clipmind-agent-fact-check"
        self.copy_skill(skill_id)

        output, errors = self.module.build_package(self.temp_root, skill_id, 1)

        self.assertIsNone(output)
        self.assertTrue(any("默认文案调试队列" in error for error in errors), errors)

    def test_refuses_package_when_original_baseline_is_tampered(self):
        skill_id = "clipmind-agent-xhs-graphic-note"
        self.copy_skill(skill_id)
        skill_dir = self.temp_root / "skills" / skill_id
        original_path = skill_dir / "references/original.md"
        candidate_path = skill_dir / "SKILL.md"
        changed = original_path.read_text(encoding="utf-8").replace(
            "1. 先判断主题是否适合图文笔记,并标出素材缺口。",
            "1. 先判断主题和用户阶段是否适合图文笔记,并标出素材缺口。",
            1,
        )
        original_path.write_text(changed, encoding="utf-8")
        candidate_path.write_text(changed, encoding="utf-8")

        output, errors = self.module.build_package(self.temp_root, skill_id, 1)

        self.assertIsNone(output)
        self.assertTrue(any("原始基线" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
