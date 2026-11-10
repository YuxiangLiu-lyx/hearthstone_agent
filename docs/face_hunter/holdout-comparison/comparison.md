# Paired strategy comparison

Wilson intervals describe the sampled opponent mixture. Paired differences use
10,000 bootstrap draws of whole seed clusters (analysis RNG seed 598).
These exploratory intervals do not adjust for sequential selection or multiple comparisons.

| Arm | Wins | Rate | Wilson 95% | Mean turns | Mean hero damage | Policy errors |
|---|---:|---:|---|---:|---:|---:|
| V0 | 113/200 | 56.5% | 49.6%–63.2% | 13.86 | 28.10 | 0 |
| V1 | 116/200 | 58.0% | 51.1%–64.6% | 13.62 | 27.82 | 0 |
| V2 | 115/200 | 57.5% | 50.6%–64.1% | 13.63 | 27.66 | 0 |
| V3 | 119/200 | 59.5% | 52.6%–66.1% | 13.76 | 28.07 | 0 |

| Difference | Paired games | Change | Cluster 95% | Gains / losses |
|---|---:|---:|---|---:|
| V1 − V0 | 200 | +1.5 pp | +0.0 to +3.0 pp | 3 / 0 |
| V2 − V0 | 200 | +1.0 pp | -2.5 to +4.5 pp | 8 / 6 |
| V2 − V1 | 200 | -0.5 pp | -4.0 to +3.0 pp | 5 / 6 |
| V3 − V0 | 200 | +3.0 pp | -2.0 to +7.5 pp | 14 / 8 |
| V3 − V1 | 200 | +1.5 pp | -3.5 to +6.0 pp | 11 / 8 |
| V3 − V2 | 200 | +2.0 pp | -1.0 to +5.0 pp | 6 / 2 |
