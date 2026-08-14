# Operator Copy Tuning Fixture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restrict the operator workflow to 32 copy-related Skills, seed a synthetic Zhao Yueyue IP fixture automatically, and prevent any tuned package from changing its baseline or critical contract.

**Architecture:** Keep all 146 exported transport Skills intact, but turn `inventory/tuning-order.json` into the only operator queue. Store the synthetic fixture and per-Skill scenarios under `fixtures/ip/赵玥玥/`, seed it only into an empty ignored `IP素材库/`, and enforce queue membership plus baseline hashes in the existing guard/finalizer.

**Tech Stack:** Python 3 standard library, JSON, Markdown, `unittest`.

---

### Task 1: Lock the 32-Skill operator queue

**Files:**
- Modify: `tests/test_project_check.py`
- Modify: `inventory/tuning-order.json`
- Create: `inventory/optional-copy-skills.json`
- Modify: `.agents/skills/clipmind-skill-tuner/scripts/project_check.py`

- [ ] **Step 1: Write the failing queue test**

Add assertions that `tuning-order.json` contains exactly these original orders:

```python
expected_orders = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    17, 18, 28, 32, 33, 34, 35, 36,
    39, 43, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
}
self.assertEqual(expected_orders, {item["source_order"] for item in queue})
self.assertEqual(32, len(queue))
```

Also assert the optional file contains source orders `{26, 30, 44, 60, 62, 63, 64}`, is disjoint from the default queue, and every queued Skill exists in the full inventory.

- [ ] **Step 2: Run the test and verify RED**

Run: `python3 -m unittest tests.test_project_check -v`

Expected: FAIL because the queue still has 146 entries and the optional file does not exist.

- [ ] **Step 3: Build the minimal queue files**

Filter the existing inventory entries without changing their contracts. Renumber `order` from 1 to 32 and retain the original value as `source_order`. Set top-level counts to `{"tune": 32}`; keep only phases 1-5 that contain selected entries.

Create `optional-copy-skills.json` with the seven untouched inventory records, `enabled_by_default: false`, and a short activation note.

- [ ] **Step 4: Update project consistency checks**

Keep the full export checks at 146 Skills, but change queue validation to:

```python
EXPECTED_OPERATOR_COUNT = 32
EXPECTED_OPTIONAL_COUNT = 7
if len(order) != EXPECTED_OPERATOR_COUNT:
    errors.append(...)
if not set(queue_ids).issubset(inventory_ids):
    errors.append(...)
```

- [ ] **Step 5: Run queue tests and verify GREEN**

Run: `python3 -m unittest tests.test_project_check -v`

Expected: PASS for the queue assertions or continue to the next missing fixture assertion.

### Task 2: Add the versioned synthetic IP fixture and scenarios

**Files:**
- Create: `fixtures/ip/赵玥玥/README.md`
- Create: `fixtures/ip/赵玥玥/MATERIALS.md`
- Create: `fixtures/ip/赵玥玥/PROFILE.md`
- Create: `fixtures/ip/赵玥玥/EVIDENCE-INDEX.md`
- Create: `fixtures/ip/赵玥玥/原始材料/01-人物访谈.md`
- Create: `fixtures/ip/赵玥玥/原始材料/02-业务与产品.md`
- Create: `fixtures/ip/赵玥玥/原始材料/03-用户访谈与评论.md`
- Create: `fixtures/ip/赵玥玥/原始材料/04-案例记录.md`
- Create: `fixtures/ip/赵玥玥/原始材料/05-表达语料.md`
- Create: `fixtures/ip/赵玥玥/原始材料/06-历史内容样本.md`
- Create: `fixtures/ip/赵玥玥/原始材料/07-内容表现数据.md`
- Create: `fixtures/ip/赵玥玥/原始材料/08-阶段目标与选题池.md`
- Create: `fixtures/ip/赵玥玥/scenarios.json`
- Modify: `tests/test_project_check.py`
- Modify: `.agents/skills/clipmind-skill-tuner/scripts/project_check.py`

- [ ] **Step 1: Write failing fixture integrity tests**

Assert that every required fixture file exists, every Markdown fixture starts with a visible `MOCK` declaration, and:

```python
scenarios = json.loads((fixture / "scenarios.json").read_text(encoding="utf-8"))
self.assertEqual(queue_ids, set(scenarios["skills"]))
for scenario in scenarios["skills"].values():
    self.assertTrue(scenario["task"].strip())
    self.assertTrue(scenario["materials"])
    for relative in scenario["materials"]:
        self.assertTrue((fixture / relative).exists(), relative)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python3 -m unittest tests.test_project_check -v`

Expected: FAIL because `fixtures/ip/赵玥玥` does not exist.

- [ ] **Step 3: Add rich, explicitly synthetic fixture materials**

Write a coherent fictional IP profile with no real contact details or real client names. Each Markdown file must begin with:

```markdown
> **MOCK 合成演练数据**：本文件只用于 Skill Forge 调优，不对应真实个人、客户或经营结果，不得用于外部宣传。
```

Use stable evidence IDs across the profile and raw materials. Include contradictions, missing evidence, negative feedback, weak-performing content, and forbidden claims so the Skills can be tested realistically.

- [ ] **Step 4: Map all 32 Skills to fixed tasks**

`scenarios.json` must have:

```json
{
  "fixture_id": "zhao-yueyue",
  "skills": {
    "clipmind-sop-ip-s01-profile-extract": {
      "task": "基于全部建档资料提炼赵玥玥的 8 个档案维度候选。",
      "materials": ["PROFILE.md", "EVIDENCE-INDEX.md", "原始材料/01-人物访谈.md"]
    }
  }
}
```

Add one complete mapping per queue Skill.

- [ ] **Step 5: Run fixture integrity tests and verify GREEN**

Run: `python3 -m unittest tests.test_project_check -v`

Expected: PASS for fixture and scenario assertions.

### Task 3: Seed the fixture without overwriting user material

**Files:**
- Modify: `tests/test_progress.py`
- Modify: `.agents/skills/clipmind-skill-tuner/scripts/progress.py`

- [ ] **Step 1: Write failing seeding tests**

Add tests for:

```python
seeded = progress.seed_builtin_fixture(project_root)
self.assertTrue(seeded)
self.assertEqual(fixture_profile, runtime_profile)
```

Then create a user file in `IP素材库/原始材料/`, call the function again, and assert it returns `False`, preserves the user file, and does not copy fixture profile files.

Add a state test showing built-in seeding produces:

```python
self.assertEqual("ready", state["ip_profile_status"])
self.assertEqual("builtin_fixture", state["profile_mode"])
self.assertEqual("zhao-yueyue", state["active_ip_fixture"])
```

- [ ] **Step 2: Run progress tests and verify RED**

Run: `python3 -m unittest tests.test_progress -v`

Expected: FAIL because `seed_builtin_fixture` does not exist.

- [ ] **Step 3: Implement minimal safe seeding**

Add `seed_builtin_fixture(root: Path) -> bool` using `shutil.copy2`. Treat any non-`.gitkeep` raw material or existing `PROFILE.md`, `MATERIALS.md`, or `EVIDENCE-INDEX.md` as user-owned and return without copying.

Extend `load_or_initialize(..., project_root=None)` so the CLI passes the project root, records fixture state when seeding succeeds, and reconciles state to the current 32-Skill queue.

- [ ] **Step 4: Run progress tests and verify GREEN**

Run: `python3 -m unittest tests.test_progress -v`

Expected: all progress tests PASS.

### Task 4: Add queue and immutable-baseline gates

**Files:**
- Modify: `tests/test_skill_guard.py`
- Create: `inventory/baseline-locks.json`
- Modify: `.agents/skills/clipmind-skill-tuner/scripts/skill_guard.py`

- [ ] **Step 1: Write failing guard tests**

Add tests proving:

- a queued untouched Skill passes with `enforce_operator_scope=True`;
- a governance, visual, or non-queued content Skill is blocked;
- changing `references/original.md` is blocked even when `SKILL.md` is changed to the same text;
- changing visual-method lines in `xhs-graphic-note` is blocked;
- changing an allowed copy-processing line still passes.

The desired API is:

```python
result = guard.validate_skill_dir(
    skill_dir,
    project_root=ROOT,
    enforce_operator_scope=True,
)
```

- [ ] **Step 2: Run guard tests and verify RED**

Run: `python3 -m unittest tests.test_skill_guard -v`

Expected: FAIL because the new parameters and baseline manifest do not exist.

- [ ] **Step 3: Add baseline lock manifest**

Create:

```json
{
  "algorithm": "sha256",
  "skills": {
    "clipmind-sop-ip-s01-profile-extract": "<sha256 of references/original.md>"
  }
}
```

with exactly the 32 queue IDs.

- [ ] **Step 4: Implement queue, hash, and copy-only checks**

Extend `validate_skill_dir` with optional project-root enforcement. When enforcement is on:

1. load queue IDs and reject non-members;
2. load the expected baseline hash and compare it with the actual original;
3. run existing contract validation;
4. for `clipmind-agent-xhs-graphic-note`, compare all original/candidate definition lines containing visual markers such as 画面、图片、截图、版式、配图、构图、颜色、字体、留白、视觉.

The CLI and finalizer must turn enforcement on. Project-wide integrity checks may still validate excluded transport packages structurally with enforcement off.

- [ ] **Step 5: Run guard tests and verify GREEN**

Run: `python3 -m unittest tests.test_skill_guard -v`

Expected: all guard tests PASS.

### Task 5: Refuse final packages outside the operator queue

**Files:**
- Modify: `tests/test_finalize.py`
- Modify: `.agents/skills/clipmind-skill-tuner/scripts/finalize.py`

- [ ] **Step 1: Write failing finalizer tests**

Assert a queued Skill packages successfully and a non-queued ordinary content Skill, governance Skill, and baseline-tampered Skill all return `None` with a boundary error.

- [ ] **Step 2: Run finalizer tests and verify RED**

Run: `python3 -m unittest tests.test_finalize -v`

Expected: FAIL because ordinary non-queued content still packages.

- [ ] **Step 3: Enforce the guard in `build_package`**

Change the guard call to:

```python
result = validate_skill_dir(
    skill_dir,
    project_root=root,
    enforce_operator_scope=True,
)
```

Include the verified baseline hash in `validation.md`.

- [ ] **Step 4: Run finalizer tests and verify GREEN**

Run: `python3 -m unittest tests.test_finalize -v`

Expected: all finalizer tests PASS.

### Task 6: Update the operator workflow and documentation

**Files:**
- Modify: `.agents/skills/clipmind-skill-tuner/SKILL.md`
- Modify: `README.md`
- Modify: `开始调试.md`
- Modify: `调试顺序.md`
- Modify: `IP素材库/README.md`
- Modify: `Skill不可修改边界.md`
- Modify: `AGENTS.md`
- Modify: `操盘手调试话术.md`

- [ ] **Step 1: Update the tuner workflow**

Remove visual, component, and governance modes from the operator flow. Require automatic fixture selection, scenario loading, workbench-style generation, fixed-input reuse, feedback classification, guard-first rerun, and explicit `OK` before finalization.

- [ ] **Step 2: Update human-facing docs**

Replace all 146-Skill and manual-import instructions with:

- 32 default copy Skills;
- built-in synthetic Zhao Yueyue fixture;
- no operator action on visual/governance/shared components;
- exactly two feedback choices;
- optional real-material replacement only as an advanced path that never overwrites data.

- [ ] **Step 3: Run stale-copy scans**

Run:

```bash
rg -n '146 个|22 个生图|27 个治理|共享质量组件|把一个 IP.*放进|review_only|visual_tune|component_tune' README.md 开始调试.md 调试顺序.md IP素材库/README.md 操盘手调试话术.md .agents/skills/clipmind-skill-tuner/SKILL.md
```

Expected: no stale operator instructions; historical or explicit exclusion wording is allowed only when it clearly says the operator does not handle those items.

### Task 7: Full verification and branch handoff

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run the complete test suite**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests PASS with zero failures.

- [ ] **Step 2: Run project distribution check**

Run: `python3 .agents/skills/clipmind-skill-tuner/scripts/project_check.py`

Expected: PASS for 146 transport packages, 32 operator Skills, fixture integrity, scenarios, and baseline locks.

- [ ] **Step 3: Run syntax and diff checks**

Run:

```bash
python3 -m compileall -q .agents/skills/clipmind-skill-tuner/scripts tests
git diff --check
git status --short
```

Expected: Python compile exits 0, diff check is empty, and status contains only scoped intended changes.

- [ ] **Step 4: Review scope and commit**

Inspect `git diff --stat`, `git diff --name-only`, and the staged list. Commit only the intended queue, fixture, scripts, tests, and documentation.
