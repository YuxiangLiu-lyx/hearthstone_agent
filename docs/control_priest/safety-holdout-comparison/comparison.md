# Paired strategy comparison

Wilson intervals describe the sampled opponent mixture. Paired differences use
10,000 bootstrap draws of whole seed clusters (analysis RNG seed 598).
These exploratory intervals do not adjust for sequential selection or multiple comparisons.

| Arm | Wins | Rate | Wilson 95% | Mean turns | Mean hero damage | Policy errors |
|---|---:|---:|---|---:|---:|---:|
| Original | 151/300 | 50.3% | 44.7%–56.0% | 21.79 | 21.97 | 0 |
| V1 | 231/300 | 77.0% | 71.9%–81.4% | 21.81 | 27.86 | 0 |
| V2 | 231/300 | 77.0% | 71.9%–81.4% | 21.82 | 27.87 | 0 |

| Difference | Paired games | Change | Cluster 95% | Gains / losses |
|---|---:|---:|---|---:|
| V1 − Original | 300 | +26.7 pp | +18.7 to +35.0 pp | 100 / 20 |
| V2 − Original | 300 | +26.7 pp | +18.7 to +35.0 pp | 100 / 20 |
| V2 − V1 | 300 | +0.0 pp | +0.0 to +0.0 pp | 0 / 0 |
