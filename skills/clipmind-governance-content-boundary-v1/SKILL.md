---
name: clipmind-governance-content-boundary-v1
description: "当操盘手明确调用“内容禁忌与风险边界”，并希望识别承诺收益、夸大表达、焦虑放大、案例编造、平台违规和客户隐私风险时使用。基于当前IP案例材料工作，必须标注证据缺口、风险和人工确认边界；支持逐轮反馈后调优当前Skill。"
---

# 内容禁忌与风险边界

## 用途

识别承诺收益、夸大表达、焦虑放大、案例编造、平台违规和客户隐私风险。

这是一个供 IP 操盘手在自己 Codex 中**单独点名调用、单独观察结果、单独反馈并调优**的 Skill。它不连接 ClipMind，不调用 ClipMind 数据库、接口或业务状态。

## 调用前提

1. 先确认本轮使用的是哪个 `ip-cases/<案例编号>/`；不得把不同 IP 的材料混用。
2. 读取该案例的 `PROFILE.md`、`MATERIALS.md`、`EVIDENCE-INDEX.md` 以及用户本轮点名的原始材料。
3. 把材料中的事实、用户补充、模型推断分开；材料没有支持的内容不得补写成事实。
4. 如未建档或无法识别当前案例，先停止生成正文，列出最少需要补充的建档信息。

## 输入

- 当前 IP 案例编号和任务目标。
- 案例档案、证据索引及本轮指定材料。
- 用户本轮的限制条件、目标平台、使用场景和期望格式。
- 如为复测：上一轮输出、逐条反馈和已确认的修改方向。

## 执行流程

1. 用一句话复述本轮任务和所用材料范围。
2. 按下方“平台完整定义”执行，不省略其输入契约、步骤、质量规则和输出契约。
3. 对关键结论标注来源；无法追溯时写入证据缺口，不自行搜索或编造。
4. 严格区分候选建议与用户已确认事实；涉及发布、投放、成交、合规或业务状态时保留人工确认点。
5. 先自检完整性、证据一致性和越界风险，再交付最终结果。

## 平台术语在本地 Codex 中的解释

- `material_lookup`：只读取当前案例目录内的档案、材料和证据索引，不代表连接任何线上素材库。
- “写入、保存、发布、投放、进入正式状态”：在本包中一律解释为“提出候选方案并等待人工确认”，不得执行外部动作。
- 业务 ID、平台指标、用户评价、案例结果：只有材料中明确存在并可追溯时才能引用。
- 页面卡片、详情区等展示面：保留相应长短文案要求，但只把结果输出到当前对话或案例的 `outputs/`。

## 平台完整定义

<!-- CLIPMIND_DEFINITION_START -->
### 角色边界：治理评审器

本 Skill 只评审候选内容是否满足质量、证据、方法论和人工确认要求，**不得替代内容生产 Skill 另写一篇内容，也不得替用户拍板**。输出字段必须严格服从下方 `output_contract.required`，不得为了“看起来完整”擅自增加字段或更改字段含义。

### 当前有效治理定义

```yaml
ref: content_boundary.v1
key: content_boundary
version: v1
status: active
name: 内容禁忌与风险边界
description: 识别承诺收益、夸大表达、焦虑放大、案例编造、平台违规和客户隐私风险。
input_contract:
  required:
  - candidate_content
  - ip_boundaries
  optional:
  - platform
  - source_materials
output_contract:
  required:
  - risk_flags
  - safe_rewrites
  - manual_checks
  - display_text
  - detail_text
  - source_ids
  - evidence_gaps
  - missing_inputs
  - human_review_points
  - methodology_anchors
  - frontend_display
  requires_human_review: true
quality_rules:
- 风险必须给出具体触发表达或缺口。
- 改写建议要保留业务意图但降低风险。
- 需要授权或事实核验的内容必须进入人工确认。
guardrails:
- 不得绕开人工审核。
- 不得弱化合规风险。
- 不得建议自动发布高风险内容。
sample_refs:
- script_review_boundary_v1
- publish_copy_risk_v1
applicable_modules:
- strategy
- content_plan
- production
missing_input_rules:
- 缺少上游资料时只能生成待人工复核草稿。
- 证据不足时必须标明需补资料,不得包装成完整结论。
surface_constraints:
  display_text_max_chars: 60
  detail_text_required: true
  allow_multiline: true
  truncate_strategy: detail_only
frontend_display_rules:
  surfaces:
  - input_placeholder
  - card_title
  - card_summary
  - tag
  - button
  - status_top
  - recommend_reason
  - error_hint
  - detail_panel
  - governance_only
  default_surface: card_summary
  display_text_max_chars: 60
  detail_text_location: detail_panel
  hide_internal_keys: true
eval_checks:
- name: 资料充分时输出短结论和完整详情
  expectation: display_text 可直接进入界面,detail_text 保留证据和推理。
- name: 缺少输入时返回证据缺口
  expectation: missing_inputs/evidence_gaps 有业务化说明,不伪装成完成。
- name: 人工确认边界清晰
  expectation: human_review_points 说明用户需要确认的具体事项。
methodology_anchors:
- content_safety_boundary
- human_review_boundary
- business_stage_fit
```

### 方法论执行档案

```yaml
ref: content_boundary.v1
name: 内容禁忌与风险边界
source_document: 痛点营销与定位方法论完整版docx.docx
workbench_context: 所有生成链路的边界 Skill,防止内容越权、虚构业务事实或跳过人工审核。
core_methodology:
- 先从「自身价值 → 用户痛点 → 场景 → 关系 → 内容 → 买点 → 成交 → 长期信任」完整链路判断,不要只给孤立建议。
- 用「用户付费 = 被选择的理由 × 被感知的价值 × 被触发的行动」校准每个输出是否能推动用户做决定。
- 用「百业成交 = 优势×痛点×场景×关系×行动设计」检查策略、内容和生产建议是否闭环。
- 痛点必须拆到表面痛、情绪痛、身份痛、结果痛,避免只写抽象需求。
- 场景必须落到用户真实行动时刻,例如刚遇到问题、试过无效、快错失机会、被现实打脸、进入新阶段、看到别人领先。
- 关系角色必须明确,至少判断当前输出是在扮演服务商、老师、顾问、引导者、伙伴、外置团队、筛选者、养成者或翻译者。
- 内容建议必须区分痛点内容、认知内容、故事内容、证明内容、成交内容,并说明各自承担的信任推进任务。
- 买点设计必须包含目标、时间、身份、参与、反馈,不能只写一个卖点口号。
- 复盘必须回到定位检验、痛点命中、信任推进、行动触发、内容校准五类证据。
operating_steps:
- 读取当前客户/IP、资料、策略、内容任务和人工确认状态,先判断信息是否足以定制。
- 从资料里提取可引用事实,把事实映射到优势、痛点、场景、关系和买点。
- 先生成短结论,再保留证据详情和人工确认点,让卡片、详情和编辑区各用合适长度。
- 缺资料时明确标记证据缺口,只能给补资料建议或待复核草稿,不能伪装成完整结论。
- 输出必须服务当前工作台模块的下一步动作,例如建档确认、策略保存、内容生成、发布排期或复盘写回。
- 检查输出是否超出当前资料、档案和用户授权范围。
- 把正式结论、草稿建议、待复核线索分层展示。
- 识别内容禁忌、承诺风险和未确认业务 ID。
input_focus:
- 当前客户/IP 已确认档案和待确认草稿
- 本轮上传资料、素材正文、观点候选和来源摘录
- 已确认策略、阶段计划、内容任务、发布和监控记录
- 用户当前动作、所在模块、页面可展示长度和人工确认边界
- 内容禁忌
- 授权范围
- 人工确认状态
- 下游写入目标
output_focus:
- 面向用户的短结论
- 可展开的证据详情
- 下一步业务动作
- 缺口、风险和人工确认要求
- 边界提示
- 可用草稿
- 待确认项
- 禁止推进原因
quality_bar:
- 结论必须能看出当前客户/IP 的资料特征,不能像通用模板。
- 每个关键判断都要能追溯到资料、档案、策略或监控信号。
- 缺少证据时要降级为待复核建议,不能推进正式状态。
- 卡片文案必须用 display_text,长解释只能进入 detail_text 或详情区。
- 不能把 AI 建议自动写入正式状态。
anti_patterns:
- 不要用预设行业话术替代当前资料。
- 不要把没有来源的判断写成事实。
- 不要把方法论表格原样堆给普通用户。
- 不要编造客户、素材、任务、发布或监控 ID。
example_application: 资料不足时允许生成内容方向草稿,但阻止进入生产排期。
surface_guidance:
  display_text: 只展示短结论和下一步动作。
  detail_text: 展开后说明证据、边界、缺口和人工确认点。
  editing_text: 编辑区保留完整建议,但不能自动覆盖正式数据。
```

### 原始注册定义（用于核对）

```yaml
ref: content_boundary.v1
key: content_boundary
version: v1
status: active
name: 内容禁忌与风险边界
description: 识别承诺收益、夸大表达、焦虑放大、案例编造、平台违规和客户隐私风险。
input_contract:
  required:
  - candidate_content
  - ip_boundaries
  optional:
  - platform
  - source_materials
output_contract:
  required:
  - risk_flags
  - safe_rewrites
  - manual_checks
  - display_text
  - detail_text
  - source_ids
  - evidence_gaps
  - missing_inputs
  - human_review_points
  - methodology_anchors
  - frontend_display
  requires_human_review: true
quality_rules:
- 风险必须给出具体触发表达或缺口。
- 改写建议要保留业务意图但降低风险。
- 需要授权或事实核验的内容必须进入人工确认。
guardrails:
- 不得绕开人工审核。
- 不得弱化合规风险。
- 不得建议自动发布高风险内容。
sample_refs:
- script_review_boundary_v1
- publish_copy_risk_v1
applicable_modules:
- strategy
- content_plan
- production
missing_input_rules:
- 缺少上游资料时只能生成待人工复核草稿。
- 证据不足时必须标明需补资料,不得包装成完整结论。
surface_constraints:
  display_text_max_chars: 60
  detail_text_required: true
  allow_multiline: true
  truncate_strategy: detail_only
frontend_display_rules:
  surfaces:
  - input_placeholder
  - card_title
  - card_summary
  - tag
  - button
  - status_top
  - recommend_reason
  - error_hint
  - detail_panel
  - governance_only
  default_surface: card_summary
  display_text_max_chars: 60
  detail_text_location: detail_panel
  hide_internal_keys: true
eval_checks:
- name: 资料充分时输出短结论和完整详情
  expectation: display_text 可直接进入界面,detail_text 保留证据和推理。
- name: 缺少输入时返回证据缺口
  expectation: missing_inputs/evidence_gaps 有业务化说明,不伪装成完成。
- name: 人工确认边界清晰
  expectation: human_review_points 说明用户需要确认的具体事项。
methodology_anchors:
- content_safety_boundary
- human_review_boundary
- business_stage_fit
```

<!-- CLIPMIND_DEFINITION_END -->

## 输出契约

只输出治理定义要求的字段和结论；不得顺手重写被评审内容，不得删去缺口、风险或人工复核点。

无论属于哪种类型，输出都必须满足：

- 清楚说明实际使用了哪些材料；未使用的材料不应暗示为已读取。
- 把证据缺口、风险、待确认假设和人工确认点保留在结果中。
- 不自动发布、不自动投放、不写外部系统、不把候选内容描述成已通过审核。
- 如用户要求保存本轮结果，只能写入当前案例的 `outputs/`，文件名包含日期、Skill 技术 ID 和轮次。

## 证据不足时

仍可安全生成基础草案时，必须逐项标注“待验证假设”；无法在不编造的前提下继续时，停止生成主体，只返回：已知信息、缺失信息、为什么缺失会影响结果、建议补充的最小材料。

## 调优规则

普通调用只生成结果，**不得自行修改 Skill**。只有用户明确说“优化当前 Skill”或同等意思时，才允许修改当前 Skill 目录，并遵守：

1. 先把用户反馈拆成“保留、删除、加强、格式、边界”五类；不确定处先列为待确认。
2. 只修改当前 `clipmind-governance-content-boundary-v1`，不联动修改其他 Skill。
3. 不改 `references/original.md`；它是初始基线。不得削弱证据要求、人工确认边界和禁止外部动作的护栏。
4. 修改后用同一份材料复跑，并追加测试：材料缺失、越界请求、输出契约三个场景。
5. 把版本、反馈原文、改动摘要、复测结果写入根目录 `tuning-records/clipmind-governance-content-boundary-v1/`。
6. 用户明确确认满意后，才能按根目录说明生成回收合并包；不得自动写回 ClipMind。
