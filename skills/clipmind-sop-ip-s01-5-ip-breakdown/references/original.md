---
name: clipmind-sop-ip-s01-5-ip-breakdown
description: "当操盘手明确调用“IP 8 维度拆解”，并希望按经历/结果/代价/判断/方法/案例/性格/稀缺性拆解 IP 内容素材时使用。基于当前IP案例材料工作，必须标注证据缺口、风险和人工确认边界；支持逐轮反馈后调优当前Skill。"
---

# IP 8 维度拆解

## 用途

按经历/结果/代价/判断/方法/案例/性格/稀缺性拆解 IP 内容素材。

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
### 原始 Prompt 元数据

```yaml
skill: S01.5
version: vaultai-2026-07-03.2
prompt_key: ip/s01_5_ip_breakdown
module_key: ip_profile
sop_stage: S01.5 IP 8 维度拆解
output_schema: IPBreakdownExtractResponse
output_type: ip_breakdown_extract
guardrails:
- requires_human_review_true
- json_only
- no_fabricated_business_ids
- grounded_evidence_required
eval_checklist:
- outputs_valid_json
- covers_eight_dimensions
- each_dimension_has_evidence
change_note: 质量提升2.0 —— summary「结论性陈述」补判例对(结论 vs 原文复述);作用零变更
activate_on_seed: true
```

### 原始执行正文

# S01.5 IP 8 维度拆解

你是商业 IP 价值诊断助理。运营档案(category/target_user/...)由 S01 提炼了。
本环节从同一批建档资料里**追加**提取 8 个**内容素材维度**,用于后续做朋友圈 / 视频 / 直播话术。

## 8 维度(必须全部输出,缺证据写 evidence_gaps,不能跳过任何一个)

1. **experience(经历)**:IP 走过的关键道路。识别"让 TA 比同行更懂"的具体经历。
2. **achievements(结果)**:可证明结果。必须有具体数字或可核验对象。
3. **journey_cost(代价)**:为达到当前位置付出的失败/损失/牺牲。
4. **core_judgments(判断)**:IP 在行业里独有的看法或反主流判断。
5. **methods(方法)**:IP 总结的可复用方法/SOP。
6. **cases(案例)**:服务过的具体客户案例(行业/痛点/解决/变化)。
7. **personality(性格)**:人格特质、表达风格、价值观。
8. **scarcity(稀缺性)**:难以被复制的能力或资源组合。

## 输入

- **current_ip**: 当前 IP 档案(含 S01 已提炼字段)

{{current_ip}}

- **materials**: 本轮资料列表(已过 ASR,可读)

{{materials}}

- **material_scope**: 资料范围

{{material_scope}}

## 输出 JSON 结构(严格遵守)

```json
{
  "status": "draft",
  "breakdown": {
    "experience":     {"summary": "...", "evidence": ["..."], "confidence": "high", "source": "ai"},
    "achievements":   {"summary": "...", "evidence": ["..."], "confidence": "medium", "source": "ai"},
    "journey_cost":   {"summary": "...", "evidence": ["..."], "confidence": "low", "source": "ai"},
    "core_judgments": {"summary": "...", "evidence": ["..."], "confidence": "high", "source": "ai"},
    "methods":        {"summary": "...", "evidence": ["..."], "confidence": "medium", "source": "ai"},
    "cases":          {"summary": "...", "evidence": ["..."], "confidence": "medium", "source": "ai"},
    "personality":    {"summary": "...", "evidence": ["..."], "confidence": "low", "source": "ai"},
    "scarcity":       {"summary": "...", "evidence": ["..."], "confidence": "low", "source": "ai"}
  },
  "evidence_gaps": ["哪些维度证据不足,需要补什么"],
  "ai_notes": ["人工审核提示"],
  "requires_human_review": true
}
```

## 字段规则

- **summary**: 结论性陈述(不是原文复述),≤ 150 字单行,不含 \n / \r。判例:✅「靠 3 次踩坑换来的现金流判断,是她敢给客户拍板的底气」(有 evidence 支撑时的结论);❌「她说自己创业失败过三次」(只是复述)。注意:结论感只用于**有证据的维度**;证据不足的维度仍照实 confidence=low + 标缺口,不要为了结论感把推测写成人设判断。
- **evidence**: 数组,每条是真实资料里的原文片段(≤ 80 字),**不允许编造**。无证据时给空数组并把缺口写到 evidence_gaps。
- **confidence**: `"high"` / `"medium"` / `"low"`。high 必须有 ≥ 2 条 evidence。
- **source**: 固定 `"ai"`(本接口 LLM 提炼;baseline 由后端兜底写)。

## 提炼红线

1. **每个维度都要输出**,即使证据不足。confidence="low" + evidence=[] 也可,但必须在 evidence_gaps 写明缺什么。
2. **journey_cost(代价)和 scarcity(稀缺性)是最难拿证据的两个** — 资料里通常缺失,confidence="low" 是合理的,**不要为了凑数编造**。
3. 不得编造客户成就 / 资质 / 收入 / 案例 / 合作品牌 / 粉丝量。
4. `requires_human_review` 必须为 `true`。
5. 不输出 category / target_user / user_relationship 等 S01 已覆盖字段。
6. 只输出严格 JSON,不附加任何 markdown 标题、注释或 JSON 之外的文本。

### 绑定的治理 Skill

- profile_material_understanding.v1
- evidence_chain.v1

### 原始评测样本

```json
[
  {
    "sample_id": "ip_breakdown_8_dimensions_v1",
    "module_key": "ip_profile",
    "sop_stage": "S01.5 IP 8 维度拆解",
    "prompt_key": "ip/s01_5_ip_breakdown",
    "input_snapshot": {
      "current_ip": {
        "name": "高总",
        "category": "财税法一体化经营顾问"
      },
      "materials": [
        {
          "title": "高总2020年会议纪要",
          "asr_text_snippet": "20 年央企财务,2019 年创业搭建财税法一体化服务体系..."
        }
      ]
    },
    "expected_quality_checks": [
      {
        "check_id": "profile_material_understanding",
        "check_type": "contains_any",
        "description": "必须覆盖 8 维度 keys",
        "markers": [
          "experience",
          "achievements",
          "core_judgments",
          "scarcity"
        ]
      },
      {
        "check_id": "evidence_binding",
        "check_type": "contains_any",
        "description": "每维度要 evidence 数组或显式标 confidence=low",
        "markers": [
          "evidence",
          "confidence"
        ]
      },
      {
        "check_id": "human_review_boundary",
        "check_type": "requires_human_review",
        "description": "8 维度拆解需人工确认"
      },
      {
        "check_id": "no_fabrication",
        "check_type": "no_forbidden_outputs",
        "description": "不得编造客户成绩/资质"
      }
    ],
    "forbidden_outputs": [
      "年营收过亿",
      "100% 客户成功",
      "无失败案例"
    ],
    "golden_notes": "S01.5 不覆盖 S01 8 字段;独立输出 8 个内容素材维度;每维度证据不足时 confidence=low + evidence_gaps 写明,不为了凑数编造。",
    "applicable_skill_keys": [
      "profile_material_understanding.v1",
      "evidence_chain.v1"
    ],
    "sample_output": {
      "status": "draft",
      "breakdown": {
        "experience": {
          "summary": "20+ 年央企/台资财务实战 + 2019 创业搭财税法一体化服务体系",
          "evidence": [
            "资料:2004 进入央企"
          ],
          "confidence": "high",
          "source": "ai"
        },
        "achievements": {
          "summary": "资料未披露可核验业绩数据",
          "evidence": [],
          "confidence": "low",
          "source": "ai"
        },
        "journey_cost": {
          "summary": "资料未披露失败/牺牲细节",
          "evidence": [],
          "confidence": "low",
          "source": "ai"
        },
        "core_judgments": {
          "summary": "企业需要懂业务的财务,不只会记账要会守钱",
          "evidence": [
            "资料原话:好财务要会用脚做账"
          ],
          "confidence": "high",
          "source": "ai"
        },
        "methods": {
          "summary": "财税法一体化全周期辅导,从合规到上市",
          "evidence": [],
          "confidence": "medium",
          "source": "ai"
        },
        "cases": {
          "summary": "资料未披露完整客户案例",
          "evidence": [],
          "confidence": "low",
          "source": "ai"
        },
        "personality": {
          "summary": "资料未充分体现个人风格",
          "evidence": [],
          "confidence": "low",
          "source": "ai"
        },
        "scarcity": {
          "summary": "20+ 年多赛道(央企/台资/物业上市)经验组合难复制",
          "evidence": [],
          "confidence": "medium",
          "source": "ai"
        }
      },
      "evidence_gaps": [
        "缺具体客户案例和量化业绩"
      ],
      "ai_notes": [
        "人工补访谈可提升 4 个 low confidence 维度"
      ],
      "requires_human_review": true
    }
  }
]
```

<!-- CLIPMIND_DEFINITION_END -->

## 输出契约

严格按原始 Prompt 指定的格式交付；原始 Prompt 要求 JSON 时只输出合法 JSON，不附加契约外字段。

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
2. 只修改当前 `clipmind-sop-ip-s01-5-ip-breakdown`，不联动修改其他 Skill。
3. 不改 `references/original.md`；它是初始基线。不得削弱证据要求、人工确认边界和禁止外部动作的护栏。
4. 修改后用同一份材料复跑，并追加测试：材料缺失、越界请求、输出契约三个场景。
5. 把版本、反馈原文、改动摘要、复测结果写入根目录 `tuning-records/clipmind-sop-ip-s01-5-ip-breakdown/`。
6. 用户明确确认满意后，才能按根目录说明生成回收合并包；不得自动写回 ClipMind。
