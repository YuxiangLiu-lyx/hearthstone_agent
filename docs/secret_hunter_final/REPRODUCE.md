# 复现与断点恢复

工作目录是 `/Users/liuyuxiang/developer/hearthstone-final-20261113`，分支 `research/secret-hunter-final-20261113`，起点为 `5c02d4870a86e2915095ec66d6afab60510afa50`。使用 `.venv/bin/python`（3.11，hs-arena 0.2.2），无需安装新依赖。原工作目录及两个用户 ZIP 保留。

## 检查交付

```sh
shasum -a 256 dist/secret-hunter-final-20261113.zip
.venv/bin/python -m development.secret_hunter_final.audit
.venv/bin/python -m development.secret_hunter_final.check_face_lethal
.venv/bin/python -m development.secret_hunter_final.study status
```

推荐包哈希、精确解包目录和选版门槛结果见 `docs/secret_hunter_final/recommendation.json`。只提交 `dist/secret-hunter-final-20261113.zip`；研究数据、报告及证据归档不属于 Skill ZIP。

课程校验：先把推荐包解到一个新临时目录，再运行 `.venv/bin/hs-arena validate --no-game <目录>/secret-hunter`。每个候选的实际 submit_deck 审计见 `deck-audit.json`，冻结包审计见运行目录 `release-candidates.json`。

## 已有账本恢复

主账本为 `runs/final-20261113/ledger.sqlite`（SQLite WAL），完整游戏日志在 `batches/<batch>/<arm>/games/`，续局在 `early-labels/`，来源在 `early-sources/`。每次启动先记 attempt，成功文件原子落盘，再更新完成状态。两个主动中断尝试计入预算，已完成文件不会重算。

同一完整游戏写者持 `writer.lock`，续局写者持 `cf-writer.lock`；不要并行启动两个同类型写者。正常中断可向主进程发送 SIGINT 或 SIGTERM，然后重跑原命令。失败、超时与中断记录保留；不要删除账本以掩盖失败。原六小时期限届满后应另建复现实验目录，不应改旧 manifest 延长预算。

## 从冻结代码重跑

以下命令适用于新目录。相同种子结果属于复现，不能再称为未见的独立验证。

```sh
export KRUSH_FINAL_RUN="$PWD/runs/final-reproduction"
.venv/bin/python -m development.secret_hunter_final.study init
.venv/bin/python -m development.secret_hunter_final.build
.venv/bin/python -m development.secret_hunter_final.audit
.venv/bin/python -m development.secret_hunter_final.study run --batch pilot1 --arms B M --start 41300000 --seeds 1 --workers 1
.venv/bin/python -m development.secret_hunter_final.study run --batch pilot2 --arms B M L ML --start 41300001 --seeds 1 --workers 2
.venv/bin/python - <<'PY'
import json
from development.secret_hunter_final.study import RUN
for seed in [21110024, 21110037]:
    keys = [[opponent, seed, seat] for opponent in ['bot2-face-proxy', 'bot2-trade-proxy'] for seat in [1, 2]]
    (RUN / f'historical-{seed}.json').write_text(json.dumps(keys))
PY
.venv/bin/python -m development.secret_hunter_final.study run --batch historical24 --arms B L --start 21110024 --seeds 1 --workers 3 --selection "$KRUSH_FINAL_RUN/historical-21110024.json"
.venv/bin/python -m development.secret_hunter_final.study run --batch historical37 --arms B L --start 21110037 --seeds 1 --workers 3 --selection "$KRUSH_FINAL_RUN/historical-21110037.json"
.venv/bin/python -m development.secret_hunter_final.reproduce
.venv/bin/python -m development.secret_hunter_final.study run --batch dev-core --arms B M L ML --start 41301000 --seeds 20 --workers 3 --warm
.venv/bin/python -m development.secret_hunter_final.study run --batch dev-guard --arms B M L ML --start 41302000 --seeds 4 --pool guardrail --workers 3 --warm
.venv/bin/python -m development.secret_hunter_final.select_mulligans
.venv/bin/python -m development.secret_hunter_final.continue_batches
```

continue_batches 依次完成 dev2-core（41303000 起 12 组）、dev2-guard（41304000 起 4 组）、conditional-core（41310000 起 240 组起手筛选）、conditional-guard（41311000 起 120 组起手筛选）。已有 done 任务跳过。条件化每臂实际 162、90 局；未命中起手不会被算作全池结果。

早期反事实：

```sh
.venv/bin/python -m development.secret_hunter_final.counterfactual mine --cap 144
.venv/bin/python -m development.secret_hunter_final.defense_sources
.venv/bin/python -m development.secret_hunter_final.counterfactual run --samples 3 --workers 2 --limit 4000
.venv/bin/python -m development.secret_hunter_final.counterfactual run --samples 3 --workers 2 --limit 4000 --scenario forced_coil
.venv/bin/python -m development.secret_hunter_final.learn
.venv/bin/python -m development.secret_hunter_final.label_audit
```

`defense_sources.py` 从 dev-core/B 的完整观察重建自然 Amani 覆盖清单，选出两个新增来源。已有清单时逐字段核对，不用胜负结果改变选择。`label_audit` 汇总早期及这两个晚期来源。全部来源路径与后续样本仍指向同一新账本目录。

最终必须在开发结束、唯一挑战者选定后按顺序运行。原研究选择见 `final-freeze.json`；下列 ML2 是原冻结挑战者，不是额外备选提交包。

```sh
.venv/bin/python -m development.secret_hunter_final.final_plan --core-seeds 100
.venv/bin/python -m development.secret_hunter_final.release prepare --challenger ML2
.venv/bin/python -m development.secret_hunter_final.study freeze --arms B ML2
.venv/bin/python -m development.secret_hunter_final.study run --batch final-core --arms B ML2 --start 41400000 --seeds 100 --workers 3 --final
.venv/bin/python -m development.secret_hunter_final.study run --batch final-guard --arms B ML2 --start 41500000 --seeds 8 --pool guardrail --workers 3 --final
.venv/bin/python -m development.secret_hunter_final.release recommend
.venv/bin/python -m development.secret_hunter_final.final_changes
```

最终不加 `--warm`。这两批实际使用 `frozen/<版本>/secret-hunter` 的精确 ZIP 解包目录。打开最终种子后，程序拒绝新的开发批次和候选调整。最终推荐根据预注册门槛可能回到 B，不强行晋级 ML2。

停掉所有重负载工作者后，以 recommendation.json 的 `final_exact_unpacked_path` 为参数：

```sh
.venv/bin/python -m development.secret_hunter_final.runtime --candidate <精确解包目录>
.venv/bin/python -m development.secret_hunter_final.mcp_audit --candidate <精确解包目录>
.venv/bin/python -m development.secret_hunter_final.delivery_audit
.venv/bin/python -m development.secret_hunter_final.report
.venv/bin/python -m development.secret_hunter_final.archive
```

runtime 包括真实入口的先后手换牌、Tracking choice、常规随机出牌、结束回合、注入故障回退、过期 seq 与 GAME OVER。mcp_audit 启动官方 no-model client，对固定三个种子各跑双方座位，核对所有原样 seq/action。它不能复现缺失的真实 Luna 测试。

## 三组动作证据

在原运行目录执行（先 `unset KRUSH_FINAL_RUN`）：

```sh
.venv/bin/python -m development.secret_hunter_final.replay --batch dev-core --arm B --opponent astra-sticky-proxy --seed 41301000 --seat 2
.venv/bin/python -m development.secret_hunter_final.replay --batch dev-core --arm M --opponent astra-sticky-proxy --seed 41301000 --seat 2
.venv/bin/python -m development.secret_hunter_final.reproduce
.venv/bin/python -m development.secret_hunter_final.replay --continuation runs/final-20261113/early-labels/41301009-astra-sticky-proxy-s2-q4-2-baseline.json
.venv/bin/python -m development.secret_hunter_final.replay --continuation runs/final-20261113/early-labels/41301009-astra-sticky-proxy-s2-q4-2-coin_bow.json
```

重放命令会增加辅助续局尝试计数，但不会改任何候选、种子或胜负标签。旧 C2 重建续局的六条逐动作复验记录已保存为 `legacy-evidence.json`；其来源是已见回放及旧原卡组局面，不是本轮独立来源。
