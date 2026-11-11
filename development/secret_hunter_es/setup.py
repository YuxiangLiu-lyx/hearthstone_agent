"""Start a separate, frozen-budget continuation of the F2 research round."""
import json, shutil
from pathlib import Path
from development.secret_hunter_program.common import ROOT, sha, write
from development.benchmarks.run import fingerprint

DOC=ROOT/'docs/secret_hunter_es'
DEV=ROOT/'development/secret_hunter_es'
assert not (DOC/'budget.json').exists()
write(DOC/'budget.json', {'started_utc':'2026-11-11T06:51:29+00:00',
 'deadline_utc':'2026-11-11T10:51:29+00:00',
 'limits':{'full_games':6000,'short_continuations':20000,'wall_seconds':14400},
 'reserved_final_games':2300,'runs':[],'short_continuations':[]})
write(DOC/'splits.json', {'screen':list(range(78100,78104)),
 'evolution':[list(range(78200+10*g,78204+10*g)) for g in range(3)],
 'validation':list(range(79000,79008)), 'confirmation':list(range(281000,281040)),
 'reproduction':list(range(281000,281002)),
 'historical':'All previous rounds, including F1/F2 holdouts, are development data.'})
protected={str(p.relative_to(ROOT)):sha(p) for folder in ['secret-hunter-program','secret-hunter-agent','development/checkpoints']
 for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'scratch' not in p.parts}
for name in ['SECRET_HUNTER_CHAMPION.json','dist/secret-hunter-program.zip','dist/secret-hunter-program.manifest.json']:
 protected[name]=sha(ROOT/name)
write(DOC/'freeze.json', {'baseline_tree':fingerprint(ROOT/'secret-hunter-program'),
 'deck_sha256':sha(ROOT/'secret-hunter-program/deck.json'),
 'opponent_manifest_sha256':sha(ROOT/'docs/secret_hunter_program/opponent_manifest.json'),
 'runtime_manifest_sha256':sha(ROOT/'docs/secret_hunter_program/runtime.json'),'protected':protected})
shutil.copy2(ROOT/'SECRET_HUNTER_CHAMPION.json',DOC/'previous-champion.json')
shutil.copytree(ROOT/'secret-hunter-program',DEV/'candidates/B0',ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
for module in ['run.py','accounting.py']:
 text=(ROOT/'development/secret_hunter_program'/module).read_text()
 text=text.replace('docs/secret_hunter_program/budget','docs/secret_hunter_es/budget')
 (DEV/module).write_text(text)
(DOC/'PLAN.md').write_text('''# F2 loss-driven evolutionary continuation

Started 2026-11-11 06:51:29 UTC; maximum 4 hours, 6,000 full games and
20,000 experimental short continuations. Frozen F2 is the same-deck baseline.
The previous 14 opponents, runtime, and 30-card deck remain unchanged.

Screen B0 and three hypotheses on 4 seeds each (448 games): exact public
effect coverage; interpretable state features; visible attack exposure.
Train a (mu=2, lambda=4) self-adaptive evolution strategy for 3 generations,
re-evaluating every parent and child on a fresh shared 4-seed block (2,016).
Validation uses 8 fresh seeds and at most 5 arms (1,120).
Freeze one candidate, then compare against F2 on 40 untouched seeds (2,240).
Reserve 56 reproduction games, 2 client games, and at most 2 relay smoke games.
Planned total 5,884, with 116 contingency games. Both seats, all 14 opponents.
Fitness and primary outcome exclude official Greedy, reported separately.

The 90% goal is aspirational. Promotion requires a positive primary paired
seed-bootstrap 95% interval, at least 1 percentage point point gain, zero own
illegal/timeout/forfeit, reliable CLI fallback, and observed decisions below 2 s.
If no candidate meets those gates, preserve F2. Do not cherry-pick holdouts.
Validation ties favor simpler modules, then the older candidate.

Paper adaptation: real-valued explanatory features, per-gene mutation scales,
parent re-evaluation, and elitist (mu+lambda) retention. Fixed opponents replace
the prohibited competitive coevolution. Use multiplicative log-normal sigma
adaptation with bounded scales; the HTML equation (9) prints an additive sigma
expression, so this is an explicit ES variant, not a literal paper replication.
No rarity score, external simulator source, runtime model, or private inputs.
''')
print('Frozen new round; prior champion preserved.')
