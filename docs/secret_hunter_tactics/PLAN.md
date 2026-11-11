# Tactical Secret Hunter round

Started 2026-11-11 07:55:08 UTC, four-hour / 6,000 full-game / 20,000 short-case caps.
Preserve F2, the exact 30-card deck, installed engine, and the historical 14-opponent pool.
Program-only strategy; at most two final official host relay games. Old holdouts are development.

Hypotheses: (1) exact lethal/combo coverage with guards around unmodelled random continuations;
(2) next-turn hand damage, visible attack replies, protection and survival before static material;
(3) class-conditioned opening curve, Secret support, and Hounds retention against pressure classes.
Start with F2 and three candidates on six paired development seeds (672 games).
Use up to six compact parameter/config mutations on six different tuning seeds (1,008 games),
plus at most two diagnostic candidate screens (336). Independent validation uses at most five arms
on ten seeds (1,400). Freeze one finalist and compare to F2 on forty new seeds (2,240),
then reproduce fifty-six games and run two client and at most two relay smoke games.
Planned maximum 5,716 games; remaining budget is contingency. At least 2,300 final games reserved.

Primary outcome: equally weighted thirteen historical opponents, excluding separately reported
Greedy Mage. Promotion requires primary paired seed-bootstrap lower 95% bound >0 and >=1 pp
point improvement, no own illegal/timeout/forfeit/policy exceptions, measured CLI <2s,
and exact official relay if available. No promotion on development gains alone.
Forcing wins from a local board difference is prohibited: record terminal status and uncertainty.
