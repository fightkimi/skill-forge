---
name: clipmind-sop-method-s10-method-underlying-logic
description: "当操盘手明确调用“视频底层逻辑提炼”，并希望提炼爆款的原理层(为什么爆),所有依据来自已有拆解证据时使用。基于当前IP案例材料工作，必须标注证据缺口、风险和人工确认边界；支持逐轮反馈后调优当前Skill。"
---

# 视频底层逻辑提炼

## 用途

提炼爆款的原理层(为什么爆),所有依据来自已有拆解证据。

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
skill: S10
version: vaultai-2026-05-25
prompt_key: method/s10_method_underlying_logic
module_key: method
sop_stage: S10 底层逻辑提炼
output_schema: MethodUnderlyingLogic
output_type: method_underlying_logic
guardrails:
- requires_human_review_true
- json_only
- no_fabricated_data
eval_checklist:
- outputs_valid_json
- includes_underlying_logic
- includes_replicability
change_note: 视频拆解后追加"底层逻辑"提炼,把战术动作抽象为可复用方法
activate_on_seed: true
```

### 原始执行正文

# S10 视频底层逻辑提炼

你是商业 IP 操盘手培训教练。前一步已经把视频拆成 timeline / pattern_card / shooting / editing /
narrative,你的任务是从这些拆解结果中提炼**底层逻辑**(为什么这么做能爆),写成可复用的方法描述。

## 输入

- **title** / **platform** / **url**:基础信息
- **pattern_card**:模式卡(钩子 / 痛点 / 反差 / 证据 / 行动)

  {{pattern_card}}

- **timeline**:时间轴节点

  {{timeline}}

- **narrative**:叙事分析

  {{narrative}}

- **shooting**:拍摄方法

  {{shooting}}

- **editing**:剪辑方法

  {{editing}}

## 输出 JSON 字段(严格)

```json
{
  "underlying_logic": "200-400 字描述:为什么这条视频能爆 = 用什么底层规律 + 触达哪类用户判断 + 哪个心理触点。不要重复战术动作,谈原理。",
  "replicability_note": "复刻这个方法需要满足的最低条件(题材/赛道/IP 角色)。不能写'任何 IP 都能用'。",
  "applicable_ip_types": ["创业经营顾问","财税法服务","..."],
  "applicable_platforms": ["抖音","视频号","小红书"],
  "trust_content_type": "身份|痛点|判断|方法|案例|产品",
  "key_anti_pattern": "复刻最容易踩的坑(1 句话)",
  "requires_human_review": true
}
```

## 规则

1. `underlying_logic` 必须谈"为什么爆"(原理层),不重复战术动作。
2. `replicability_note` 不能写"任何 IP 都能用",必须给适配条件。
3. `trust_content_type` 必须是 6 类信任内容之一(身份/痛点/判断/方法/案例/产品)— 出自《核心判断》。
4. `applicable_ip_types` ≥ 1 条,描述 IP 角色定位(不是个人名字)。
5. `applicable_platforms` ≥ 1 条,只选输入 platform 同类或更宽泛的平台。
6. 不得编造账号粉丝量 / 播放量 / 互动数。`requires_human_review` 必须为 `true`。
7. 输出**严格 JSON**,不附加任何 markdown 标题、注释或 JSON 之外的任何文本。

### 绑定的治理 Skill

- viral_structure.v1
- evidence_chain.v1

### 原始评测样本

```json
[
  {
    "sample_id": "method_underlying_logic_v1",
    "module_key": "method",
    "sop_stage": "S10 底层逻辑提炼",
    "prompt_key": "method/s10_method_underlying_logic",
    "input_snapshot": {
      "title": "副业第一步别急着花钱",
      "platform": "抖音",
      "pattern_card": {
        "hook": "反常识开场",
        "painpoint": "花钱投课买焦虑",
        "reversal": "先验证再投入",
        "evidence": "评论高频追问第一步",
        "action": "本周做一次低风险尝试"
      },
      "shooting": {
        "composition": "正面口播 + 桌面 demo"
      },
      "editing": {
        "rhythm": "快剪 + 关键句字幕放大"
      }
    },
    "expected_quality_checks": [
      {
        "check_id": "viral_structure",
        "check_type": "contains_any",
        "description": "底层逻辑要谈结构原理",
        "markers": [
          "底层",
          "原理",
          "结构",
          "为什么"
        ]
      },
      {
        "check_id": "evidence_binding",
        "check_type": "contains_any",
        "description": "复刻条件必须基于已拆解证据",
        "markers": [
          "复刻条件",
          "适用",
          "前提"
        ]
      },
      {
        "check_id": "human_review_boundary",
        "check_type": "requires_human_review",
        "description": "底层逻辑入库需人工确认"
      },
      {
        "check_id": "no_fabrication",
        "check_type": "no_forbidden_outputs",
        "description": "不得编造播放量等"
      }
    ],
    "forbidden_outputs": [
      "保证爆",
      "任何 IP 都能用",
      "100% 复刻",
      "播放量过百万"
    ],
    "golden_notes": "S10 底层逻辑提炼基于已拆解证据,只产出可复用方法描述 + 适配条件 + 反模式,不入库不激活。",
    "applicable_skill_keys": [
      "viral_structure.v1",
      "evidence_chain.v1"
    ],
    "sample_output": {
      "underlying_logic": "用'反常识开场'打断用户'起号要先投钱'的惯性判断,把决策成本拆到一周内可执行的小动作,触达的是'怕花冤枉钱'的损失厌恶心理,而不是炫技或制造焦虑。",
      "replicability_note": "适配陪跑型/顾问型 IP(创业 / 自媒体 / 商业认知),不适合纯技能教学(如健身/手工)。",
      "applicable_ip_types": [
        "创业经营顾问",
        "自媒体陪跑教练"
      ],
      "applicable_platforms": [
        "抖音",
        "视频号"
      ],
      "trust_content_type": "判断",
      "key_anti_pattern": "把'反常识'写成情绪化质问会让用户防御加重,要落回具体证据。",
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
2. 只修改当前 `clipmind-sop-method-s10-method-underlying-logic`，不联动修改其他 Skill。
3. 不改 `references/original.md`；它是初始基线。不得削弱证据要求、人工确认边界和禁止外部动作的护栏。
4. 修改后用同一份材料复跑，并追加测试：材料缺失、越界请求、输出契约三个场景。
5. 把版本、反馈原文、改动摘要、复测结果写入根目录 `tuning-records/clipmind-sop-method-s10-method-underlying-logic/`。
6. 用户明确确认满意后，才能按根目录说明生成回收合并包；不得自动写回 ClipMind。
