# 来源与边界

本轮从指定提交 `8c158c07280788d7b7872476dd728ba43e3e71ca` 建立独立 worktree。先读上一轮 `docs/secret_hunter_long/{REPORT,REPRODUCE,CASE_STUDIES,SOURCES}.md` 与 `final-validation.json`，基线固定为 DARCL2，不复用旧脚本中的 B 定义。

课程规则：[HW2](https://bu-agenticai-class-fall26.vercel.app/materials/assignments/hw2.md)。本地快照 SHA-256：`994756797ee569ea368cd7938a0d17cb73af86475a7846b8d5dab6cd0937a27a`。五分完成奖励扣弃权；Bot 1 的 5–6 胜取得 +3，Bot 2 的 3–4 胜取得 +2，Astra 每胜 +1。可核实的历史 10 分回执为较早 C2：Bot 1 5/6、Bot 2 2/4、Astra 1/4。DARCL2 和本轮候选没有新的正式回执；本地代理胜率不等同正式成绩。

只使用仓库已有 `development/teacher_eval/core.json` 的六个对手、`guardrail.json` 的十四个对手及课程 Greedy Mage。引擎固定 `hs-arena 0.2.2`，341 个代码/资源文件及依赖版本、对手文件均在新账本 manifest 中保存哈希。对手代码、牌表与历史账本未更改。

上一轮 SOURCES 列出的 Miller 合法分支分配、PredatorMCTS 的 `simulate` / `simulateOpponentWithPrediction` / `getPredictionMap` 只作为已见机制背景。RJC 独立修正课程投影中确定性飞刀召唤的覆盖；PRR 使用真实课程引擎产生的配对终局标签，拟合固定公开特征的岭回归残差。PRR 在原六个可见回应搜索完成之后打分，不增加恢复搜索，不把原 48 节点拆成 32/16，也不读取预测或真实暗手，因此不重复上一轮 TRPLY/TRPLY2 的实现。没有复制第三方 bot 源码，也没有运行新对手。

反事实根校验原公开前缀、根状态和原世界基线终局。原世界与额外世界分别标注；额外世界配对重排双方剩余牌序及后续 RNG，**原隐藏手牌固定**，不能声称覆盖所有与公开历史相容的暗手。H1/H2 相应的世界 2 与独立来源标签在假设及源码冻结后读取；H4 再使用的训练根及三个世界都已经见过，不再称作留出。所有种子、代理名称、隐藏世界和教师标签仅在离线驱动中；Skill 决策只读取课程发布的公开状态与己方已知信息。

历史报告、原正式回放与全部已知旧种子均为已见数据。对本机可读取的旧账本、汇总与根文件核查新种子不重叠；缺失的历史原始归档没有被宣称为已经重放。
