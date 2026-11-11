"""Write the final measured result, limitations and artifact decision."""
import json,math
from development.secret_hunter_program.common import ROOT,write
O=ROOT/'docs/secret_hunter_tactics'
read=lambda name:json.loads((ROOT/name).read_text())
pct=lambda x:f'{100*x:.2f}%'
interval=lambda x:' to '.join(f'{100*y:.2f}' for y in x)

def main():
    metrics=read('docs/secret_hunter_tactics/experiments.json');paired=read('docs/secret_hunter_tactics/final-paired.json')
    validation=read('docs/secret_hunter_tactics/validation.json');tuning=read('docs/secret_hunter_tactics/tuning.json')
    budget=read('docs/secret_hunter_tactics/budget.json');promote=read('docs/secret_hunter_tactics/promotion.json')
    runtime=read('docs/secret_hunter_tactics/runtime-checks-final.json');verify=read('docs/secret_hunter_tactics/verification.json')
    relay=read('docs/secret_hunter_tactics/relay-audit.json');client=read('docs/secret_hunter_tactics/client-audit.json')
    single=read('docs/secret_hunter_tactics/single-version-clustered-intervals.json');manifest=read('dist/secret-hunter-tactics.manifest.json')
    baseline=metrics['experiments/tactics-b0-confirmation'];final=metrics['experiments/tactics-final-confirmation']
    total_decisions=sum(x['latency_s']['n'] for x in metrics.values())
    decision={'status':'promote_H7' if promote['promoted'] else 'retain_F2','primary_paired':paired['primary'],
      'primary_single_version_seed95':single['primary']['H7'],'canonical_zip':'dist/secret-hunter-program.zip',
      'zip_sha256':manifest['zip_sha256'],'gates':promote['gates'],
      'official_host_completed':relay['games'],'official_host_attempts':relay['attempts'],
      'external_interruption':'Second host attempt has no completed result; 26 accepted actions and 27 act requests match the script.',
      'strategy_changes_after_holdout':False,'full_games_completed':budget['full_games_completed'],
      'full_attempts_charged':budget['full_game_attempts_charged'],'short_cases_charged':budget['short_continuations_used']}
    write(O/'decision.json',decision)
    lines=['# Secret Hunter tactical continuation', '',
      '**H7 is the new local program champion. The fixed-deck primary holdout reached 92.31%.**', '',
      'Across 40 previously unopened seed clusters and both seats, H7 won **960/1040 (92.31%)** against the 13 equally weighted primary opponents. Preserved F2 won **910/1040 (87.50%)**. The paired gain is **+4.81 percentage points**, with a seed-cluster bootstrap 95% interval of **+2.40 to +7.12**. No strategy or configuration changed after the final freeze.', '',
      'The primary H7 single-version seed-cluster interval is **90.19–94.33%**. Across all 14 opponents the point estimate is **1031/1120 (92.05%)**, but its seed-cluster interval is **89.73–94.20%**. Thus the primary fixed-pool estimate supports exceeding 90% at this interval level; the all-pool estimate is above 90% without that stronger lower-bound claim. Neither result promises 90% against every opponent, unseen classmates or hidden course bots.', '',
      'The official host scope is **one completed exact game**, plus one externally interrupted attempt. The completed game had 25/25 exact actions; the incomplete attempt had 26/26 exact accepted actions and 27/27 exact requests. It has no fabricated outcome and was not replaced with a third attempt. See `host-acceptance.md` and `host-interruption.json`.', '',
      '## Frozen final results', '',
      'The 30-card deck, course hs_arena 0.2.2 engine, 14-opponent manifest and opponent implementations are unchanged. Greedy Mage is reported separately. Each opponent has 80 games per arm. Shared seeds do not guarantee identical later draws after actions diverge. Wilson intervals are descriptive; paired and single-version seed-cluster intervals account for the matched seed grouping.', '',
      '| Group | F2 wins/rate (Wilson 95%) | H7 wins/rate (Wilson 95%) | Paired gain pp (seed 95%) |',
      '|---|---:|---:|---:|']
    for group,label in [('primary','Primary 13, equal macro'),('base','Official Greedy Mage'),('all','All 14, equal macro')]:
        a,b=baseline['summary'][group],final['summary'][group];d=paired[group]
        lines.append(f"| {label} | {a['wins']}/{a['n']} {pct(a['win_rate'])} ({interval(a['wilson95_descriptive'])}) | {b['wins']}/{b['n']} {pct(b['win_rate'])} ({interval(b['wilson95_descriptive'])}) | {100*d['gain']:+.2f} ({interval(d['gain_seed_cluster_95'])}) |")
    lines+=['','| Opponent | F2 wins /80 | H7 wins /80 | H7 rate | Gain pp |','|---|---:|---:|---:|---:|']
    for name,b in final['summary']['by_opponent'].items():
        a=baseline['summary']['by_opponent'][name]
        lines.append(f"| {name} | {a['wins']} | {b['wins']} | {pct(b['win_rate'])} | {100*(b['win_rate']-a['win_rate']):+.2f} |")
    lines+=['',f"There were {paired['primary']['b_only_wins']} H7-only wins and {paired['primary']['a_only_wins']} F2-only wins. Both actual first-player seats are represented. These new F2 results are not pooled with the previous round's 867/1040; the seed blocks differ.", '',
      '## What changed', '',
      '- Correct Snake Beast recognition in features and Kill Command ranking, plus explicit Hyena/Juggler/Hounds order, useful Beast sacrifices, protection trades and last-Beast preservation.',
      '- Continuous face value: the old 11-to-10-health transition could reduce the face score. Mana-constrained next-turn hand damage and a separate conditional surviving-board clock now guide safe closure.',
      '- Bounded visible attack responses for promising end states. Taunt removal, efficient enemy trades, ordered Explosive/Freezing/Snake triggers and Bow durability affect the comparison. Hidden hands and future draws are never exposed.',
      '- Class-prior opening curve and conditional Secret/Hounds retention; duplicates and expensive unsupported hands are discouraged.',
      '- Coverage guards preserve useful random follow-ups, including ranked Coin into Juggler. Actual random results always cause replanning.', '',
      'The policy still starts with an independent lethal search. Its entrypoint retains base effect coverage; Houndmaster and Secretkeeper buff lethals can instead be found by ordinary turn search with a terminal score. Two targeted official-engine fixtures confirm those release-policy wins, while `coverage-boundary.json` explicitly records that they are not independent proof-first coverage. Extending that entrypoint is a future hypothesis, not an untested post-holdout patch.', '',
      'See `STRATEGY.md` for the decision hierarchy and unsupported interactions. The sources are in `SOURCES.md`. Silverfish informs lethal-first search, end-state scoring and replies. The evolutionary paper informs empirical mutation, same-block parent re-evaluation and retention; its full algorithm, coevolution and published weights were not reproduced.', '',
      '## Iteration and ablation', '',
      '| Development arm | Primary wins /156 | Greedy wins /12 | Meaning |','|---|---:|---:|---|']
    labels={'b0':'Preserved F2','h1':'Snake/combo/protection and coverage changes','h2':'Add race/visible replies','h3':'Add opening plan','h4':'Reject unobserved thaw; fair response deadlines','h5':'Reply ablation, identical ordinary-effect coverage'}
    for n,label in labels.items():
        s=metrics[f'experiments/tactics-{n}-development']['summary']
        lines.append(f"| {n.upper()} | {s['primary']['wins']} | {s['base']['wins']} | {label} |")
    lines+=['','The initial 95.51% development result did not remain that high on the next block. The (1+5) interpretable mutation generation re-evaluated H4 and all five children on six fresh shared seeds:', '',
      '| Tuning arm | Primary wins /156 | Greedy wins /12 |','|---|---:|---:|']
    for r in tuning['fitness']:lines.append(f"| {r['name']} | {r['primary_wins']} | {r['base_wins']} |")
    lines+=['','T5 won this small tuning block, but did not beat its parent on independent validation. No improvement is attributed to the tuned weights.', '',
      '| Validation arm | Primary wins /260 | Greedy wins /20 |','|---|---:|---:|']
    for r in validation['arms']:lines.append(f"| {r['candidate']} | {r['summary']['primary']['wins']} | {r['summary']['base']['wins']} |")
    lines+=['','The matched response ablation improved 223/260 to 230/260 (+2.69 pp; seed 95% +0.38 to +5.00), with only ten seed clusters. The new opening plan was favorable in the initial H2/H3 screen, but has less independent evidence than the response module.', '',
      'After a recorded-loss replay exposed Coin into an unmodelled summon being pruned, an additional 280-game H7 validation arm was explicitly charged before holdout. H7 and H4 both won 230/260; one win changed in each direction. The predeclared tie rule preferred the guarded version. T5+guard prototype H6 was saved but never evaluated. These are adaptive selection data, not independent final evidence. `validation-amendment*.json` preserves the sequence.', '',
      '## Loss evidence and remaining weaknesses', '',
      'Twelve early decision divergences in new F2 losses were replayed through the current turn (24 branches). Four previous-round regressions were revisited with three forced root alternatives each (12 branches). All those endpoints were nonterminal; they do not prove changed full-match winners. Concrete cases include:', '',
      '- `12a99366782242d1`, turn 6: H7 plays Juggler before Leper. The legal continuation gets one knife damage that C2’s reversed order misses.',
      '- `268393d8aff7447c`, turn 4: H7 attacks with Juggler then deploys Explosive against two 3/2 attackers. C2 spends the mana on two immediate face damage and leaves the trap in hand.',
      '- `fc6bd930cf9548ab`, turn 5: H7 still takes the Bow/removal line rather than F2’s Explosive line. The different health/resource endpoints remain unresolved; this case is not claimed fixed.',
      '- `c1ddebf91ae24f98`, turn 2: the pre-guard version could end the turn instead of Coin into Juggler because ordinary search excluded the follow-up. H7’s guard and direct engine fixture address that coverage hole.', '',
      'The frozen final has 80 primary losses plus nine Greedy losses. Adversarial Priest (13), Zoo (11) and Search Paladin (9) remain the weakest primary matchups. A limited post-freeze audit made 94 deeper base/extended-proof probes on at most two early supported low-enemy-health states per lost game and found no terminal lethal alternative. This does not establish that all losses are unavoidable or that no lethal was missed. Unknown-card interactions, random summons, finite beam pruning, opponent spells/healing and trigger coverage remain important limits.', '',
      'The failure taxonomy explicitly separates simulation rules, missed lethal, avoidable death, trade/placement, Secret timing, resources, combos, mulligan, compute limits and draw/random variance. Only evidence-supported labels are assigned; unresolved losses are not automatically attributed to randomness. See `DIAGNOSTICS.md`, `losses.json`, `revisited-cases.json`, and `final-loss-inventory.json`.', '',
      '## Reliability and runtime', '',
      'Fourteen official-engine mechanism test methods and eight tactical methods passed. The tactical cases include Hounds clearing three Taunts before a grown ready Hyena kills the hero, a 1/1 Snake removing a 6/1 Ogre while preserving Juggler, safe face setup for next-turn power, immediate lethal despite lethal incoming, and Coin/Juggler order.', '',
      'The first historical response differential had 265/271 matches; the six mismatches concerned unobserved end-turn thaw. After conservatively rejecting that case, the supported differential matched **236/236** official-engine branches. Initial failures remain archived. Random Misdirection, Snake plus Juggler and uncertain full-hand Freezing interactions remain excluded from reply search.', '',
      '| Measurement | F2 final | H7 final |','|---|---:|---:|']
    for q in ('p50','p95','p99','max'):lines.append(f"| Pure policy {q} ms | {1000*baseline['latency_s'][q]:.3f} | {1000*final['latency_s'][q]:.3f} |")
    lines+=['',f"Across {total_decisions:,} pure-Python decisions: zero policy exceptions, emergency fallbacks or >2-second decisions. All completed Python/client/host games had zero own illegal moves, timeouts or forfeits. H7 final nodes P95/P99/max: {final['nodes']['p95']}/{final['nodes']['p99']}/{final['nodes']['max']}.", '',
      'Thirty cold supervised CLI cases measured P50/P95/P99/max '+ '/'.join(f"{1000*runtime['cold_latency_s'][str(q)]:.2f}" for q in (.5,.95,.99,1))+' ms. Including forced hangs/crashes and tiny budgets, maximum '+f"{runtime['all_latency_s']['1']:.3f} s; zero illegal actions or >2-second cases. These are measurements, not a hard-real-time guarantee.", '',
      f"The extracted ZIP reproduced 56/56 outcomes and 56/56 complete action traces on already used seeds. Two official client games won with {client['decisions']}/{client['decisions']} exact actions. One official Luna-medium host game won in 268.83 s with 25/25 exact actions. The second externally interrupted attempt contributes no complete-game outcome. Host model/tool latency is separate from program latency. The host uses a model; the policy never does.", '',
      '## Delivery and budget', '',
      f"Completed **{budget['full_games_completed']}/6000 full games**: 5,992 Python, two client and one official host. One externally interrupted host attempt remains charged, for **{budget['full_game_attempts_charged']} total attempt charges**. Charged **{budget['short_continuations_used']}/20000** short cases, including a conservative 1,000-case supplement for early failed fixtures/manual probes. Internal runtime search nodes are separate. Elapsed at archival: {budget['elapsed_wall_seconds']/60:.1f} minutes of the four-hour cap. The final pair plus reproduction used 2,296 games, above the 25% reserve.", '',
      f"Validated {verify['protected_files_unchanged']} protected historical files, {verify['runtime_files_unchanged']} installed runtime files, 14 opponents and {verify['public_observations_checked']:,} public policy inputs. No private hand, deck order, RNG, seed or hidden opponent identity enters runtime decisions.", '',
      '- Active source: `secret-hunter-program/`; canonical ZIP: `dist/secret-hunter-program.zip`.',
      '- Exact research ZIP: `dist/secret-hunter-tactics.zip`; the canonical ZIP is byte-identical.',
      '- Previous F2 source: `development/secret_hunter_tactics/previous-champion/secret-hunter-program/`; original ZIP: `dist/secret-hunter-program-f2.zip`; original marker: `previous-champion.json`.',
      '- Result and promotion: `SECRET_HUNTER_CHAMPION.json`, `decision.json`, `promotion.json` and `REPRODUCE.md`.', '',
      f"ZIP SHA-256: `{manifest['zip_sha256']}`; {manifest['zip_bytes']:,} bytes compressed / {manifest['unpacked_bytes']:,} unpacked. Deck SHA-256: `{manifest['deck_sha256']}`. Base commit: `6a7fc2475a17190268594ef2f5940b5b3a62f8f0`; frozen hashes identify uncommitted research files. No engine/opponent change, remote push, formal submission or new dependency/service was used.", '',
      'The large-workspace warning was addressed before promotion: `.vscode/settings.json` narrows analysis/watch/search scope, and `secret-hunter.code-workspace` opens only policy, current research, reports and releases. Raw traces retain their original paths. See `../WORKSPACE.md` and `../workspace-audit.json`; these editor changes did not alter the frozen package.', '']
    p=final['summary']['base']['win_rate'];bonus=sum(math.comb(6,k)*p**k*(1-p)**(6-k)*(0 if k==0 else 1 if k<=2 else 2 if k<=4 else 3) for k in range(7))
    lines.append(f"Under the audited course six-game Bot-1 bonus rule, plugging the Greedy estimate {pct(p)} into an independent binomial approximation gives {bonus:.2f}/3 expected win-bonus points ({5+bonus:.2f}/8 conditional on completing all six games). This noisy estimate is not an earned grade; hidden-bot and ladder scores remain unknown.")
    (O/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(decision))
if __name__=='__main__':main()
