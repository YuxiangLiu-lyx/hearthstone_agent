# Paired strategy comparison

Wilson intervals describe the sampled opponent mixture. Paired differences use
10,000 bootstrap draws of whole seed clusters (analysis RNG seed 598).
These exploratory intervals do not adjust for sequential selection or multiple comparisons.

| Arm | Wins | Rate | Wilson 95% | Mean turns | Mean hero damage | Policy errors |
|---|---:|---:|---|---:|---:|---:|
| GenericTheft | 114/240 | 47.5% | 41.3%–53.8% | 22.46 | 20.77 | 0 |
| SpecialistTheft | 185/240 | 77.1% | 71.4%–81.9% | 21.76 | 27.31 | 0 |

| Difference | Paired games | Change | Cluster 95% | Gains / losses |
|---|---:|---:|---|---:|
| SpecialistTheft − GenericTheft | 240 | +29.6 pp | +19.6 to +40.0 pp | 81 / 10 |
