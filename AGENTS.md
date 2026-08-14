# Skill Forge 工作规则

本项目只用于内置“赵玥玥”MOCK IP 上下文下的 32 个纯文案 Skill 受控调试，不是 ClipMind 工程。

## 每次对话必须执行

1. 完整读取 `.agents/skills/clipmind-skill-tuner/SKILL.md` 并按其流程工作。
2. 读取 `Skill不可修改边界.md`、`inventory/tuning-order.json`、`fixtures/ip/赵玥玥/scenarios.json` 和本地进度 `.skill-forge/progress.json`；进度不存在时由脚本初始化。
3. 素材库为空时由 `progress.py init` 自动装载赵玥玥 MOCK 资料。只读取当前场景列出的材料，不得混入其他客户、旧对话、互联网或模型记忆中的事实。业务 Skill 内旧路径 `ip-cases/<案例编号>/` 在本项目中统一解释为根目录 `IP素材库/`。
4. 一次只打开、运行和修改一个 `skills/<技术ID>/`；已有进行中的 Skill 时不得切换。
5. 原始材料和 `references/original.md` 只读。

## 修改授权

用户回复 `不OK：<反馈>`，即授权你在**当前 Skill 的允许区域**做与本轮反馈直接相关的最小修改并同材料复跑，无需再要求用户说“优化当前 Skill”。

不得把以下内容当作修改授权：普通提问、希望重跑、补材料、只评价某一段但未表示不满意。

每次修改前区分：当前 IP 个案、可通用方法、产品契约变更。当前 IP 个案只影响本轮生成；产品契约变更必须拦截并说明；只有可通用方法进入候选 Skill。

## 硬边界

- 不改其他 Skill，不顺手重构，不统一模板。
- 不改身份、路由、模块/SOP 阶段、IP/global 属性、工具、权限、输入输出契约、必需交付模块、人工确认语义、证据与禁止外部动作护栏。
- 人工边界既不能削弱，也不能擅自加强。
- 不把当前 IP 的名称、产品、事实、案例、数字或口头禅写进通用 Skill。
- 只有 `inventory/tuning-order.json` 中的 32 个纯文案 Skill 可以启动、修改和打包；治理、共享组件、视觉、生图及其他排除项一律不进入操盘手流程。
- `references/original.md` 必须通过 `inventory/baseline-locks.json` 的 SHA-256 检查；不得修改基线、锁文件、清单、校验器或测试来放行候选。
- 小红书图文 Skill 只调标题、分页文字、正文和标签等文字方法，不调画面、版式、配图、颜色或字体。
- 修改后必须运行 `skill_guard.py`；未通过不得复跑、不得让用户确认、不得交付最终版。
- 不写回 ClipMind，不自动提交、推送、发布、投放或改变任何外部状态。

## 每轮结尾

始终给用户两个固定选项：

1. `OK，完成这个 Skill`
2. `不OK：请直接写修改意见`
