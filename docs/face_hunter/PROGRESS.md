# Face Hunter progress

All six milestones are complete. See [the final report](README.md) for evidence,
limits and reproduction commands.

- M0: official hs-arena 0.2.2 inspected; exact supplied 30-card deck validated.
- M1: deterministic baseline, phase handling and real MCP games completed.
- M2: bounded lethal search and all twelve requested combination tests passed.
- M3: next-turn estimates and all three risk modes implemented and tested.
- M4: 2,400 repaired model-free games completed with zero policy exceptions, illegal
  actions, timeouts or exits. The earlier 160 games with contained baseline exceptions
  are retained and rejected. V3 was selected before independent validation; the sole
  deck challenger was rejected for insufficient evidence.
- M5: 31 tests passed; V3 holdout 119/200; final MCP smoke 2/3; real Luna smoke 2/3,
  with all 77 actions exactly relayed and no fallback. Official static validation and
  extracted-ZIP setup passed. Python-only archive: 17,538 bytes compressed.

The bounded audit confirmed 17 missed-lethal turns in 200 baseline development games,
one in the corresponding V1 games, and detected zero in 400 V3 development plus 200
V3 holdout games. The remaining V1 case reached its production search deadline.
Zero detections do not establish exhaustive coverage.

V3's holdout win-rate interval is 52.6%–66.1%; its paired +3-point advantage over V0
has interval -2.0 to +7.5 points. Next-turn planning alone has no demonstrated average
benefit. Zoo remains the hardest local opponent (20/50). No Mystery/Astra validation
is claimed. No course upload was performed.

The repository is bound to `YuxiangLiu-lyx/hearthstone_agent`. All 45 original
Paladin/Zoo protected hashes remain identical. Hunter has a separate checkpoint,
champion pointer and release ZIP. The original fixed deck is retained.
