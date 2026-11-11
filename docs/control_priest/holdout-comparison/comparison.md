# Paired strategy comparison

Wilson intervals describe the sampled opponent mixture. Paired differences use
10,000 bootstrap draws of whole seed clusters (analysis RNG seed 598).
These exploratory intervals do not adjust for sequential selection or multiple comparisons.

| Arm | Wins | Rate | Wilson 95% | Mean turns | Mean hero damage | Policy errors |
|---|---:|---:|---|---:|---:|---:|
| Original | 157/300 | 52.3% | 46.7%–57.9% | 22.50 | 22.76 | 0 |
| GenericNewDeck | 159/300 | 53.0% | 47.3%–58.6% | 22.58 | 22.47 | 0 |
| ControlPriest | 231/300 | 77.0% | 71.9%–81.4% | 22.04 | 28.44 | 0 |

| Difference | Paired games | Change | Cluster 95% | Gains / losses |
|---|---:|---:|---|---:|
| GenericNewDeck − Original | 300 | +0.7 pp | -6.7 to +7.7 pp | 63 / 61 |
| ControlPriest − Original | 300 | +24.7 pp | +15.3 to +33.3 pp | 103 / 29 |
| ControlPriest − GenericNewDeck | 300 | +24.0 pp | +18.0 to +30.0 pp | 85 / 13 |
