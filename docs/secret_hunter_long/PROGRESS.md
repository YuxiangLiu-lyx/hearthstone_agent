# 执行中检查点

## 2026-11-14 12:34 UTC 更新

开发全部完成。M/L2八版每版360局：B305、BM303、BL2305、BML2303、DARC310、DARCM307、DARCL2310、DARCML2307。两条线M×L2终局交互均零；最终选拔代表BL2与DARCL2。所有父代配对、动作审计及因子报告已读完。72局六并发CLI负载零异常、max0.518秒、51.741局/分钟。

prepare_selection已执行，具体五臂B/BL2/DARCL2/KO/DWOLF；60核心组51500000起、8护栏组51501000起，共4720场，六并发完整CLI。选择与容量计划复制至docs并将在首次选择比赛前提交。最终170核心组51600000–51600169与16护栏组51700000–51700015已锁，原manifest另存。当前整局9968+辅助12=9980；选择后14700，剩5300；最终4976与未来辅助8后总19684。

selection-execution-plan只跑两条已定选择命令。选择一旦打开禁止新开发/CF。须等两池全部完成再select_challenger，按既定最大主指标和精确分数平手顺序挑唯一可靠挑战者，不调参。其后release prepare→git commit→study freeze→runtime两版精确解包路径→最终170+16→recommend→Luna2/Client6辅助→报告、delivery_audit与archive。所有旧检查点的100组均为历史初案。


## 2026-11-14 12:24 UTC 更新

本节优先于下面的历史检查点。候选生成与反事实均已停止；不得额外探索。CF总15580次尝试=15492完成+88初期驱动错误。主批mulligan-combination尚在最后两版，之后cli-load-plan自动执行72局六并发完整CLI；mulligan-analysis-plan在主批结束后自动补齐配对、动作和因子分析。

原牌表B/BL2均305胜，BM/BML2均303胜，原牌表按预先配方选BL2。DARC310、DARCM307（1翻胜4翻败，主指标−0.833pp），留牌总体收益未复现；DARCL2/DARCML2待完成。最终奥术射击线只按selection-design.json的既定顺序和主指标选择。KO、DWOLF为另两张纯牌表备选，共五臂选拔。

12:13 UTC、选拔与最终均未打开时，锁定final_design容量规则：如果全部计划+20未来辅助+100场余量在20000场内，且按CLI实测吞吐预计选拔+最终+30分钟在12小时内，则最终核心170组/版；否则100组。护栏16组保持。170方案共4976最终整局，预计全部含8次最终辅助为19684次。不能在最终开封后按结果扩容。prepare_selection会保存原manifest、amendment和实际选择。

下一步：读全批M/L2及CLI负载结果→prepare_selection→提交具体计划→按计划完整CLI selection-core/selection-guard共4720局→select_challenger→release prepare→提交并freeze→对两版精确解包路径runtime→完整最终核心+护栏→release recommend→推荐包Luna双座位及ClientSeat辅助→文档/审计/封存。所有最终样本数以actual final-freeze范围为准，不能机械沿用历史100组命令。

新delivery_audit检查预算、最少5000最终预留、不可变候选、完整性和包；archive必须最后且无写入器时运行，先提交所有源码/报告，再生成一致SQLite备份、文件哈希和evidence/source tar，最后提交archive哈希记录。原B字节必须保留。无远端push、无课程提交。


## 2026-11-14 11:35 UTC 更新

最新提交0f73a46。DARC第二轮4122CF全部完成；没有生成DARCT2：334训练提案只有原策略满足门槛，留出274/360不变。教师原世界120根86→88（4/2），CI[-3.333,5.833]pp。所有CF当前停止，meta cf_pid=None；15492完成+88初期失败=15580尝试，标签完整性通过（2516留牌、12976战术，10094实际覆盖改动续局、140254前缀核对步）。无需任何新的tactical full batch，也不再扩模型拟合已见留出。

Two-card全部完成：B313、DWOLF317、KO317、WOOZE321/360。DWOLF16/12翻转，主指标+.278pp；KO9/5，+.972pp；WOOZE22/14，+.833pp。DWOLF与WOOZE新批Bot2都−3.333pp。WOOZE比DWOLF多4胜但主指标只+.556pp，比KO多4总胜却主指标−.139pp，故归档，不做M/其他模块迁移。KO与DWOLF留作独立选拔备选；合并开发：KO50组主指标+1.167pp CI[-1.583,4]；DWOLF90组+1.528pp CI[-.556,3.704]。已更新decisions与REPORT，two-card全部分析已完成，卡位附表已刷新。

现在主进程mulligan-combination8臂30组，B即将完成，后续BM、BL2、BML2、DARC、DARCM、DARCL2、DARCML2。对应mulligan-analysis-plan在等待，完成后自动做所有模块父代配对、动作审计、factorial交互。cli-load-plan（session53887）随后自动用B/DARCML2/WOOZE，51400010–11，6并发72完整CLI；只决定并发，不用于选策略。若6并发全可靠、<=2s且吞吐>29.6games/min，选拔最终用6，否则3。

已在结果前记录selection-design.json：最终具体selection-plan等Codex读完自然因子与负载报告再建。5臂顺序[B,原牌表最佳模块线,DARC最佳模块线,KO,DWOLF]，核心60组51500000–59，护栏8组51501000–07。原牌表候选按mulligan-combination主指标选BL2/BML2/BM，1e-12内平手用此列顺序；DARC线候选DARCL2/DARCML2/DARCM/DARC同理。偏好已证明窄斩杀且不额外添加无观察收益的M。要求开发执行无错误。全5版选拔齐后，仍按原manifest最大主指标+可靠性唯一选版，最终门槛不变。预选择主次数9968，选择4720，合14688+当前辅助12=14700，保留5300到最终；最终3296。不要超预算额外探索。

新增lineage_report.py生成LINEAGE.md（区别源码改动/仅牌表配置/未构建提案），card_tables.py生成CARD_STATISTICS.md，report_tables.py生成STATISTICS.md。最终都须重跑。REPORT已是详细执行中草稿，但首段/末段待完成和M结果/冻结结果必须最终重写。源组positive_seed_groups旧字段是至少一次翻胜组，不一定净正；核对BM20净正/6负/22零，DARCM20/7/21，mulligan-group-definition-audit.json，门槛未事后改。

所有剩余交付步骤与11:09条目相同：读M结果、load、建具体选择plan→完整CLI核心/护栏→select_challenger→精确pack/extract→本地commit+freeze→两版runtime-NAME→100core/16guard最终CLI→recommend→精确推荐包Luna两座位（可选ClientSeat6）→统计/报告/谱系/预算/静态验牌→delivery_audit→停止本轮所有workers、SQLite备份/evidence+source archives→最终本地commit与ZIP/hash链接。仍不推远端、不提交课程。说明文档独立fresh worktree复验，避免sealed ledger继续开发或覆盖研究输出。

## 2026-11-14 11:09 UTC 更新

最新提交d139559，之后新增card_tables与附表待提交。完整草稿REPORT.md已写，首段明确选拔/最终未开封；最终须重写为实际交付结论并移除待完成段。STATISTICS.md由report_tables生成；CARD_STATISTICS.md由card_tables生成。archive.py、delivery_audit.py已写，只在最终完成/停止写入器后运行。

recovery-fix完成：B207/240，TRPLY203、TRPLY2 203。各5翻胜9翻败，主指标−1.875pp CI[-5,1.25]pp；Astra−2.5、Bot2−1.25、Bot1零，按预注册transfer门槛两者归档，不做原定1920局回应/M迁移。实际动作分歧137/135局，修正版恢复18113次调用、18007次支持、256462节点；TRPLY与TRPLY2仅2局动作分歧、无终局差。TRPLY两批合计40组主指标+.729pp CI[-2.396,4.062]。四个翻胜/回归实际首分岔已检查，diagnostic存analysis/recovery-fix-flip-diagnostic.json。

B第二轮4083战术标签完成：训练hold_coin且opponent_hunter<1，540未来净+6；留出360未来262→256（2翻胜8翻败），拒绝无BT2。教师world1/2选→world0验：120留出根83→86（5/2），CI[-2.5,6.667]pp，仍不确定。DARC4122标签当前CF队列在跑（PID以meta为准；exec session93410），日志coverage-DARC-labels.log；队列目标总CF尝试15580=7375原有+4083B+4122DARC。DARC全部完成后显式learn_tactical --batch coverage-core --arm DARC --candidate-name DARCT2；若通过，跑实际policy jobs并evaluate_policy，之后再决定20组M/T自然因子批次。

CF执行器现在直接执行request归档的kind-module字节，记录harness_execution。此前请求只证明分发时hash，明确不是独立导入时hash。B队列末段曾加纯决策/回退计数，无基线路线逻辑更改；harness-dispatch-change.json记录限制。不要把早期结果追认成后加的字节固定执行器。

主整局two-card在跑（B360已完，DWOLF将完，随后KO/WOOZE），之后旧控制器自动进入mulligan-combination8臂30组。新增two-card-analysis-plan与mulligan-analysis-plan会在各批全部完成后生成父代配对、动作审计、factorial交互及卡位表；只分析，不自动改候选。

完整原定主线仍9896局；取消回应迁移后可给选拔更大样本，例如5臂60核心+8护栏=4720，另72负载试验与辅助约20仍在15000前最终上限内。若DARCT2实际有效并添加960局4臂M/T自然因子，选拔应相应缩为5臂40核心+8护栏=3520。候选和选拔规模必须等开发齐全再锁，不可提前看选拔结果。

还需：所有开发跑齐/读结果；6并发实际CLI负载pilot（新的51400010起种子，B/DARC及重候选72局）决定最终并发；selection-plan、select_challenger；release prepare精确解包、study freeze、冻结前本地git提交；最终100核心+16护栏每版、两版runtime-NAME；recommend；推荐精确包真实Luna两座位与可选ClientSeat6；完整报告/案例/谱系决定/全预算；delivery_audit、SQLite备份与hash归档、最终本地commit、确认本轮进程全部退出。正式课程与远端不动。

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
