import importlib.util
import inspect
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/clipmind-skill-tuner/scripts/skill_guard.py"


def load_guard_module():
    spec = importlib.util.spec_from_file_location("skill_guard", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SkillGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guard = load_guard_module()

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="skill-guard-test-"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def copy_skill(self, skill_id: str) -> Path:
        source = ROOT / "skills" / skill_id
        target = self.temp_dir / skill_id
        shutil.copytree(source, target)
        return target

    def validate(self, skill_dir: Path):
        return self.guard.validate_skill_dir(skill_dir)

    def validate_operator(self, skill_dir: Path):
        parameters = inspect.signature(self.guard.validate_skill_dir).parameters
        self.assertIn("project_root", parameters)
        self.assertIn("enforce_operator_scope", parameters)
        return self.guard.validate_skill_dir(
            skill_dir,
            project_root=ROOT,
            enforce_operator_scope=True,
        )

    def test_queued_skill_passes_operator_scope(self):
        skill = self.copy_skill("clipmind-agent-xhs-graphic-note")
        result = self.validate_operator(skill)
        self.assertTrue(result.ok, result.errors)

    def test_nonqueued_content_skill_is_blocked_for_operator(self):
        skill = self.copy_skill("clipmind-agent-fact-check")
        result = self.validate_operator(skill)
        self.assertFalse(result.ok)
        self.assertTrue(any("默认文案调试队列" in error for error in result.errors), result.errors)

    def test_baseline_tampering_is_blocked_even_when_candidate_matches(self):
        skill = self.copy_skill("clipmind-agent-xhs-graphic-note")
        original_path = skill / "references/original.md"
        candidate_path = skill / "SKILL.md"
        original = original_path.read_text(encoding="utf-8")
        changed = original.replace(
            "1. 先判断主题是否适合图文笔记,并标出素材缺口。",
            "1. 先判断主题和用户阶段是否适合图文笔记,并标出素材缺口。",
            1,
        )
        original_path.write_text(changed, encoding="utf-8")
        candidate_path.write_text(changed, encoding="utf-8")

        result = self.validate_operator(skill)

        self.assertFalse(result.ok)
        self.assertTrue(any("原始基线" in error for error in result.errors), result.errors)

    def test_mixed_graphic_skill_cannot_change_visual_method(self):
        skill = self.copy_skill("clipmind-agent-xhs-graphic-note")
        path = skill / "SKILL.md"
        text = path.read_text(encoding="utf-8").replace(
            "每页给出画面建议、主文案和补充说明",
            "每页给出高饱和画面建议、主文案和补充说明",
            1,
        )
        path.write_text(text, encoding="utf-8")

        result = self.validate_operator(skill)

        self.assertFalse(result.ok)
        self.assertTrue(any("视觉" in error for error in result.errors), result.errors)

    def test_mixed_graphic_skill_can_change_copy_method(self):
        skill = self.copy_skill("clipmind-agent-xhs-graphic-note")
        path = skill / "SKILL.md"
        text = path.read_text(encoding="utf-8").replace(
            "2. 提炼 3 个封面标题方向,分别覆盖痛点、结果和反常识角度。",
            "2. 先绑定用户原话,再提炼 3 个封面标题方向,分别覆盖痛点、结果和反常识角度。",
            1,
        )
        path.write_text(text, encoding="utf-8")

        result = self.validate_operator(skill)

        self.assertTrue(result.ok, result.errors)

    def test_untouched_agent_passes(self):
        skill = self.copy_skill("clipmind-agent-xhs-graphic-note")
        result = self.validate(skill)
        self.assertTrue(result.ok, result.errors)

    def test_agent_processing_method_can_change(self):
        skill = self.copy_skill("clipmind-agent-xhs-graphic-note")
        path = skill / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "1. 先判断主题是否适合图文笔记,并标出素材缺口。",
            "1. 先用目标用户、使用场景和现有素材判断主题是否适合图文笔记,并标出素材缺口。",
            1,
        )
        path.write_text(text, encoding="utf-8")
        result = self.validate(skill)
        self.assertTrue(result.ok, result.errors)

    def test_agent_input_contract_cannot_change(self):
        skill = self.copy_skill("clipmind-agent-xhs-graphic-note")
        path = skill / "SKILL.md"
        text = path.read_text(encoding="utf-8").replace('"task_brief",', '"new_field",', 1)
        path.write_text(text, encoding="utf-8")
        result = self.validate(skill)
        self.assertFalse(result.ok)
        self.assertTrue(any("输入契约" in error for error in result.errors), result.errors)

    def test_agent_cannot_add_external_action_to_method(self):
        skill = self.copy_skill("clipmind-agent-xhs-graphic-note")
        path = skill / "SKILL.md"
        text = path.read_text(encoding="utf-8").replace(
            "4. 整理正文 caption、话题标签、素材清单和人工确认点。",
            "4. 整理正文 caption、话题标签、素材清单和人工确认点。\n5. 自动发布到小红书并保存发布状态。",
            1,
        )
        path.write_text(text, encoding="utf-8")
        result = self.validate(skill)
        self.assertFalse(result.ok)
        self.assertTrue(any("越过人工业务边界" in error for error in result.errors), result.errors)

    def test_wrapper_cannot_change(self):
        skill = self.copy_skill("clipmind-agent-xhs-graphic-note")
        path = skill / "SKILL.md"
        text = path.read_text(encoding="utf-8").replace("## 用途", "## 新用途", 1)
        path.write_text(text, encoding="utf-8")
        result = self.validate(skill)
        self.assertFalse(result.ok)
        self.assertTrue(any("平台定义之外" in error for error in result.errors), result.errors)

    def test_sop_prose_can_change_but_metadata_cannot(self):
        skill = self.copy_skill("clipmind-sop-ip-s03-strategy-suggestion")
        path = skill / "SKILL.md"
        original = path.read_text(encoding="utf-8")
        changed = original.replace(
            "策略主线、差异化打法和方法引用都要来自档案、诊断或输入方法;缺证据写入 evidence_gaps。",
            "策略主线、差异化打法和方法引用先逐项绑定档案、诊断或输入方法;缺证据写入 evidence_gaps。",
            1,
        )
        path.write_text(changed, encoding="utf-8")
        self.assertTrue(self.validate(skill).ok)

        path.write_text(original.replace("module_key: strategy", "module_key: production", 1), encoding="utf-8")
        result = self.validate(skill)
        self.assertFalse(result.ok)
        self.assertTrue(any("元数据" in error for error in result.errors), result.errors)

    def test_sop_role_and_task_cannot_change(self):
        skill = self.copy_skill("clipmind-sop-ip-s03-strategy-suggestion")
        path = skill / "SKILL.md"
        text = path.read_text(encoding="utf-8").replace(
            "你是自媒体工作台里的策略确认 Agent。",
            "你是自媒体工作台里的自动发布 Agent。",
            1,
        )
        path.write_text(text, encoding="utf-8")
        result = self.validate(skill)
        self.assertFalse(result.ok)
        self.assertTrue(any("角色和原始任务" in error for error in result.errors), result.errors)

    def test_governance_skill_is_read_only(self):
        skill = self.copy_skill("clipmind-governance-ip-consistency-v1")
        path = skill / "SKILL.md"
        text = path.read_text(encoding="utf-8").replace("IP 一致性判断", "IP 一致性严格判断", 1)
        path.write_text(text, encoding="utf-8")
        result = self.validate(skill)
        self.assertFalse(result.ok)
        self.assertTrue(any("只读" in error for error in result.errors), result.errors)

    def test_image_prompt_can_change_but_size_cannot(self):
        skill = self.copy_skill("clipmind-image-cover-xhs")
        path = skill / "SKILL.md"
        original = path.read_text(encoding="utf-8")
        changed = original.replace("高级配色,留白考究", "低饱和高级配色,主体四周保留安全留白", 1)
        path.write_text(changed, encoding="utf-8")
        self.assertTrue(self.validate(skill).ok)

        path.write_text(original.replace("1024x1536", "1536x1024", 1), encoding="utf-8")
        result = self.validate(skill)
        self.assertFalse(result.ok)
        self.assertTrue(any("生图 Prompt" in error for error in result.errors), result.errors)


if __name__ == "__main__":
    unittest.main()
