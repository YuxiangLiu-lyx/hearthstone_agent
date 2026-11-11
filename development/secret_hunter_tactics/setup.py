"""New tactical research round, preserving all previous champions and evidence."""
import json,shutil
from pathlib import Path
from development.secret_hunter_program.common import ROOT,sha,write
from development.benchmarks.run import fingerprint
D=ROOT/'development/secret_hunter_tactics';O=ROOT/'docs/secret_hunter_tactics'
assert not (O/'budget.json').exists()
write(O/'budget.json',{'started_utc':'2026-11-11T07:55:08+00:00','deadline_utc':'2026-11-11T11:55:08+00:00',
 'limits':{'full_games':6000,'short_continuations':20000,'wall_seconds':14400},'reserved_final_games':2300,'runs':[],'short_continuations':[]})
write(O/'splits.json',{'development':list(range(82100,82106)),'tuning':list(range(82200,82206)),
 'validation':list(range(83000,83010)),'confirmation':list(range(291000,291040)),
 'historical':'All program and ES rounds, including their holdouts, are used development data.'})
protected={str(p.relative_to(ROOT)):sha(p) for root in ['secret-hunter-program','secret-hunter-agent'] for p in (ROOT/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'scratch' not in p.parts}
for p in ['SECRET_HUNTER_CHAMPION.json','dist/secret-hunter-program.zip','dist/secret-hunter-program.manifest.json']:protected[p]=sha(ROOT/p)
write(O/'freeze.json',{'baseline_sha256':fingerprint(ROOT/'secret-hunter-program'),'deck_sha256':sha(ROOT/'secret-hunter-program/deck.json'),
 'opponent_manifest_sha256':sha(ROOT/'docs/secret_hunter_program/opponent_manifest.json'),'protected':protected})
shutil.copy2(ROOT/'SECRET_HUNTER_CHAMPION.json',O/'previous-champion.json')
shutil.copytree(ROOT/'secret-hunter-program',D/'candidates/B0',ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
shutil.copytree(ROOT/'development/secret_hunter_es/candidates/D1',D/'working',ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
for name in ['run.py','accounting.py','runtime_checks.py','profile_components.py']:
 p=ROOT/'development/secret_hunter_es'/name;s=p.read_text().replace('secret_hunter_es/budget','secret_hunter_tactics/budget').replace('from development.secret_hunter_es.accounting','from development.secret_hunter_tactics.accounting')
 s=s.replace('development/secret_hunter_es/candidates/C3','development/secret_hunter_tactics/working').replace('docs/secret_hunter_es/runtime-checks-screen.json','docs/secret_hunter_tactics/runtime-checks.json')
 s=s.replace('development/secret_hunter_es/release/secret-hunter-program','development/secret_hunter_tactics/release/secret-hunter-program').replace('docs/secret_hunter_es/component-profile.json','docs/secret_hunter_tactics/component-profile.json')
 (D/name).write_text(s)
(O/'PLAN.md').write_text('''# Tactical Secret Hunter round

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
''')
print('Tactical round frozen.')
