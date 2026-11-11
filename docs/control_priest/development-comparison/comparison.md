# Paired strategy comparison

Wilson intervals describe the sampled opponent mixture. Paired differences use
10,000 bootstrap draws of whole seed clusters (analysis RNG seed 598).
These exploratory intervals do not adjust for sequential selection or multiple comparisons.

| Arm | Wins | Rate | Wilson 95% | Mean turns | Mean hero damage | Policy errors |
|---|---:|---:|---|---:|---:|---:|
| Copy | 124/240 | 51.7% | 45.4%–57.9% | 22.18 | 23.47 | 0 |
| Policy | 133/240 | 55.4% | 49.1%–61.6% | 21.43 | 23.50 | 0 |
| Synergy | 178/240 | 74.2% | 68.3%–79.3% | 21.60 | 27.32 | 0 |
| Theft | 185/240 | 77.1% | 71.4%–81.9% | 21.76 | 27.31 | 0 |

| Difference | Paired games | Change | Cluster 95% | Gains / losses |
|---|---:|---:|---|---:|
| Policy − Copy | 240 | +3.8 pp | -2.5 to +10.0 pp | 31 / 22 |
| Synergy − Copy | 240 | +22.5 pp | +14.2 to +30.4 pp | 74 / 20 |
| Synergy − Policy | 240 | +18.8 pp | +9.6 to +28.3 pp | 75 / 30 |
| Theft − Copy | 240 | +25.4 pp | +16.7 to +33.8 pp | 83 / 22 |
| Theft − Policy | 240 | +21.7 pp | +12.9 to +30.4 pp | 75 / 23 |
| Theft − Synergy | 240 | +2.9 pp | -7.1 to +13.3 pp | 44 / 37 |
