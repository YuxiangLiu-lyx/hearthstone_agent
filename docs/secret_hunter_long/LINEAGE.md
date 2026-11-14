# 候选谱系与实际验证

源码快照在创建后不改；状态决定另存，避免用后来的决定覆盖原始生成证据。
只更换deck.json属于牌表配置变化；改变Python文件属于源码变化。离线小规则参数搜索若未过门槛，没有生成候选，也没有改变线上策略。
完整有序30张、源码SHA-256、变动文件与时间在 `development/secret_hunter_long/lineage.json`；所有阶段决定在 `runs/long-20261114/decisions.json`。

| 候选 | 父代 | 创建代 | 改动类型 | 相对B换卡数 | 最新状态 |
| --- | --- | --- | --- | --- | --- |
| B | — | 0 | 原始基线 | 0 | baseline |
| DARC | B | 0 | 仅牌表配置 | 1 | advance_for_replication |
| DWOLF | B | 0 | 仅牌表配置 | 1 | retain_selection_option |
| TMILL | B | 1 | 源码改动 | 0 | archive |
| TRPLY | B | 1 | 源码改动 | 0 | archive_after_independent_replication |
| BL2 | B | 1 | 源码改动 | 0 | 已建快照，按批次验证 |
| KO | B | 2 | 仅牌表配置 | 1 | retain_selection_option |
| BM | B | 3 | 源码改动 | 0 | advance_natural_frequency |
| DARCM | DARC | 3 | 源码改动 | 1 | advance_natural_frequency |
| TRPLY2 | TRPLY | 2 | 源码改动 | 0 | archive_after_independent_replication |
| WOOZE | DWOLF | 4 | 仅牌表配置 | 2 | archive |
| BML2 | BM | 5 | 源码改动 | 0 | 已建快照，按批次验证 |
| DARCL2 | DARC | 5 | 源码改动 | 1 | 已建快照，按批次验证 |
| DARCML2 | DARCM | 5 | 源码改动 | 1 | 已建快照，按批次验证 |


## B

Exact requested ZIP, frozen reference

变动文件：无；精确指定ZIP基线。

源码SHA-256：`ad6194e2024f0375805be8a32c5f78230af7f8d3af06a161dd6748bd89e3abc9`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| pilot-cli | cli_development | 51400000–51400001 | 2 | done |
| deck-screen | development | 51401000–51401059 | 60 | done |
| mechanism-core | development | 51402000–51402019 | 20 | done |
| lethal-guard | development | 51403000–51403003 | 4 | done |
| coverage-core | development | 51404000–51404049 | 50 | done |
| recovery-fix | development | 51407000–51407019 | 20 | done |
| two-card | development | 51408000–51408029 | 30 | done |
| mulligan-combination | development | 51409000–51409029 | 30 | pending |


## DARC

Replace Krush slot with one Arcane Shot; unchanged mulligan and tactics

变动文件：`deck.json`

源码SHA-256：`b1228c5d81a97f94a50a7f33e3692512da3f77c2726bd40d6881c4b333f5d04c`。

决定：Single-card 60 groups primary +1.81pp, CI crosses zero; no final promotion

证据：`analysis/deck-screen-B-DARC-paired.json`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| pilot-cli | cli_development | 51400000–51400001 | 2 | done |
| deck-screen | development | 51401000–51401059 | 60 | done |
| coverage-core | development | 51404000–51404049 | 50 | done |
| mulligan-combination | development | 51409000–51409029 | 30 | pending |


## DWOLF

Replace Krush slot with second Dire Wolf; unchanged mulligan and tactics

变动文件：`deck.json`

源码SHA-256：`df95bb9b9eb927b396c97b832da3beb0a494d8cfc87e89ec47ea04775d2b5ff4`。

决定：Two independent cohorts90groups: primary+1.528pp CI[-0.556,3.704]; fresh30groups Bot2 -3.333pp flags instability. Keep as a pure-card option, no module transfer before independent selection.

证据：`analysis/combined-B-DWOLF.json`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| pilot-cli | cli_development | 51400000–51400001 | 2 | done |
| deck-screen | development | 51401000–51401059 | 60 | done |
| two-card | development | 51408000–51408029 | 30 | done |


## TMILL

2020 premade champion Miller GetMove branching depth allocation; same parent caps

变动文件：`scripts/turn_search.py`

源码SHA-256：`1e219bbc22be8925d8979a768383d1216f076dba690d70670fb6ac44616160d3`。

决定：Five actual game action divergences, zero terminal changes across240 paired games; no demonstrated terminal value

证据：`analysis/mechanism-core-B-TMILL-paired.json`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| mechanism-core | development | 51402000–51402019 | 20 | done |


## TRPLY

2018 premade champion PredatorMCTS response then known-hand recovery; same 48 nodes split 32/16 per endpoint

变动文件：`scripts/turn_search.py`, `scripts/champion_recovery.py`

源码SHA-256：`477c8b5c4899d32a1443ec3c2e937aa15a278de0391d9e705f4ae468f9f8c095`。

决定：Preregistered transfer gate fails: fresh20groups main gain -1.875pp,5rescues9regressions; no transfer or M/response combinations. Boundary fix creates legal extra recovery branches but no terminal improvement.

证据：`analysis/recovery-fix-B-TRPLY-paired.json`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| mechanism-core | development | 51402000–51402019 | 20 | done |
| recovery-fix | development | 51407000–51407019 | 20 | done |


## BL2

Standalone inherited narrow burn/power lethal coverage repair; original deck and mulligan

变动文件：`scripts/face_lethal.py`, `scripts/program_policy.py`

源码SHA-256：`74021ae82a78867b9eac465511a4a9907322e9e1b43a01aaf5d158174aedc2b9`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| mechanism-core | development | 51402000–51402019 | 20 | done |
| lethal-guard | development | 51403000–51403003 | 4 | done |
| mulligan-combination | development | 51409000–51409029 | 30 | pending |


## KO

Keep Krush, replace Misdirection with second Ooze: new B sample has 13 losses with received unplayed Misdirection, no Misdirection play before mana turn4; test early body, not proof of causality

变动文件：`deck.json`

源码SHA-256：`19a9129510b911a949956f16eb0e952b52bec559c61e59d4592e4c7c8200d0ee`。

决定：Fresh30groups primary+0.972pp with no observed family regression; combined50groups primary+1.167pp CI[-1.583,4.0]. Retains Krush; original strategy stays isolated.

证据：`analysis/combined-B-KO.json`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| mechanism-core | development | 51402000–51402019 | 20 | done |
| two-card | development | 51408000–51408029 | 30 | done |


## BM

Frozen trap-no-low opening rule replicated on wholly new matched source seeds after insufficient first holdout; not yet accepted

变动文件：`scripts/tactics_rank.py`

源码SHA-256：`60794f33424ecb0608930958b8838233f4d42b51cb34101708ae79f403833f9c`。

决定：Locked public opening rule: fresh144 openings48groups,36rescues8regressions;144/144 actualCLI match

证据：`mulligan-confirmation-B.json`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| mulligan-combination | development | 51409000–51409029 | 30 | pending |


## DARCM

Frozen trap-no-low opening rule replicated on wholly new matched source seeds after insufficient first holdout; not yet accepted

变动文件：`scripts/tactics_rank.py`

源码SHA-256：`06abd0846214232dcbf237774cc592dfbf77f749e56ce0e6326c80f474fbbc97`。

决定：Separate transfer check: fresh144 openings48groups,37rescues7regressions;144/144 actualCLI match

证据：`mulligan-confirmation-DARC.json`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| mulligan-combination | development | 51409000–51409029 | 30 | pending |


## TRPLY2

Actual-engine recovery boundary: refresh hero attack entitlement after spent previous attack, reset turn metadata; same32/16 budget; extra coverage counters only

变动文件：`scripts/turn_search.py`, `scripts/champion_recovery.py`

源码SHA-256：`f75e7f906890bf81094b579d64982b8c8120ac12f50eb469cf55765f5a1d76d1`。

决定：Preregistered transfer gate fails: fresh20groups main gain -1.875pp,5rescues9regressions; no transfer or M/response combinations. Boundary fix creates legal extra recovery branches but no terminal improvement.

证据：`analysis/recovery-fix-B-TRPLY2-paired.json`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| recovery-fix | development | 51407000–51407019 | 20 | done |


## WOOZE

Both single-card screens positive: Wolf improves early board and Ooze replaces uncast Misdirection; test interaction on new seeds against B and both single-card parents; no statistical promotion claimed

变动文件：`deck.json`

源码SHA-256：`6229797f9f0fc9aae1ac5f5b8b7868f6441c44641d210246a7e1d4e517d95c16`。

决定：Fresh30groups: total+8 wins but primary+0.833pp below KO parent; Bot2 -3.333pp exceeds stability preference. No module transfer or extra double-card combinations.

证据：`analysis/two-card-B-WOOZE-paired.json`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| two-card | development | 51408000–51408029 | 30 | done |


## BML2

Factorial isolation: confirmed public opening rule and/or narrow lethal coverage; full-game validation pending; no L2 exception for a combined patch

变动文件：`scripts/face_lethal.py`, `scripts/program_policy.py`

源码SHA-256：`daecd49ef40816722970e87313320abee5bb5c788423cf8297c30ab8f15cb18e`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| mulligan-combination | development | 51409000–51409029 | 30 | pending |


## DARCL2

Factorial isolation: confirmed public opening rule and/or narrow lethal coverage; full-game validation pending; no L2 exception for a combined patch

变动文件：`scripts/face_lethal.py`, `scripts/program_policy.py`

源码SHA-256：`e0cf461721004b82ab70cd128fbdd99ab2d59bb8e6c561d11449f8ea06d3b6c4`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| mulligan-combination | development | 51409000–51409029 | 30 | pending |


## DARCML2

Factorial isolation: confirmed public opening rule and/or narrow lethal coverage; full-game validation pending; no L2 exception for a combined patch

变动文件：`scripts/face_lethal.py`, `scripts/program_policy.py`

源码SHA-256：`5c8e85d78e15f85efcac9c0296d3a60ce96c7a3d1eb2ea6ac2c78338c57b85d3`。

| 实际登记批次 | 阶段 | 来源种子 | 组数 | 状态 |
| --- | --- | --- | --- | --- |
| mulligan-combination | development | 51409000–51409029 | 30 | pending |


## 未构建的学习提案

| 提案 | 原因 | 证据 |
| --- | --- | --- |
| BT1_proposal | Training-only develop at mana<3 rule net+7, heldout net-9; fixed-route label gate fails | `tactical-learning-deck-screen-B.json` |
| BT2_proposal | Balanced50source-group replication: training hold_coin unless public opponent class Hunter net+6, heldout360futures net-6 (2rescues8regressions). Teacher original-world net+3 on120roots, clusterCI crosses zero. Do not retune on this holdout. | `tactical-learning-coverage-core-B.json` |
| DARCT2_proposal | Training-only search334options: only unchanged parent passes training support/gain screen. Heldout unchanged274/360; teacher original-world86→88 net+2 CI[-3.333,5.833]pp. No deployed new tactical policy or extra natural-factorial games. | `tactical-learning-coverage-core-DARC.json` |

