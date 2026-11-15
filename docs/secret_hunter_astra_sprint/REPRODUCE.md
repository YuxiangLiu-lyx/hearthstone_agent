# 复跑与断点恢复

运行目录：`runs/astra-sprint-20261114`，独立源码分支 `research/secret-hunter-astra-sprint-20261114`。Python 3.11，课程 `hs-arena==0.2.2`；对手与引擎资源指纹以 manifest 为准。不要覆盖上一轮账本或从旧 B 生成候选。

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.study status
```

账本中的整局任务由 `(candidate, phase, opponent, seed, seat)` 唯一确定；已完成结果不会重新计费或重新运行。失败与中断保留在 attempts 中；重试也占额度。实际 SIGKILL 恢复演练保存了 479 个已完成结果，6 个在途任务的持久结果被收回，无额外重试。详情见 `resume-check.json`。

反事实任务同样按根、世界、路线唯一登记；源码在每次派发时按哈希归档并执行归档代码。控制器启动时固定待执行清单，因此后来新登记的候选续局需要在本轮结束后再次运行同一命令。

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.cfqueue run --kind tactical --workers 3
```

只在没有另一个控制器持有 writer lock 时恢复。不要并行启动完整 CLI 评测和续局负载；本轮完整 CLI 的计时以六并发为标准。

开发批次可用原命令断点续跑，例如：

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.study run \
  --batch round1-recall --arms DARCL2 RJC --start 62150100 --seeds 40 --workers 6
.venv/bin/python -m development.secret_hunter_astra_sprint.study run \
  --batch round2-ranker --arms DARCL2 PRR --start 62150200 --seeds 40 --workers 6
```

后续单卡、公开手牌资源及独立确认的固定命令：

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.study run \
  --batch round3-arcane --arms DARCL2 DA2 --start 62150300 --seeds 40 --workers 6
.venv/bin/python -m development.secret_hunter_astra_sprint.study run \
  --batch round4-hand-resource --arms DARCL2 EHC --start 62150400 --seeds 40 --workers 6
.venv/bin/python -m development.secret_hunter_astra_sprint.study run \
  --batch confirmation-arcane --arms DARCL2 DA2 --start 62150500 --seeds 80 --workers 6
```

已完成批次的全部翻转局可直接复读，先列原赢变输：

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.inspect_full_flips round4-hand-resource EHC
.venv/bin/python -m development.secret_hunter_astra_sprint.inspect_policy_flips --arm EHC
```

H2 模型训练数据只包括最初早期根及较晚训练根的世界 0/1，按来源种子五折划分；模型源码和冻结系数在 `candidates/PRR/`。已冻结的拟合结果见 `experiments/H2-fitted-ranker.json`。不要重拟合并覆盖同名候选，也不要把已开封标签重新称作留出。

选拔完成后，最终只冻结 DARCL2 和一名挑战者。两池全部完成前不读结果；恢复只补原计划任务，不添加种子或候选。精确包验证和独立复跑入口：

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.reproduce_frozen \
  --source-run runs/astra-sprint-20261114 --verify-only
.venv/bin/python -m development.secret_hunter_astra_sprint.reproduce_frozen \
  --source-run runs/astra-sprint-20261114 --run runs/astra-sprint-replication
```

第二条命令创建全新账本并输出两池的完整复跑命令，绝不重开原账本。它校验原 ZIP、相对路径匹配的引擎资源、依赖、对手及冻结统计代码；复制原字节并登记新的精确解包路径。复跑同样种子是复现，不是新的独立验证。

完整 CLI、注入故障、MCP 协议与真实 Luna 的计时分开。最终真实模型/ClientSeat 复跑使用 `final-acceptance-plan.json` 的预定种子，并继续记入辅助整局额度；策略选拔不使用这些胜负。正式 Slack 提交由用户完成。
