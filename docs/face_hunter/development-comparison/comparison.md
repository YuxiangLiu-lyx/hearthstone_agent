# Paired strategy comparison

Wilson intervals describe the sampled opponent mixture. Paired differences use
10,000 bootstrap draws of whole seed clusters (analysis RNG seed 598).
These exploratory intervals do not adjust for sequential selection or multiple comparisons.

| Arm | Wins | Rate | Wilson 95% | Mean turns | Mean hero damage | Policy errors |
|---|---:|---:|---|---:|---:|---:|
| V0 | 115/200 | 57.5% | 50.6%–64.1% | 13.51 | 27.55 | 0 |
| V1 | 224/400 | 56.0% | 51.1%–60.8% | 13.47 | 26.89 | 0 |
| V2 | 115/200 | 57.5% | 50.6%–64.1% | 13.56 | 27.73 | 0 |
| V3 | 236/400 | 59.0% | 54.1%–63.7% | 13.68 | 27.61 | 0 |

| Difference | Paired games | Change | Cluster 95% | Gains / losses |
|---|---:|---:|---|---:|
| V1 − V0 | 200 | +1.0 pp | +0.0 to +2.5 pp | 2 / 0 |
| V2 − V0 | 200 | +0.0 pp | -3.5 to +3.5 pp | 8 / 8 |
| V2 − V1 | 200 | -1.0 pp | -4.0 to +2.0 pp | 7 / 9 |
| V3 − V0 | 200 | +3.0 pp | -2.0 to +8.0 pp | 16 / 10 |
| V3 − V1 | 400 | +3.0 pp | +0.0 to +6.0 pp | 30 / 18 |
| V3 − V2 | 200 | +3.0 pp | +0.0 to +6.0 pp | 9 / 3 |
