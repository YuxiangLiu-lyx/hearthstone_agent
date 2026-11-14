# 执行中检查点

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
