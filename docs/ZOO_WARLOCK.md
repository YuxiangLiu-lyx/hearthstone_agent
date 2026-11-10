# 动物园术候选：攻略、卡组与决策

本页保留 v6 的历史构筑与结果。当前动物园推荐版为 [v7：败局复盘与强度提升](ZOO_OPTIMIZATION.md)，
在新留出集通过相对 v6 的提升验证；主圣骑士 Champion 仍未改变。

状态：独立候选 `development/candidates/v6-zoo-guide`，没有替换圣骑士 Champion。
本轮检索与验证日期：2026-11-10。适用课程 `hs-arena 0.2.2` 固定卡池，不是当前天梯推荐。

## 攻略依据与卡池适配

- [Icy Veins：Classic Zoo Warlock，Kat，2021-03-25](https://www.icy-veins.com/hearthstone/classic-zoo-warlock-deck)：参考低费随从、恐狼、增益随从的经典构筑骨架。该页正文仍写着攻略待补，不能把它当作完整打法指南。
- [CompetitiveHS：NA Legend Zoolock，2016](https://www.reddit.com/r/CompetitiveHS/comments/53tk0r/na_legend_zoolock_decklist_and_guide/)：参考起手找一费、硬币铺两个一费，以及低手牌后用分流续航的经验；不移植其扩展包组件。
- [HearthPwn：Warlock Zoo Deck List Guide，2017](https://www.hearthpwn.com/decks/793674-warlock-zoo-deck-list-guide)：参考有利交换、恐狼站位、弃牌顺序和防清场留资源的原则。下述分数、阈值与课程卡池替代方案均为本项目的实现选择。

卡牌规则以本地 `hs_arena.cards.load()` 和 Fireplace 实际结算为准。末日守卫 `EX1_310`、力量的代价 `EX1_316`、鬼灵爬行者 `FP1_002` 均不在允许卡池，不能照搬历史卡组。课程灵魂之火是 **1 费**，叫嚣的中士是 **1/1**，飞刀杂耍者是 **2/2**。

## 30 张卡组

[机器可读卡组](../development/decks/warlock-zoo-guide.json)，[候选 Skill](../development/candidates/v6-zoo-guide/SKILL.md)，[独立 ZIP](../dist/hearthstone-zoo-candidate.zip)。

| 费用 | 卡牌 | ID | 数量 | 用途 |
|---|---|---|---|---|
| 1 | 烈焰小鬼 | EX1_319 | 2 | 开局抢场 |
| 1 | 虚空行者 | CS2_065 | 2 | 保护核心随从、接受增益 |
| 1 | 银色侍从 | EX1_008 | 2 | 圣盾保留场面 |
| 1 | 叫嚣的中士 | CS2_188 | 2 | 临时加攻完成交换 |
| 1 | 灵魂之火 | EX1_308 | 2 | 节奏解场、终结直伤 |
| 1 | 死亡缠绕 | EX1_302 | 2 | 补刀并补牌 |
| 2 | 恐狼前锋 | EX1_162 | 2 | 邻位加攻 |
| 2 | 飞刀杂耍者 | NEW1_019 | 2 | 后续召唤收益 |
| 2 | 酸性沼泽软泥怪 | EX1_066 | 2 | 二费站场、针对武器 |
| 3 | 麦田傀儡 | EX1_556 | 2 | 亡语保留场面 |
| 3 | 破碎残阳祭司 | EX1_019 | 2 | 永久增益 |
| 3 | 血色十字军战士 | EX1_020 | 2 | 圣盾与增益配合 |
| 4 | 黑铁矮人 | EX1_046 | 2 | 站场并临时加攻 |
| 4 | 阿古斯防御者 | EX1_093 | 2 | 双邻位增益与嘲讽 |
| 6 | 银色指挥官 | EX1_067 | 2 | 冲锋解场或终结 |

26 随从、4 法术，平均费用 **2.33**；曲线为一费 12、二费 6、三费 6、四费 4、六费 2。
银色指挥官承担末日守卫缺席后的冲锋角色，但不等价：费用更高、伤害更低，保留圣盾且没有弃牌。
软泥怪替代旧 Zoo 配方的精灵龙；死亡缠绕替代雪人，以降低曲线并补充小解。此轮只测试这一配方，没有声称它是最优构筑。

## 关键决策的实现

代码：[policy.py](../development/candidates/v6-zoo-guide/scripts/policy.py)。底层评分保存在 [base_policy.py](../development/candidates/v6-zoo-guide/scripts/base_policy.py)，与 Champion 原文件逐字节一致。

| 场景 | 当前规则 | 边界 |
|---|---|---|
| 斩杀 | 原策略最高分达到 100000，直接返回原排序，先于全部 Zoo 修正 | 沿用已有即时斩杀分支；不把飞刀随机伤害视为必达伤害 |
| 起手 | 优先小鬼、行者、侍从，最多两张；已有一费才留一个二费；对牧师/战士有一二费曲线时可留麦田 | 不把削弱后的中士当优质裸下一费；高费和默认灵魂火换走 |
| 低费展开 | 保留原有法力组合评分；支持硬币接两个一费 | 每次动作后重新读取状态 |
| 飞刀顺序 | 法力和场位足够接随从时，提高先下飞刀的排序 | 只估计收益，不预测随机落点 |
| 增益交换 | 比较加攻/加血前后的可行交换价值，优先改善击杀或存活结果 | 只比较本次交换，不声称完整多步最优 |
| 恐狼站位 | 倾向能帮助相邻可攻击随从完成交换的位置；降低插入随从挤掉既有有效光环的分数 | 圣盾/亡语随从略偏向边缘；未实现完整连续送怪链搜索 |
| 阿古斯 | 继续优先双邻位，并计入交换改善及危险时的嘲讽价值 | 依据实际邻位，不假设任意两个目标 |
| 灵魂火 | 计入平均弃牌损失；可保留灵魂火费用时，倾向先出随从；只剩灵魂火且有有价值目标时，先打再分流 | 即时斩杀仍最优先；不会假设随机弃掉指定卡 |
| 分流 | 手牌少时补牌；血甲合计必须大于 `max(8, 对方可见威胁+5)`；牌库非空、手牌小于 9 | 不透支已知生存余量；不会为了这次抽牌烧牌或进入疲劳；不刻意放弃关键站场法力 |
| 清场风险 | 依据对手职业和下回合法力窗口，在已有四个随从、七攻且至少三个脆弱随从时，适度减少继续铺普通随从、提高补牌排序 | 只是公开信息启发式，不知道对手手牌；危险或对手血线很低时不留资源 |
| 转为打脸 | 保留原版低血线加大打脸权重和自身危险时降权 | 没有替换原有攻守转换体系 |
| 自伤 | 三点自伤会杀死自己时，不主动下烈焰小鬼 | 原有即时获胜动作仍先于该规则 |

清场窗口当前为：法师 7 费/4 伤，骑士 4/2，牧师 5/2，术士 4/3，萨满 3/3，德鲁伊 4/1。
它没有覆盖所有清场牌，也不根据隐藏信息推测具体手牌。对局内不保存跨局状态。

## 保留现版本的证据

- Champion 指针、正式提交目录、正式 ZIP，以及 `v4-paladin-search` 研究候选共 **24 个文件**通过前后 SHA-256 校验，全部未变。
- 新候选的 `actions.py`、`decide.py`、`evaluator.py` 与当前提交版本完全相同；合法动作验证、异常兜底、子进程硬超时继续生效。
- 多步斩杀研究模块保留原版本，**没有在 Zoo 中启用**。当前正式 Champion 本来就没有启用该研究模块，不能把它描述为本次已交付的 Zoo 全覆盖斩杀搜索。
- 对 Zoo 两个实验集的 **15,228 个可见决策状态**复核，原版即时斩杀分支触发 **339 次，339 次动作完全保留**；记录动作全部合法。[审计数据](../development/reports/zoo-lethal-audit.json)

## 实测结果与限制

预先固定开发集 12 个种子（6000–6011）、8 个对手、交换双方座位，共 192 局/方案；留出集 20 个新种子（100300–100319）、6 个对手、交换座位，共 240 局/方案。三种方案共 **1,296 局真实引擎对局**。留出开始后没有修改候选策略。

| 方案 | 开发集 | 留出集 |
|---|---:|---:|
| 相同 Zoo 卡组 + 原通用策略 | 149/192，77.60% | 176/240，73.33% |
| Zoo 卡组 + 本次专用策略 | 156/192，81.25% | 188/240，78.33% |
| 当前圣骑士 Champion | 163/192，84.90% | 185/240，77.08% |

Zoo 留出胜率 Wilson 95% 区间为 72.70%–83.08%。相对同卡组通用策略提高 5.00 个百分点，但按种子聚类的配对 bootstrap 95% 区间为 **[-1.25, +11.67] 个百分点**；相对圣骑士为 +1.25 个百分点，区间 **[-6.25, +8.75]**。两者均跨零，未通过既定晋级门槛。

开发集对搜索圣骑士仅 15/24，留出对进化控制牧师仅 16/40，仍有明显弱项。结果不代表天梯或未知对手胜率，也没有证明每项启发式单独有效；此轮验证的是整套规则。

三组全部零非法动作、零超时、零提前退出、零策略异常、零引擎/测试框架失败。[配对比较](../development/reports/zoo-comparisons.json)

其他验证：

- Zoo 专项 14 项通过；候选协议/合法性/异常恢复/超时/随机实战 6 项通过；原 Champion 6 项和原研究版 12 项回归通过。
- 随机抽取 100 个实战状态执行完整 Python CLI，均无错误；平均 59.06 ms，P99 73.22 ms，最大 77.40 ms，包含解释器启动和保护进程。[延迟报告](../development/reports/zoo-cli-latency.json)
- 官方 MCP `client:` 完整对局 2 胜 0 负，零非法动作、超时或失败，验证动态提交卡组和逐步 CLI 执行。
- **本候选未新增 Luna/Haiku 实测。** MCP 客户端和纯 Python 对局均不冒充模型比赛；复用的传输提示之前只在圣骑士上做过 Luna 验证。

## 复现

在项目根目录执行；实验输出目录必须尚不存在。下述已检验种子用于复现，不能再称为新的留出样本。

```sh
.venv/bin/python development/tests/test_zoo.py
.venv/bin/python development/tests/test_agent.py development/candidates/v6-zoo-guide
.venv/bin/hs-arena validate development/candidates/v6-zoo-guide --no-game
.venv/bin/python -m development.benchmarks.run --candidate development/candidates/v6-zoo-guide --population development/opponents/expanded.json --out development/experiments/reproduce-zoo-train --start 6000 --seeds 12 --workers 4 --split train
.venv/bin/python -m development.benchmarks.run --candidate development/candidates/v6-zoo-guide --population development/opponents/holdout3.json --out development/experiments/reproduce-zoo-holdout --start 100300 --seeds 20 --workers 4 --split holdout
.venv/bin/python development/build_zoo.py
```

完整逐局回放、座位、首次行动者、耗时和可见 observation 位于 `development/experiments/zoo-{guide,generic,champion}-{train,holdout}/`；传输测试位于 `development/experiments/integration-zoo-client/`。

独立候选包为 `dist/hearthstone-zoo-candidate.zip`，11,769 字节，解压 30,338 字节，8 个文件；SHA-256 为 `e62cdfc5340fc9984821e091b650575269f5d53ec50eca39042551983d6cccb0`。[构建清单](../development/reports/zoo-build.json)
当前正式包仍是 `dist/hearthstone-agent.zip`，未被覆盖。没有进行正式提交。
