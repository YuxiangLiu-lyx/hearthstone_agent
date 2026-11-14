# 执行中检查点

## 2026-11-14 10:45 UTC 更新

最新已提交 `d7751b0`。工作继续；选拔与最终种子尚未打开，所有候选仍不可变。以下进度优先于历史检查点。

- coverage-core 完成：B503/600、DARC514/600，18翻胜7翻败。主指标+1.333pp，95% CI[-.25,3.25]pp。与首轮合计110组1320局/版，B1111、DARC1131，37/17，主指标+1.591pp、CI[.303,2.992]pp；这是自适应开发汇总，不是晋级检验。
- mechanism-core 与 lethal-guard 已完成。BL2核心202/240和护栏105/112均与B同终局；分别4次窄证明，实际首次动作分歧4局/1局。TMILL仍归档。TRPLY复验及TRPLY2修正比较正在 recovery-fix 中进行；结束后two-card与mulligan-combination两个预定义控制器依次运行。
- balanced 战术第二轮：B与DARC各300根、50组来源（两版共享50组，不能说100组），各180训练根/30组与120留出根/20组。每版家族150Astra/100Bot2/50Bot1。B4083个终局任务在跑；DARC4122任务已入队，当前队列启动时尚未加入，需下一次cfqueue调用。
- B轮结束后显式运行 `learn_tactical --batch coverage-core --arm B --candidate-name BT2`；DARC完成后用 `--arm DARC --candidate-name DARCT2`。门槛通过才生成真实策略续局。新增 `evaluate_policy.py` 验证相同源根/暗牌世界/前缀，在真实无状态策略执行后重验net>=3、>=3正组、动作确实改变；通过后仍需新种子自然整局。
- 两个新opening case已完成共4辅助整局，见OPENING_CASES.md：一翻胜一回归。精确核对初始手牌、动作、回合和赢家；旧标签未保存逐步状态哈希，不声称比较过旧逐步状态。辅助总次数12（2Luna、6换卡重放、4起手重放）。
- 选择与最终冻结防线已加强：selection-plan固定臂顺序、核心/护栏批次，第一次选择比赛即阻止开发与新标签；两池完整后select_challenger唯一选版。release prepare与freeze必须匹配selection-decision。最终recommend必须有B及挑战者两个精确解包路径的runtime-NAME.json验收。
- 执行harness源码内容寻址归档已加到CF请求与主批次启动。历史5个缺失harness版本全部从git/精确中间差分恢复并校验SHA，零未解析。新的请求会自动存源码。

当前任务PID以SQLite meta为准，禁止仅凭旧PID杀进程。旧run_plan控制器在新增“主批次完成”断言之前已启动；如需中止主批次，必须先停止其父控制器，避免继续挖部分来源。正常无需中断。最终预算仍预留5000整局，已定义主线9896局，视回应迁移/学习结果决定少数新候选与选择池规模。

## 2026-11-14 10:00 UTC 更新（以下优先于后面的旧检查点）

最近提交 `996af8e`（此前 `8073855`），之后有新候选/分析器未提交。工作仍继续，最终种子未打开。`REPORT.md` 尚待最后冻结结果生成，已写逐动作 `CASE_STUDIES.md`、`REPRODUCE.md`、`SOURCES.md`。

首批完整：B608/720、DARC617/720（19翻胜10翻败，主指标+1.8056pp，CI−.1389到3.9583）、DWOLF621/720（27/14，主指标+2.1528pp，CI−.5556到5.0694）。都只是开发信号。逐卡完整分层在 `analysis/deck-screen.json`，六个案例引擎逐状态重放全部吻合。DWOLF 的恐狼统计为两张总计，不能把所有489次使用归给替换卡。

mechanism-core 仍进行：B202/240；KO208/240，14翻胜8翻败，主指标+1.4583pp，区间宽；TMILL202/240，五局真正同状态动作分歧，零终局改变，归档不进入下一轮；TRPLY214/240，18翻胜6翻败，128局真实动作分歧，主指标+3.3333pp、CI−1.875到9.1667，需要独立复验；BL2 尚在跑。TRPLY真实节点数657005 vs B460391，最大节点/时间限额相同但实际工作量更多，不能说平均成本相同；两者我方阶段时间截断均0。TRPLY没有恢复专用计数，action_audit中的 recovery_metrics_calls=0 表示未记录，不是没有执行恢复。

第一轮战术4771标签（含10烟雾）完成，无新增错误、全部终局胜者1/2。学习入口已运行：训练规则 develop、mana<3，648未来/36训练组净+7；432留出未来/24组净−9（17翻胜26翻败），拒绝，不生成BT1。多世界教师在144留出根的原世界108→110（3/1），CI跨零。下一轮不扩模型，先补家族覆盖；首轮339/360根Astra、15Bot2、6Bot1。新增 `--balance-families` 采样，下一批每组六根目标3Astra/2Bot2/1Bot1，仍最早T1–5分岔、胜负都含。

固定留陷阱确认全部完成：B144起手/48组107→135（36/8），DARC106→136（37/7）；全3600起手各命中144=4%。条件增益19.44/20.83pp不能称全局收益。两个规则通过事先net>=3、>=3正组门槛，BM/DARCM各144次实际CLI输出都与锁定标签动作相同，最大约.10s。`opening_runtime.py` 最初误把待玩家一换牌时的玩家二可见开局直接当CLI决策状态，返回空动作；已改成真实引擎先执行待处理对手换牌再probe，记录 `opening-runtime-probe-fix.json`。此隔离探测错误不影响已完成终局标签，候选未改。

新不可变候选：TRPLY2修复下一回合英雄攻击资格，实际引擎验证旧投影漏掉“上一回合已攻击→下一回合装备弓后攻击”，新版生成的攻击被引擎接受；同32回应+16恢复预算，额外记录覆盖计数。`recovery-refresh-check.json`。WOOZE=DWOLF父代再误导换第二软泥怪，相对B恰好两张，实际submit_deck通过。BML2、DARCL2、DARCML2分离已确认M与L2组合，均真实验牌。24项BL2边界测试全部通过，新文件 `check_face_lethal.py` 和 docs/face-lethal-checks.json。

已定义的主线后台顺序（只能跑这些明确命令，不自动提代码）：

1. 当前 continue_defined：mechanism-core → lethal-guard（B/BL2，4护栏组51403000起）。
2. run_plan coverage-plan：等lethal-guard完成，coverage-core B/DARC新50组51404000起，各600局；随后两版各300根、3未来、家族分层入CF队列。学习必须显式分别 `learn_tactical --batch coverage-core --arm B --candidate-name BT2` 与 DARC/DARCT2，避免复用BT1名字。
3. run_plan recovery-fix-plan：等coverage-core完成，B/TRPLY/TRPLY2新20组51407000起。先于结果写了 `response-transfer-gate.json`：正主指标、各家族回归<=2.5pp、无错误、至少10局实际动作分歧；两版符合时最高主指标，平手选修正TRPLY2。过门后必须Codex实际读结果，再构造M/回应与跨DARC的新20组因子对照，不能自动提代码。
4. run_plan two-card-plan：等recovery-fix完成，B/DWOLF/KO/WOOZE新30组51408000起，两个单卡父代都重测。
5. run_plan mulligan-combination-plan：等two-card完成，B/BM/BL2/BML2/DARC/DARCM/DARCL2/DARCML2新30组51409000起，共2880自然频率整局，分离卡组、M、L2和组合。含M或换卡的组合不适用独立BL2例外。

CF当前空闲；confirmation-queue已完成全部591新留牌标签，总mulligan2516。总CF尝试7375=7287完成+88早期harness错误。等coverage-core挖好新根后再运行 tactical 队列；第一轮末次结果和规则锁都保留。若BT2/DARCT2通过固定路线门槛，学习器会入队真实无状态候选续局，必须跑完并比较实际终局后再自然整局。

仍需：监控完成批次，逐个 comparisons/action_audit；在现有两牌表因子对照后决定少数候选。总已定义完整局数9896（不含辅助），至少5000预留最终，选型样本须控制在总非最终15000以内。若加入回应/M迁移20组8臂=1920，则选择池可用30–40核心组+8护栏、约4–5臂，事先锁计划，不能超过预算；最终每版100核心+16护栏仍保持。最终候选唯一后release prepare、study freeze、本地提交，再打开完整CLI最终。建议先用新pilot seed51400010–11做6并发CLI吞吐/2秒检查，通过后才考虑选择/最终6并发，否则保持3。完整最终3并发约1.85h，仍有充分12h预算。

`study.py` 已修复selection guard阶段：护栏用cli_development执行避免旧分析器假定有Astra/Bot2；最终唯一选择须在核心+护栏都齐后按预注册最大主指标和可靠性手动/新入口确认，不能让护栏覆盖选型结论。archive去掉继承的不存在Y1。`learn_tactical` 生成规则限T1–5并记录parent_action；实际policy CF能统计动作差。候选都不可变，任何改代码另取名字。

最终还要精确ZIP冷启动/故障/seq入口检查、真实Luna两座位链路（已完成开发B一次47动作）、所有来源/配对CI/动作分母/失败/预算和谱系状态、tar哈希与SQLite完整性、唯一推荐ZIP。旧Luna47动作成功记录仍在，首launcher失败保留。No push，无课程提交。

---

原任务全文：`runs/long-20261114/request.txt`。原仓库位于 `/Users/liuyuxiang/developer/hearthstone`；本轮所有工作在 `/Users/liuyuxiang/developer/hearthstone-long-20261114`，Python `.venv/bin/python`。不推远端、不提交课程。

固定预算与种子：`runs/long-20261114/manifest.json` 和 `PLAN.md`。预算从 manifest created 起 12 小时（约 2026-11-14 08:44 UTC），开发截止 8.5 小时，留出 3.5 小时。20,000 整局、24,000 CF、至少预留 5,000 整局。独立最终每版 100 核心组+16 护栏组，共 1,648 场。最终尚未开封。

已完成：B 解包/三个指纹吻合；最新远端核查；两用户旧 ZIP 的 provenance（0066 归档 259 个哈希全匹配）；14 局正式 C2 回放分类；课程规则及 Miller/PredatorMCTS 源码下载/阅读/哈希；6 项实际引擎组合验证；三初始牌表真实 submit_deck；负向 deck guard 5 项；72 场 CLI pilot 三版各23胜；断点恢复保留285个已完成结果，恢复后成功；B 开发720局608胜；26项入口故障/seq/choice等验证均通过。

当前长进程以 SQLite meta 的 pid/cf_pid 为准。主进程执行 `study run --batch deck-screen --arms B DARC DWOLF --start 51401000 --seeds 60 --workers 3 --warm`，日志 `deck-screen.log`；B 已完成，DARC/DWOLF 尚在跑。CF 当前执行 `cfqueue run --kind tactical --workers 3 --limit 6000`，日志 `tactical-labels.log`。抽取360根/60种子组，216根36训练组、144根24留出组，3世界、4,761个终局标签。另有10个pilot smoke标签已通过精确前缀/终局复现。真实原暗手保持固定，替代世界仅重排剩余牌库/未来RNG，务必报告限制。

起手：B 16来源完整8/16子集，共192终局（B11/16，全换9/16，4个败局有可赢子集）。匹配B/DARC各300来源分别70/76独立种子组，873/860终局，全部完成。训练锁定后留出：B trap_no_low train+7、valid+1（2翻胜1翻败），未过>=2门槛；DARC keep_combo_hounds train+6、valid−1（1/2），拒绝。结果 `mulligan-learning-{B,DARC}-*.json`。不按该留出调整规则。

已冻结追加假设：`mulligan-confirmation-plan.json`，同一 trap_no_low 规则在全新51421000–51421299，B/DARC各扫3600个公开起手、各命中144来源/48组，288/303标签已入队待跑。BM、DARCM 已构建但未接受；此为旧规则覆盖不足后的独立复验，不是重用旧留出。可在 tactical 完成后执行 `cfqueue run --kind mulligan --workers 3 --limit 1000`，然后按计划 net>=3、>=3正组筛选。主整局后还需少数候选和父代新种子筛选，再唯一挑战者选择，冻结后最终完整CLI。

候选（全部不可变快照/lineage）：B；DARC=Krush->Arcane；DWOLF=Krush->second Dire Wolf；KO=Misdirection->second Ooze且保留Krush（666局B中13败局拿到未打误导、误导没有T1–3使用，新的可证伪早期场面假设）；TMILL=相同350节点/.08秒 cap内按分支数深度9/6/3；TRPLY=每终点48节点切32回应+16己方无抽牌恢复；BL2=单独窄斩杀补丁；BM/DARCM=仅无低费术士留爆炸陷阱。所有候选须注册/静态验牌后用新种子对照；未通过机制不能并入推荐。

下一批建议预定义：B/KO/TMILL/TRPLY/BL2，20核心组51402000起，原策略单卡与两个冠军机制等预算。等待首批三牌表完整结果后决定双卡；双卡只能从开发通过的单卡起点，并同场包含其单卡父代。KO是保留Krush的另一条线。不得把B/DARC原换牌淘汰。

战术学习入口：`learn_tactical --batch deck-screen --arm B`，必须全部标签完成后。先训练锁规则再读留出；输出独立未来教师（world1/2选、world0验）和实际小规则。若构建BT1，会额外入队真实stateless策略的留出根续局，必须跑完再全局测试。固定路线标签不等于实际小规则效果。新代码需 `py_compile`。

真实 Luna：默认 `/opt/homebrew/bin/codex` 缺ARM vendor。发现 VS Code 内原生 `codex-cli 0.162.0-alpha.17.2`。用课程原SkillSeat、指定gpt-6-luna/medium，PATH仅对测试进程指定真实二进制目录。第一辅助尝试51800000因symlink目录缺code-mode-host、模型提前结束，已保留日志/计费；不能当策略败局或已验收。改真实目录后的51800001正在实际对局，已有逐步Python→act。`relay.py` 可复验。它的审计函数运行中升级过，完成后需重新 audit 并保留原审计，尤其 `game_over_observed` 必须来自模型收到的工具回复，而不只是主机保存终态；逐act必须有匹配的前序脚本输出。辅助局也计入整局总预算。

故障：最早mulligan CF漏按引擎pending座位顺序，88失败尝试存 `cf-errors-initial/`，已修复并全部重跑完成，保留计费；队列新增连续3错误停跑。不能报告总研究零错误，只能单列正式完整CLI可靠性。候选源码未受此离线故障影响。

交付支持代码已写：`release.py prepare/recommend`（复用旧pack但保持B原ZIP；注册容许精确解包路径切换），`runtime.py`（新目录），`analyze.py`（逐卡起手/换走/入手/首次可用/实际用/伤害/分层），`comparisons.py`（配对bootstrap、对手、实际先后手、翻胜翻败）。最终还需完整REPORT/CASE_STUDIES/REPRODUCE、冠军消融、至少3逐动作案例、谱系状态、精确ZIP静态+submit_deck、冷启动/负载分位数与Luna/MCP验收、数据归档/本地git提交。无新候选达标则推荐核验B。最终结果开封后不得改候选或用其结果增加样本。

更新：Luna native 路径修复后的51800001已完成47次真实中转，Python/act逐条一致、正常GAME OVER、零非法/超时/回退；正常战败，链路P95 5.014s，程序内部P95 .0905s。corrected-audit.json含逐act前序脚本检查。完整研究仍保留首次launcher故障。
