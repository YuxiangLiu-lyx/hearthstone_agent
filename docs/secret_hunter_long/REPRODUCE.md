# 复验与断点恢复

本轮在本地分支 `research/secret-hunter-long-20261114`，worktree `/Users/liuyuxiang/developer/hearthstone-long-20261114`。原 worktree、旧实验账本和固定牌表验证器未改。最终推荐包、冻结源码指纹和最终有效样本数以同目录 `REPORT.md`、`recommendation.json` 为准。`PLAN.md` 是开始时的预算、种子与晋级门槛。

## 环境与数据

使用 Python 3.11、课程提供的 `hs_arena 0.2.2` 发行包。按发行包 `INSTALL.txt` 安装随包 wheel；不要用当前在线炉石卡池替代课程资源。当前 `.venv` 与 `hs-arena-0.2.2` 是指向原 worktree 的本地符号链接。`runs/long-20261114/manifest.json` 记录实际已安装引擎全部 Python/JSON/XML/TXT 文件 SHA-256、依赖版本、固定代理指纹及源路径。

进入该 worktree 后：

```sh
.venv/bin/python -m development.secret_hunter_long.study status
.venv/bin/python -m development.secret_hunter_long.build
```

`build` 对已有快照只校验，不覆盖。每个候选在 `development/secret_hunter_long/candidates/`；`lineage.json` 保存父代、变动文件、完整有序 30 张牌和源码指纹。原始 B 来自指定 ZIP，原字节哈希必须为 `6b20fe6572857413fcc87b9134d94eb06340fa4be6f62578ac8354a58a9a067b`。新的 deck guard 同时检查课程牌表合法性、多重集替换数不超过 2、原位置与受保护组合数量；每版调用真实 `scripts/decide.py` 检查 `submit_deck`。

SQLite 在 `runs/long-20261114/ledger.sqlite`，完整对局结果与观察在 `batches/<batch>/<arm>/games/`；反事实源局面与终局标签在 `mulligan-sources/`、`mulligan-labels/`、`tactical-sources/`、`tactical-labels/`。每个 CF request 另记执行时 harness 文件哈希。真实暗牌只出现在离线审计标签。

## 已定义批次

所有整局严格以 `(opponent, seed, seat)` 配对。下面的相同命令可在尚未开启选拔时恢复未完成任务，不重做已完成任务。选拔已开启的账本会拒绝继续开发；最终封存账本只用于审计。需要从头重跑时，设置新的 `HUNTER_LONG_RUN` 绝对目录并初始化；必须显式重建对应来源清单，不能把旧绝对路径悄悄当成新数据：

```sh
.venv/bin/python -m development.secret_hunter_long.study run --batch pilot-cli --arms B DARC DWOLF --start 51400000 --seeds 2 --workers 3
.venv/bin/python -m development.secret_hunter_long.study run --batch deck-screen --arms B DARC DWOLF --start 51401000 --seeds 60 --workers 3 --warm
.venv/bin/python -m development.secret_hunter_long.study run --batch mechanism-core --arms B KO TMILL TRPLY BL2 --start 51402000 --seeds 20 --workers 3 --warm
.venv/bin/python -m development.secret_hunter_long.study run --batch lethal-guard --arms B BL2 --start 51403000 --seeds 4 --pool guardrail --workers 3 --warm
.venv/bin/python -m development.secret_hunter_long.study run --batch coverage-core --arms B DARC --start 51404000 --seeds 50 --workers 3 --warm
.venv/bin/python -m development.secret_hunter_long.study run --batch recovery-fix --arms B TRPLY TRPLY2 --start 51407000 --seeds 20 --workers 3 --warm
.venv/bin/python -m development.secret_hunter_long.study run --batch two-card --arms B DWOLF KO WOOZE --start 51408000 --seeds 30 --workers 3 --warm
.venv/bin/python -m development.secret_hunter_long.study run --batch mulligan-combination --arms B BM BL2 BML2 DARC DARCM DARCL2 DARCML2 --start 51409000 --seeds 30 --workers 3 --warm
```

`--warm` 是开发用进程内决策；不加时逐次启动完整 Python CLI。最终与选型阶段禁止 warm。已定义的后台序列在 `defined-next-stages.json`、`coverage-plan.json`，只运行列出的候选和命令，不生成新代码。当前 PID 以 SQLite meta 的 `pid`、`cf_pid` 为准；用 SIGTERM 请求停止，等待活动子进程退出后再恢复相同命令。单写入器文件锁防止误启两个同类 supervisor。不能仅靠旧日志中的 PID 杀进程，应先核对完整命令。

首次恢复审计见 `recovery-before.json`、`recovery-check.json`：285 个已完成结果指纹保持一致，活动任务收尾后继续未完成项。所有启动、失败和中断分别留账，失败不当作策略败局。开发初期的 88 次 mulligan harness 错误保留在 `cf-errors-initial/`；已修复引擎玩家一先换牌的协议顺序，重跑成功。队列连续三个错误即停止，不能静默跳过配对。

## 留牌与战术终局标签

```sh
.venv/bin/python -m development.secret_hunter_long.cfqueue run --kind mulligan --workers 3 --limit 24000
.venv/bin/python -m development.secret_hunter_long.learn_mulligan --arm B --start 51420100
.venv/bin/python -m development.secret_hunter_long.learn_mulligan --arm DARC --start 51420300
.venv/bin/python -m development.secret_hunter_long.label_analysis --arm B --start 51421000 --confirmation
.venv/bin/python -m development.secret_hunter_long.label_analysis --arm DARC --start 51421000 --confirmation

.venv/bin/python -m development.secret_hunter_long.tactical --batch deck-screen --arm B --cap 360 --samples 3
.venv/bin/python -m development.secret_hunter_long.cfqueue run --kind tactical --workers 3 --limit 24000
.venv/bin/python -m development.secret_hunter_long.learn_tactical --batch deck-screen --arm B --candidate-name BT1

.venv/bin/python -m development.secret_hunter_long.tactical --batch coverage-core --arm B --cap 300 --samples 3 --balance-families
.venv/bin/python -m development.secret_hunter_long.tactical --batch coverage-core --arm DARC --cap 300 --samples 3 --balance-families
.venv/bin/python -m development.secret_hunter_long.cfqueue run --kind tactical --workers 3 --limit 24000
.venv/bin/python -m development.secret_hunter_long.learn_tactical --batch coverage-core --arm B --candidate-name BT2
.venv/bin/python -m development.secret_hunter_long.learn_tactical --batch coverage-core --arm DARC --candidate-name DARCT2
```

CF 执行器只处理已入队任务；生成新任务时必须使用归档的源清单和原种子。学习入口在读取留出结果前先写训练规则锁；已有锁则原样重用。所有同源对手、座位和替代未来共享 `seed % 5` 分区，0/1 留出、2/3/4 训练。第一轮战术抽样 Astra 偏多，覆盖审计触发预先登记的第二批家族分层；不能把第一次标签留出改称未见样本。

匹配起手的确认规则已在 `mulligan-confirmation-plan.json` 锁定，用全新 51421000–51421299 源种子；只能验证该规则，不能从这批结果再选另一个。条件样本增益不能当成全局胜率。实际小规则若通过固定路线标签门槛，还必须运行其真实无状态代码续局，再进入未筛选整局。

战术 source0 精确恢复原始前缀和基线终局；world1/2 只重排剩余牌库和未来 RNG，保留原隐藏手牌。每对分支共享同一初始世界，但允许动作改变后续牌序消耗。每步由真实引擎执行且验证合法，继续到终局；固定路线和可部署短规则必须分开报告。

学习器通过固定路线门槛才会创建候选并添加实际策略续局。此时再次运行CF队列，再执行 `evaluate_policy --batch coverage-core --arm NAME`（NAME是B或DARC父代）。未通过时不会创建BT2/DARCT2，也没有应补跑的策略任务。队列启动时固定todo清单；运行中新增的任务要在下一次调用处理。后期CF worker直接执行request所指 `harness-by-sha/<hash>.json` 的源码字节，结果中的 `harness_execution` 明确记载；早期请求仅证明分发时源码，不能追认为同等级执行固定。

## 统计与逐动作证据

```sh
.venv/bin/python -m development.secret_hunter_long.comparisons deck-screen B DARC
.venv/bin/python -m development.secret_hunter_long.comparisons deck-screen B DWOLF
.venv/bin/python -m development.secret_hunter_long.analyze deck-screen
.venv/bin/python -m development.secret_hunter_long.action_audit mechanism-core B TMILL
.venv/bin/python -m development.secret_hunter_long.action_audit mechanism-core B TRPLY
.venv/bin/python -m development.secret_hunter_long.write_cases
```

主要指标为 Astra/Bot2 家族等权。10,000 次 bootstrap 重采整个来源种子；对实际先后手等不等长子层使用配对差总和/局数的比率估计。`analysis/*-paired.json` 保存每个对手、实际先后手和全部翻胜/翻败键。卡位报告含起手、换走、入手、首次可打、使用回合与直接伤害；恐狼光环、误导或奥秘的间接贡献不能从直接伤害归因当作零贡献。

`CASE_STUDIES.md` 的六局已重放，完整双方逐步公开状态与动作在 `case-replays/`。仅重新生成 Markdown 不增加整局次数；重新执行引擎回放必须入辅助尝试账本。

## 冻结、完整 CLI 与真实模型中转

最终只允许 B 加一个选定挑战者。先 `release prepare --challenger NAME` 打包、解包和校验，再 `study freeze --arms B NAME`。以解包后的路径跑 51600000–51600099 核心与 51700000–51700015 护栏，分别 1,200、448 局/版；不得在开封后改候选或按结果追加最终样本。实际冻结命令、选型和最终结果由完成后的报告记录。

在此之前必须先写 `selection-plan.json`，固定有序候选列表以及核心/护栏的batch/start/seeds。两池使用 `study run --selection-stage`，禁止warm。第一次调用会写selection-freeze并禁止继续开发。两池全部完成后执行 `select_challenger`；`release prepare`与`study freeze`都核对这个唯一选择及源码指纹。

冻结后对B和挑战者分别运行以下入口；输出文件名必须与候选名一致，不能只留最后一份验收覆盖另一版：

```sh
.venv/bin/python -m development.secret_hunter_long.runtime --candidate runs/long-20261114/frozen/B/secret-hunter --out docs/secret_hunter_long/runtime-B.json
.venv/bin/python -m development.secret_hunter_long.runtime --candidate runs/long-20261114/frozen/NAME/secret-hunter --out docs/secret_hunter_long/runtime-NAME.json
```

`release recommend`只有在两版完整最终样本和各自精确解包路径验收齐全时才决策。它复制冻结ZIP，不重新打包或修改候选；若不达标，原字节B为推荐。

`runtime.py` 验证冷启动、真实状态、choice、seq 刷新、故障回退和终态。真实课程中转入口：

```sh
.venv/bin/python -m development.secret_hunter_long.relay --candidate PATH_TO_EXACT_UNPACKED_SKILL --mode luna --seed UNUSED_AUXILIARY_SEED --seat 1
```

该入口直接调用课程原 `SkillSeat` 和课程指定 `gpt-6-luna/medium`，核对每个 act 之前确有匹配的 Python 输出及终态工具回复。当前机器默认 Codex launcher 缺 ARM vendor；代码为测试进程指定 VS Code 内原生 CLI 的实际目录，使其能找到伴随的 `codex-code-mode-host`。不同机器应改研究 harness 中这个二进制位置并记录新哈希，不能改冻结 Skill。首次 launcher 失败保留为辅助失败；修复后完整真实对局验收与本地代理胜率分开统计。每次模型对局均计入整局预算。

所有正式课程提交和远端推送由用户决定；本轮只生成本地研究文件与推荐 ZIP。

## 封存与完整性

停止全部本轮写入器、确认无running尝试并完成推荐后，运行 `development.secret_hunter_long.archive`。该入口检查固定引擎/对手及SQLite完整性，生成一致的 `ledger-backup.sqlite`、逐文件SHA清单、原始证据tar和当前git源码tar；哈希记录在 `docs/secret_hunter_long/archives.json`。Skill提交ZIP与研究tar彼此独立，只有前者受课程单文件夹和10MB要求约束。

恢复证据时，将backup复制为ledger.sqlite；若换了工作目录，必须显式记录数据库与请求中的路径迁移。运行环境中的时间预算可能使不同硬件提前截断小范围搜索，因此可复验是指固定代码、输入、种子、引擎和预算协议，不保证任意负载下所有启发式搜索逐指令一致。
