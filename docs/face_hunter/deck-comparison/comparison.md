# Paired strategy comparison

Wilson intervals describe the sampled opponent mixture. Paired differences use
10,000 bootstrap draws of whole seed clusters (analysis RNG seed 598).
These exploratory intervals do not adjust for sequential selection or multiple comparisons.

| Arm | Wins | Rate | Wilson 95% | Mean turns | Mean hero damage | Policy errors |
|---|---:|---:|---|---:|---:|---:|
| V3 | 236/400 | 59.0% | 54.1%–63.7% | 13.68 | 27.61 | 0 |
| V3Bluegill | 239/400 | 59.8% | 54.9%–64.4% | 13.68 | 28.05 | 0 |

| Difference | Paired games | Change | Cluster 95% | Gains / losses |
|---|---:|---:|---|---:|
| V3Bluegill − V3 | 400 | +0.8 pp | -3.8 to +5.2 pp | 39 / 36 |
