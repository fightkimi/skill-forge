---
name: clipmind-skill-tuner
description: 引导非技术 IP 操盘手在同一个 IP 素材库上，按 ClipMind 业务顺序一次一个地试跑、反馈、最小修改、同材料复跑并收口 Skill。用户说“开始调试”“开始下一个 Skill”“不OK”或“OK，完成这个 Skill”时使用。
---

# ClipMind Skill 调试引导

把项目根目录视为工作区。始终使用根目录 `AGENTS.md`、`Skill不可修改边界.md` 和本 Skill；不要要求用户安装全部业务 Skill。业务 Skill 中出现的旧案例路径 `ip-cases/<案例编号>/` 在本项目内统一映射为根目录 `IP素材库/`。

## 1. 初始化

1. 运行 `scripts/progress.py init`。已有进度时保留，不得重置。
2. 检查 `IP素材库/原始材料/` 是否有真实材料。
3. 若尚未建档，读取全部可读材料并建立：
   - `IP素材库/MATERIALS.md`
   - `IP素材库/PROFILE.md`
   - `IP素材库/EVIDENCE-INDEX.md`
   - `IP素材库/操盘手补充确认.md`
4. 分开记录材料明示事实、操盘手口头确认、Codex 推断和仍待确认。原始材料只读。
5. 让操盘手确认档案。确认后运行 `scripts/progress.py profile-ready`，再开始业务 Skill。

材料为空或关键文件不可读时，只列出最少补充动作；不要凭印象开始生成。

## 2. 取得当前唯一 Skill

1. 运行 `scripts/progress.py next`。
2. 若返回已有进行中 Skill，继续它，不切换。
3. 若返回新 Skill，运行 `scripts/progress.py start <技术ID>`。
4. 完整读取当前目录的：
   - `SKILL.md`
   - `agents/openai.yaml`
   - `references/original.md`
   - `references/source-map.md`
   - `references/platform-context.md`
   - `evals/cases.md`
5. 不读取另一个业务 Skill 的正文。共享组件的宿主回归是例外，但只能把宿主当测试输入，不能修改宿主 Skill。

首次展示只用一张短表：中文名、技术 ID、业务阶段、调试模式、实际读取材料、缺失材料和本轮目标。不要把内部 Prompt 工程术语堆给操盘手。

## 3. 固定可比较输入

根据当前 Skill 的真实输入契约和 `evals/cases.md`，从当前 IP 素材中选择一项可判断质量的真实任务。把任务、材料文件、限制条件和初始目标保存到 `tuning-records/<技术ID>/fixed-input.md`。

后续每轮必须复用同一任务和材料。操盘手补充的新事实单独追加并明确标注，不能悄悄换题来制造改善。

## 4. 首轮生成

严格按当前 `SKILL.md` 中的候选定义生成，不为迎合预期绕过 Skill。关键材料缺失时，完成不受影响的安全部分并列证据缺口；无法安全继续时停止主体生成。

输出后记录完整结果，并用简短语言标明证据缺口、风险和人工确认点。最后固定给出：

1. `OK，完成这个 Skill`
2. `不OK：请直接写修改意见`

收到反馈前不修改 Skill。

## 5. 处理“不OK”反馈

把反馈原文写入当前调试记录，然后按以下顺序处理：

1. 列出操盘手要求保留的部分。
2. 将问题归为：删除、加强、修正、格式、边界、当前 IP 个案、待确认。
3. 判断落点：
   - 当前 IP 的事实、产品、案例、数字、口头禅：只改本轮输入或档案，不写进通用 Skill。
   - 跨案例可复用的方法：允许进入当前候选 Skill。
   - 身份、路由、字段、工具、权限、Schema、人工边界或护栏：拒绝修改，说明它属于产品契约；如可行，用契约内的方法改进替代。
4. 只修改当前 Skill 中与反馈直接相关的既有板块。不增删大体结构，不顺手优化其他区域。
5. 用修改前、修改后、反馈证据、预期改善四项记录本轮改动；不要输出隐藏思维链。

用户的“不OK”已构成当前允许区域的修改授权，无需再次让用户确认修改方向。

## 6. 强制校验和复跑

修改后先运行：

```text
python3 .agents/skills/clipmind-skill-tuner/scripts/skill_guard.py skills/<技术ID>
```

校验失败时，撤回或修正本轮越界改动，直至通过；不得靠改验证器、原始基线或测试来过关。

通过后：

1. 使用 `fixed-input.md` 的同一任务和材料复跑。
2. 追加检查材料缺失、越界请求和输出契约三个场景。
3. 说明已改善、未改善、新问题和是否损伤已确认部分。
4. 保存完整输出和本轮摘要。
5. 再给固定二选一。

## 7. 按类型执行差异

- `tune`：按上述内容循环执行。
- `visual_tune`：有生图能力时必须用同一主题和素材生成候选图；没有时只交付 Prompt、尺寸和检查点，并明确未生成。只可修改“原始生图 Prompt”正文。
- `component_tune`：共享组件需选择 3 个不同宿主任务做回归，三项都没有合同回归才可让操盘手确认完成。
- `review_only`：治理 Skill 只评审候选内容。不得改 `SKILL.md`；不满意反馈写成 `merge-packages/<技术ID>/ENGINEERING-PROPOSAL.md`，包含误判/漏判、证据、影响模块和期望行为。

## 8. 操盘手确认 OK 后

1. 再次运行 `skill_guard.py`。
2. 对可调 Skill 运行 `scripts/finalize.py <技术ID> --rounds <轮数>`。
3. 对治理 Skill 输出工程变更建议单或只读验收结论，保持原定义不变。
4. 运行 `scripts/progress.py complete <技术ID> --rounds <轮数>`。
5. 交付最终文件的可点击路径，说明该 `SKILL.md` 是回收包，不会自动上线。
6. 提醒操盘手新开一个 Codex 对话并发送“开始调试下一个 Skill”。

只有操盘手明确说 OK 才能完成当前 Skill。不得自行宣布满意或自动进入下一项。
