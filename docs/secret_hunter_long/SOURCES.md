# 外部来源与独立实现

本轮先读取[主办方比赛成绩与源码档案](https://hearthstoneai.github.io/botdownloads.html)，再下载对应源码 ZIP。历史名次只用于确认机制来源，不能用来推断课程环境中的收益。两份 ZIP 未发现明确许可文件；本轮没有把其中源码复制到 Skill，也没有执行外部 bot，全部按课程 Python/公开 JSON 接口独立实现。

| 来源 | 实际阅读位置 | 原机制 | 课程差异与本地实现 | 等预算比较 |
|---|---|---|---|---|
| 2020 Premade 冠军 Sebastian Miller | `Naive_Score_Lookahead_Agent.cs`，`MyAgentSebastianMiller2.GetMove` 及内部 `score` | 合法动作数 <5、<25、其余时搜索深度 3/2/1 | SabberStone 与本地可见信息投影不同；TMILL 在继承最大深度 9 内用 9/6/3 分配，不读取实际暗牌 | 与 B 同 350 个我方投影节点、0.08 秒本阶段限额、beam 10、回应候选和回应限额；新 20 个核心种子组 |
| 2018 Premade 冠军 PredatorMCTS | `MCTS/MCTSSimulatorExt.cs`：`simulate`、`simulateOpponentWithPrediction`、`getPredictionMap` | 筛选终点、按公开历史构造预测手牌、对手回应再己方恢复 | B 已有可见攻击及己方奥秘回应；TRPLY 增加己方已知手牌的无抽牌恢复，不引入外部牌表先验或真实暗手 | 每个终点原 48 个回应节点分成 32 回应+16 恢复，原时间与终点数不变；新 20 个核心种子组 |

原下载：

- [SebastianMiller.zip](https://hearthstoneai.github.io/files/bots/PremadeDeckPlaying2020/SebastianMiller.zip)，2,019 字节，SHA-256 `93579a15f767646ee7cf975de102bb8806bbabcce8068a863dea01ea6455a221`。
- [BotPredatorMCTS.zip](https://hearthstoneai.github.io/files/bots/PremadeDeckPlaying2018/BotPredatorMCTS.zip)，1,748,213 字节，SHA-256 `1298f54aeae6714225b3d955f9960f6c0ee7164cdae38f8ffbb8e5aada768f1d`。
- 主办方档案页面快照 SHA-256 `675e8b623ff40dcc1dc564d72174f459064af4ecd03631553097782cb20e60ee`。

TRPLY2 是本轮工程修正：真实引擎证明，上一回合已使用攻击的英雄，下一个己方回合装备弓后可正常攻击。TRPLY 未重置投影的 `hero_attack_available`，漏掉这条恢复分支；TRPLY2 重置攻击资格及回合计数，并加入恢复覆盖计数。对照保留 TRPLY，三版 B/TRPLY/TRPLY2 使用全新 51407000–51407019 且维持 32/16 限额。边界证据在 `runs/long-20261114/recovery-refresh-check.json`；整局成败以 REPORT 中完成的对照为准。

恢复投影是启发式：没有模拟未知抽牌、对手暗手出牌或所有随机触发，不能称为安全证明。TRPLY2 修正一个已证实的遗漏也不自动意味着终局收益。两个冠军机制只有通过实际终局验证才可进入最终候选。

## 课程与运行协议

[HW2 规则](https://bu-agenticai-class-fall26.vercel.app/materials/assignments/hw2.md)下载快照为 14,868 字节，SHA-256 `994756797ee569ea368cd7938a0d17cb73af86475a7846b8d5dab6cd0937a27a`。课程发行版固定 `hs_arena 0.2.2`；安装资源和对手指纹在 manifest。所有线上决策只使用己方可见状态、对方公开状态及本局公开历史。Python 决策，课程指定 Luna 只中转最新 seq 的原样 JSON。比赛种子、代理配置和隐藏世界只属于离线驱动器与标签。

真实模型验证参考了 OpenAI 官方 [Codex 非交互模式](https://developers.openai.com/codex/noninteractive/)和本机 `codex exec --help`；实际执行仍使用课程原 `SkillSeat`。默认 Homebrew launcher 缺 ARM vendor，第一次辅助尝试另有伴随程序路径故障；改用已安装原生 CLI 的实际目录后完成了真实 wait→Python→act→GAME OVER。模型链路时延与完整 Python CLI 时延分开报告，未替换课程模型。

## 本仓库既有证据

已先读 `docs/secret_hunter_final/{REPORT,CASE_STUDIES,REPRODUCE}.md`、`docs/secret_hunter_turn_plans/REPORT.md`、`docs/secret_hunter_response/SOURCES.md`。它们及所有旧种子、旧正式回放均为已见数据。`runs/krush-slot-20261114/` 未找到，未捏造其原始日志。

指定原始 ZIP、源指纹、原 deck.json 哈希逐一吻合。用户提供的 `hearthstone_astra_0066a30.zip` 归档中 259 个文件哈希全部匹配，属于较早研究归档；课程结果 ZIP 可核实 14 局 C2 双奥术射击、无暴龙王，得分 10，Bot1 5/6、Bot2 2/4、Astra 1/4、零弃权。它不代表本轮新策略的正式成绩。来源哈希及逐局分类分别保存在 `source-hashes.json`、`legacy-archive-audit.json`、`formal-replay-classification.json`。
