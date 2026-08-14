# 本地调试记录

Codex 会按 `tuning-records/<技术ID>/` 保存每轮固定输入、完整输出、反馈原文、修改范围和复跑结果。操盘手明确回复 OK 后，还会写入 `acceptance.json`；没有与当前 Skill 和轮数匹配的确认凭据，最终打包会被拒绝。本目录内容默认不进入 Git。
