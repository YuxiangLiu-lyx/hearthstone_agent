# 复跑与断点恢复

运行目录：`runs/astra-sprint-20261114`，独立源码分支 `research/secret-hunter-astra-sprint-20261114`。Python 3.11，课程 `hs-arena==0.2.2`；对手与引擎资源指纹以 manifest 为准。不要覆盖上一轮账本或从旧 B 生成候选。

本轮已按用户的资源选择交付原版 DARCL2；实际文件为 `delivery-freeze.json`，没有 `final-freeze.json`。下文保留的资源恢复、选择和最终双版本命令是已登记但未执行的流程，不应在已关闭的原账本上重新启动。复核本轮结果使用后面的 `verify_delivery`、`verify_evidence` 和 `development_tables`。

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.study status
```

账本中的整局任务由 `(candidate, phase, opponent, seed, seat)` 唯一确定；已完成结果不会重新计费或重新运行。失败与中断保留在 attempts 中；重试也占额度。实际 SIGKILL 恢复演练保存了 479 个已完成结果，6 个在途任务的持久结果被收回，无额外重试。详情见 `resume-check.json`。

反事实任务同样按根、世界、路线唯一登记；源码在每次派发时按哈希归档并执行归档代码。控制器启动时固定待执行清单，因此后来新登记的候选续局需要在本轮结束后再次运行同一命令。

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.cfqueue run --kind tactical --workers 3
```

只在没有另一个控制器持有 writer lock 时恢复。不要并行启动完整 CLI 评测和续局负载；开发初期采用六并发，资源变化后的实际配置和失败稳定性检查见 [RESOURCE-INCIDENT.md](RESOURCE-INCIDENT.md)。

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
```

原 `confirmation-arcane` 批次因资源变化保留 273 个基线任务，不能把它当成已完成结果，也不要手工重新打开已关闭任务。恢复时仅按 `resource-recovery-plan.json`：固定 16 状态三并发检查通过后，运行登记的新完整 CLI pilot，随后复测 1/3/6 并发。`recovery_capacity --batch recovery-pilot-1 --health <复测 JSON 文件名> --close-original-confirmation` 只读计时、错误和动作稳定性，确认时间/额度够用才关闭原半批并记录摘要。新确认固定为：

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.study run \
  --batch confirmation-arcane-resource-reset --arms DARCL2 DA2 \
  --start 62150600 --seeds 80 --workers 6 --interleave-arms
```

两版在同对手、种子、座位上相邻派发，并轮换谁先启动；各局仍使用独立 worker 和自己的指纹路径。选择及最终阶段的并发、交错模式也必须匹配冻结计划。资源未恢复时不执行上述命令。

已完成批次的全部翻转局可直接复读，先列原赢变输：

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.inspect_full_flips round4-hand-resource EHC
.venv/bin/python -m development.secret_hunter_astra_sprint.inspect_policy_flips --arm EHC
```

H2 模型训练数据只包括最初早期根及较晚训练根的世界 0/1，按来源种子五折划分；模型源码和冻结系数在 `candidates/PRR/`。已冻结的拟合结果见 `experiments/H2-fitted-ranker.json`。不要重拟合并覆盖同名候选，也不要把已开封标签重新称作留出。

只有实际完成选拔并产生 `final-freeze.json` 时，才使用以下双版本最终复跑入口。两池全部完成前不读结果；恢复只补原计划任务，不添加种子或候选：

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.reproduce_frozen \
  --source-run runs/astra-sprint-20261114 --verify-only
.venv/bin/python -m development.secret_hunter_astra_sprint.reproduce_frozen \
  --source-run runs/astra-sprint-20261114 --run runs/astra-sprint-replication
```

第二条命令创建全新账本并输出两池的完整复跑命令，绝不重开原账本。它校验原 ZIP、相对路径匹配的引擎资源、依赖、对手及冻结统计代码；复制原字节并登记新的精确解包路径。复跑同样种子是复现，不是新的独立验证。

若本轮按明确回退条款交付原 DARCL2，则只有 `delivery-freeze.json`，没有最终双版本样本；不要执行上述 `reproduce_frozen`，也不要据此补造最终区间。原字节验证和新目录解包使用：

```sh
.venv/bin/python -m development.secret_hunter_astra_sprint.verify_delivery \
  --source-run runs/astra-sprint-20261114 --extract runs/astra-fallback-exact-copy
.venv/bin/python -m development.secret_hunter_astra_sprint.verify_evidence \
  --source-run runs/astra-sprint-20261114
.venv/bin/python -m development.secret_hunter_astra_sprint.development_tables \
  --source-run runs/astra-sprint-20261114
```

`verify_delivery` 核对 ZIP、依赖、对手、341 个引擎资源、源码指纹和真实提交牌表入口；使用 `hs-arena validate --no-game` 避免默认随机对手超出允许名单。`verify_evidence` 重算已完成四轮的主指标区间，核对来源分区、全部 7,509 次战术续局的起始世界与归档执行源码，以及 50 次投影检查计费。它不运行新对局，也不读取未完成确认的胜负。

最终 `evidence.tar.gz` 解包后，以 `astra-sprint-evidence` 作为 `--source-run` 运行相同两项校验；此时还会逐文件检查证据索引和 SQLite 快照的 SHA-256。归档不包含完整模型会话或认证文件，Luna 中转证据为允许的脚本/MCP 调用、已发布状态、时间样本及原会话哈希。文件系统路径已在校验器中按归档相对位置解析。

需要重新实际跑协议时，使用新的输出目录，不重开已结束的研究账本。完成上面的原包解包后，下列命令复用已见验收种子；这是复现，不是新的独立验证。两条 Client 命令共六局，两条 Skill 命令共两个真实 Luna 座位：

```sh
.venv/bin/hs-arena play --p1 client:runs/astra-fallback-exact-copy/secret-hunter \
  --p2 greedy --games 3 --parallel 1 --seed 62550010 \
  --out runs/astra-replica-client-s1 --keep-decisions --max-turns 180 --timeout 180
.venv/bin/hs-arena play --p1 greedy \
  --p2 client:runs/astra-fallback-exact-copy/secret-hunter \
  --games 3 --parallel 1 --seed 62550010 \
  --out runs/astra-replica-client-s2 --keep-decisions --max-turns 180 --timeout 180
.venv/bin/hs-arena play --p1 skill:runs/astra-fallback-exact-copy/secret-hunter \
  --p2 greedy --games 1 --parallel 1 --seed 62550000 \
  --out runs/astra-replica-luna-s1 --keep-decisions --max-turns 180 --timeout 180
.venv/bin/hs-arena play --p1 greedy \
  --p2 skill:runs/astra-fallback-exact-copy/secret-hunter \
  --games 1 --parallel 1 --seed 62550001 \
  --out runs/astra-replica-luna-s2 --keep-decisions --max-turns 180 --timeout 180
```

真实 SkillSeat 需要本机课程 CLI 登录及可运行的原生模型客户端。本轮实际原生程序位置、哈希及命令记录在 `relay/*.request.json` 的本地日志中，最小可发布中转链在证据包的 `relay-proof/`；课程模型为 `gpt-6-luna`。ClientSeat 复现不需要模型登录。新复现对局不属于本轮已冻结的 5,969 次整局统计。

完整 CLI、注入故障、MCP 协议与真实 Luna 的计时分开。最终真实模型/ClientSeat 复跑使用 `final-acceptance-plan.json` 的预定种子，并继续记入辅助整局额度；策略选拔不使用这些胜负。正式 Slack 提交由用户完成。
