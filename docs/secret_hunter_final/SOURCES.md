# 本轮实际阅读与接入点

本轮不复制或运行外部 bot 的代码。下载材料保存在 `runs/final-20261113/sources/`，其 SHA-256 在 `source-hashes.json`。发布 ZIP 仅使用本仓库自己的 Python 实现。以下机制是有限适配，不是论文成绩复现。

| 资料及阅读位置 | 本轮接入 | 实验约束与结果位置 |
| --- | --- | --- |
| [Silverfish 固定提交](https://github.com/noHero123/silverfish/tree/cf6d1657e9dc99b9bcac9cc6e3c26f6ed8d0f2c7)，`Ai.dosomethingclever`、`MiniSimulator.doallmoves`、`cuttingposibilities` | 保留原斩杀证明优先级；T 候选在 `turn_search.plan` 为同一首动作保留两种资源特征的终点 | 仍只评估最多六个回应终点、相同节点与时间预算；不移植其忽略奥秘的斩杀假设。`endpoint-coverage.json` 记录覆盖筛选失败 |
| [2018 PredatorMCTS 源码](https://hearthstoneai.github.io/files/bots/PremadeDeckPlaying2018/BotPredatorMCTS.zip)，`MCTSSimulatorExt.simulateOpponentWithPrediction`；[比赛档案](https://hearthstoneai.github.io/botdownloads.html) | 对照本仓库 `public_response.worst_reply`，在整回合结束状态后考察对方回应；离线各路线采用共同初始世界和相同冻结后续策略 | 外部源码以预测手牌分配各叶预算。本轮隐藏手牌只在离线标签中出现，运行策略不接收真实对手配置。随机动作后重新读取引擎观察 |
| [Choe 与 Kim，2019 MCGS](https://ieee-cog.org/2019/papers/paper_257.pdf)，III-B/D/E/F、Algorithm 1；[比赛档案](https://hearthstoneai.github.io/botdownloads.html) | 有限的完整回合分支、保留实体与站位的状态去重、同一可见状态的多个未来世界；`counterfactual.restore/execute` | 原始样本精确恢复种子与动作前缀；另外两个样本只重排剩余牌序和后续 RNG，保持原模拟手牌。未宣称穷举所有兼容手牌，也未重试在线 MCGS |
| [Darwin Gödel Machine v1](https://arxiv.org/html/2505.22954v1)，§3、A.2–A.4 | `development/secret_hunter_final/lineage.json`、不可变候选快照、失败后另建 L2/ML2 | L 的保守白名单漏掉驯兽师，已从指定错例定位并另建后代；旧快照保留。T 因动作覆盖不足拒绝，不把额外计算当作提升 |
| [Optimizing Hearthstone Agents v1](https://arxiv.org/html/2410.19681v1)，§3.2、Algorithm 2 | `study.py` 复用旧账本、进程监督与严格配对，父代和变体使用同批新种子 | 冻结对手而非共进化；以终局结果选策略。`learn.py` 仅在训练种子组上拟合单一阈值规则，然后锁定再读取留出标签 |

本轮另读了 `docs/secret_hunter_response/SOURCES.md`，并逐段对照候选的 `turn_search.py`、`chance_search.py`、`public_response.py`。在 T 的 36 个 `top_action_outside_effect_coverage` 状态中，20 个启动随机搜索，17 个实际比较了至少两个根动作并完成比较；1 个因 baseline 超出覆盖退出，2 个因回应不受支持退出，其余未激活随机搜索。不能把“调用了 chance_search”写成“比较了备选”。

课程规则重新下载自 [HW2](https://bu-agenticai-class-fall26.vercel.app/materials/assignments/hw2.md)，并与本地课程包核对：每次决定硬限 180 秒；项目完整 Python CLI 工程目标为 2 秒；运行时只能看正常可见状态和本局公开历史；一份不超过 10 MB、单 Skill 文件夹、仅 Python 脚本的 ZIP。卡牌效果使用安装的 hs_arena 0.2.2 数据与 bundled Fireplace：杀戮命令 3/5 点，猎人奥秘按攻击或随从出场触发，死亡缠绕对友方阿曼尼造成 1 点可激怒，鹰角弓仅友方奥秘揭示增加耐久。对应引擎测试见 `face-lethal-checks.json` 和运行目录中的 `inherited-mechanisms.log`。
