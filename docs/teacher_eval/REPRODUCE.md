# 老师评测驱动的奥秘猎测试复现

所有命令在仓库根目录执行，使用现有 `.venv` 和课程 `hs-arena 0.2.2`。
纯 Python 对局和 `client:` 测试不调用模型、不进行正式提交。

## 数据与布局

- 老师原文：`experiments/teacher-submission-1/raw/games.json`、`results.md`。
- 原文哈希：`experiments/teacher-submission-1/manifest.json`。
- 冠军入口：根目录 `SECRET_HUNTER_CHAMPION.json`，仍为 H7。
- 编辑器入口：根目录 `secret-hunter.code-workspace`。
- 核心对手：`development/teacher_eval/core.json`。
- 原对手池：`development/teacher_eval/guardrail.json`。
- D1：`development/teacher_eval/candidates/D1/`；打包文件：`dist/secret-hunter-teacher-d1.zip`。

重新提取报告与假设卡组（相同输入得到相同核心对手；有活动实验时不要修改输入）：

```sh
.venv/bin/python -m development.teacher_eval.analyze
.venv/bin/python -m unittest discover -s tests -p test_teacher_eval.py -v
```

每张已见卡的副本下界取同局不同实体数的最大值，不能跨局累加。
各卡组中的未知槽位是显式假设；不能用这些数据还原原始对手的私有手牌或牌序。

## 重新运行配对核心测试

输出目录必须尚不存在。以下复用已检查的种子，只用于复现，不能再当作新验证：

```sh
.venv/bin/python -m development.teacher_eval.run --candidate secret-hunter-program --out experiments/teacher-reproduce-h7 --start 910000 --seeds 40 --split confirmation
.venv/bin/python -m development.teacher_eval.run --candidate development/teacher_eval/candidates/D1 --out experiments/teacher-reproduce-d1 --start 910000 --seeds 40 --split confirmation
.venv/bin/python -m development.teacher_eval.compare experiments/teacher-reproduce-h7 experiments/teacher-reproduce-d1 --out docs/teacher_eval/reproduced-paired.json
```

默认每个对手、每个种子都测两个座位，4 个本地工作进程。每次调用只加载一种候选，
避免同名 Python 模块串到另一候选；对手加载器隔离自身模块。
程序只看公开 observation；随机 game_id 不包含对手名称或种子。

主指标对 Astra/bot2 两类等权，各类内部再对变体等权。置信区间按共享种子整簇重采样，
包括两个座位与所有对手；拒绝缺局、重复配对或不平衡种子设计。

## 旧对手池与失败复盘

```sh
.venv/bin/python -m development.teacher_eval.run --candidate secret-hunter-program --population development/teacher_eval/guardrail.json --out experiments/teacher-reproduce-h7-guard --start 911000 --seeds 10 --split guardrail
.venv/bin/python -m development.teacher_eval.run --candidate development/teacher_eval/candidates/D1 --population development/teacher_eval/guardrail.json --out experiments/teacher-reproduce-d1-guard --start 911000 --seeds 10 --split guardrail
.venv/bin/python -m development.teacher_eval.compare experiments/teacher-reproduce-h7-guard experiments/teacher-reproduce-d1-guard --out docs/teacher_eval/reproduced-guard.json
.venv/bin/python -m development.teacher_eval.diagnose experiments/teacher-reproduce-h7 experiments/teacher-reproduce-d1 --out docs/teacher_eval/reproduced-diagnostics.json
```

不要只汇报总体胜率。检查 Astra、抢血猎、法师、原对手池、实际先后手，以及两边的非法动作、
超时和执行错误。失败样本与完整动作记录在各实验的 `games/` 中，正常编辑器搜索隐藏这些大目录，
可直接打开报告中的路径。

## 引擎、ZIP 与客户端校验

```sh
.venv/bin/python -m development.teacher_eval.checks --candidate development/teacher_eval/release/secret-hunter-program --out docs/teacher_eval/reproduced-engine-checks.json
.venv/bin/hs-arena validate development/teacher_eval/release/secret-hunter-program --no-game
.venv/bin/hs-arena play --p1 client:development/teacher_eval/release/secret-hunter-program --p2 greedy --games 2 --parallel 1 --seed 912000 --out experiments/teacher-reproduce-client
```

已冻结的 D1 ZIP 由 `development.teacher_eval.build` 生成；构建器拒绝覆盖现有发布文件。
如需新发布，使用新的候选、文件名和冻结记录。已保存实验的最终审计/报告可重建：

```sh
.venv/bin/python -m development.teacher_eval.verify_release
.venv/bin/python -m development.teacher_eval.audit
.venv/bin/python -m development.teacher_eval.report
```

## 下一轮数据划分与门槛

本轮已使用：开发 86000–86007、86100–86111；D1 核心确认 910000–910039；
第一轮旧池 911000–911009；客户端 912000 起；D3 核心确认 920000–920039；
第二轮旧池 921000–921019。ZIP 复现只重用 910000–910001。
其他历史实验还使用了各自配置中的种子，选择新块前需一并检查。

D2/D3 复用了已经查看的 911000 旧池，属于自适应选择数据。它们的独立结果只来自之后的
920000/921000 块。不同种子块的 D1 与 D3 原始胜率不能直接比较，应各自减去同批 H7。

保留门槛记录在 `validation-plan.json`、`round2-plan.json`：核心两类等权提升至少 1 个百分点、
配对种子簇 95% 下界大于零；任一核心家族不退步超过 5 点；原池总退步不超过 3 点、单对手
不超过 10 点，并通过执行/打包校验。旧池点估计门槛是实用筛查，不是统计不劣效证明。

新回传应另建 submission 归档，保留原文与哈希。先更新可能卡组，再做开发筛选、冻结、
新种子确认和旧池检查。脚本不会自动替换默认冠军，也不会自动提交。
