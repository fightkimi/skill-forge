import importlib.util
import hashlib
import inspect
import json
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/clipmind-skill-tuner/scripts/progress.py"
FIXTURE = ROOT / "fixtures/ip/小月"


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
            {
                "order": 1,
                "phase": 1,
                "phase_name": "建档",
                "skill_id": "skill-a",
                "mode": "tune",
                "name": "A",
                "purpose": "先生成档案候选",
                "depends_on": [],
                "consumes_outputs_from": [],
                "selection_reason": "这是工作流起点。",
                "output_label": "档案候选",
            },
            {
                "order": 2,
                "phase": 2,
                "phase_name": "策略",
                "skill_id": "skill-b",
                "mode": "review",
                "name": "B",
                "purpose": "承接档案生成策略",
                "depends_on": ["skill-a"],
                "consumes_outputs_from": ["skill-a"],
                "selection_reason": "档案确认后才能进入策略。",
                "output_label": "策略建议",
            },
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_project_root(self) -> Path:
        project_root = Path(self.temp_dir.name) / "project"
        shutil.copytree(
            FIXTURE,
            project_root / "fixtures/ip/小月",
        )
        (project_root / "IP素材库/原始材料").mkdir(parents=True)
        return project_root

    def test_seeds_builtin_fixture_into_empty_material_library(self):
        project_root = self.make_project_root()
        self.assertTrue(hasattr(self.progress, "seed_builtin_fixture"))

        seeded = self.progress.seed_builtin_fixture(project_root)

        self.assertTrue(seeded)
        for relative in ("PROFILE.md", "MATERIALS.md", "EVIDENCE-INDEX.md"):
            expected = (project_root / "fixtures/ip/小月" / relative).read_text(
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
        self.assertEqual("xiaoyue", state["active_ip_fixture"])

    def test_migrates_recognized_legacy_builtin_fixture(self):
        project_root = self.make_project_root()
        library = project_root / "IP素材库"
        (library / "PROFILE.md").write_text(
            "# 赵玥玥 IP 档案\n\n> **MOCK 合成演练数据**：旧内置资料。",
            encoding="utf-8",
        )
        (library / "MATERIALS.md").write_text("旧内置资料", encoding="utf-8")
        (library / "EVIDENCE-INDEX.md").write_text("旧内置资料", encoding="utf-8")
        legacy_hashes = {
            relative: hashlib.sha256((library / relative).read_bytes()).hexdigest()
            for relative in ("PROFILE.md", "MATERIALS.md", "EVIDENCE-INDEX.md")
        }
        self.state_path.write_text(
            json.dumps(
                {
                    "version": 2,
                    "ip_profile_status": "ready",
                    "profile_mode": "builtin_fixture",
                    "active_ip_fixture": "zhao-yueyue",
                    "active_skill": None,
                    "skills": {},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        with mock.patch.object(
            self.progress,
            "LEGACY_FIXTURE_SHA256",
            legacy_hashes,
        ):
            state = self.progress.load_or_initialize(
                self.state_path,
                self.order,
                project_root=project_root,
            )

        self.assertEqual("xiaoyue", state["active_ip_fixture"])
        profile = (library / "PROFILE.md").read_text(encoding="utf-8")
        self.assertIn("# 小月 IP 档案", profile)
        self.assertNotIn("赵玥玥", profile)
        self.assertTrue((library / "原始材料/08-阶段目标与选题池.md").exists())

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

        self.progress.mark_started(state, self.order, "skill-a")
        self.progress.save_state(self.state_path, state)
        reloaded = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual("in_progress", reloaded["skills"]["skill-a"]["status"])

        self.progress.mark_completed(reloaded, "skill-a", 3)
        self.assertEqual("skill-b", self.progress.next_item(reloaded, self.order)["skill_id"])
        self.assertEqual(3, reloaded["skills"]["skill-a"]["rounds"])

    def test_cannot_start_two_skills_at_once(self):
        state = self.progress.load_or_initialize(self.state_path, self.order)
        self.progress.mark_started(state, self.order, "skill-a")
        with self.assertRaises(ValueError):
            self.progress.mark_started(state, self.order, "skill-b")

    def test_cannot_complete_skill_that_is_not_active(self):
        state = self.progress.load_or_initialize(self.state_path, self.order)

        with self.assertRaisesRegex(ValueError, "当前正在调试"):
            self.progress.mark_completed(state, "skill-a", 1)

    def test_completion_requires_confirmed_current_output(self):
        state = self.progress.load_or_initialize(self.state_path, self.order)
        self.progress.mark_started(state, self.order, "skill-a")

        with self.assertRaisesRegex(ValueError, "已确认输出"):
            self.progress.mark_completed(
                state,
                "skill-a",
                1,
                records_root=Path(self.temp_dir.name) / "tuning-records",
            )

    def test_cannot_start_skill_before_dependencies_are_completed(self):
        state = self.progress.load_or_initialize(self.state_path, self.order)

        with self.assertRaisesRegex(ValueError, "A"):
            self.progress.mark_started(state, self.order, "skill-b")

    def test_current_card_explains_identity_reason_and_upstream(self):
        state = self.progress.load_or_initialize(self.state_path, self.order)
        self.progress.mark_started(state, self.order, "skill-a")
        self.progress.mark_completed(state, "skill-a", 2)
        self.progress.mark_started(state, self.order, "skill-b")

        card = self.progress.current_card(state, self.order)

        self.assertEqual("第 2/2 个 · B", card["display_title"])
        self.assertEqual("档案确认后才能进入策略。", card["selection_reason"])
        self.assertEqual("策略建议", card["output_label"])
        self.assertEqual("A", card["dependencies"][0]["name"])
        self.assertEqual("completed", card["dependencies"][0]["status"])
        self.assertEqual(
            "tuning-records/skill-a/round-02-output.md",
            card["upstream_outputs"][0]["path"],
        )

    def test_start_blocks_when_required_upstream_output_is_missing(self):
        state = self.progress.load_or_initialize(self.state_path, self.order)
        self.progress.mark_started(state, self.order, "skill-a")
        self.progress.mark_completed(state, "skill-a", 1)
        records_root = Path(self.temp_dir.name) / "tuning-records"

        with self.assertRaisesRegex(ValueError, "已确认输出"):
            self.progress.mark_started(
                state,
                self.order,
                "skill-b",
                records_root=records_root,
            )

    def test_start_accepts_verified_upstream_output(self):
        state = self.progress.load_or_initialize(self.state_path, self.order)
        self.progress.mark_started(state, self.order, "skill-a")
        self.progress.mark_completed(state, "skill-a", 1)
        records_root = Path(self.temp_dir.name) / "tuning-records"
        upstream = records_root / "skill-a"
        upstream.mkdir(parents=True)
        (upstream / "acceptance.json").write_text(
            json.dumps(
                {
                    "skill_id": "skill-a",
                    "operator_confirmed": True,
                    "rounds": 1,
                }
            ),
            encoding="utf-8",
        )
        (upstream / "round-01-output.md").write_text("已确认档案", encoding="utf-8")

        self.progress.mark_started(
            state,
            self.order,
            "skill-b",
            records_root=records_root,
        )

        self.assertEqual("skill-b", state["active_skill"])


if __name__ == "__main__":
    unittest.main()
