"""Report measured results; never promote a failed candidate or overwrite F2."""
import json,random,math
from datetime import datetime,timezone
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write,readlines
O=ROOT/'docs/secret_hunter_es'
read=lambda p:json.loads((ROOT/p).read_text())
pct=lambda x:f'{100*x:.2f}%'
interval=lambda xs:'–'.join(f'{100*x:.2f}' for x in xs)

def clustered(folder,group):
 rows=readlines(ROOT/folder/'results.jsonl')
 rows=[r for r in rows if group=='all' or (r['opponent']=='official-mage')==(group=='base')]
 seeds=sorted({r['seed'] for r in rows});means={s:sum(r['score'] for r in rows if r['seed']==s)/sum(r['seed']==s for r in rows) for s in seeds}
 rng=random.Random(911);xs=sorted(sum(means[rng.choice(seeds)] for _ in seeds)/len(seeds) for _ in range(5000))
 return [xs[125],xs[4874]]

def main():
 results=read('docs/secret_hunter_es/experiments.json');paired=read('docs/secret_hunter_es/final-paired.json')
 budget=read('docs/secret_hunter_es/budget.json');validation=read('docs/secret_hunter_es/validation.json');evolution=read('docs/secret_hunter_es/evolution.json')
 baseline=results['experiments/es-b0-confirmation'];final=results['experiments/es-final-confirmation']
 runtime=read('docs/secret_hunter_es/runtime-checks-final.json');relay=read('docs/secret_hunter_es/relay-audit.json');rep=read('docs/secret_hunter_es/reproduction.json');verify=read('docs/secret_hunter_es/verification.json')
 manifest=read('dist/secret-hunter-es.manifest.json');fixed=read('dist/secret-hunter-es-relay-fix.manifest.json')
 intervals={g:{'F2':clustered('experiments/es-b0-confirmation',g),'C2':clustered('experiments/es-final-confirmation',g)} for g in ['all','primary','base']}
 write(O/'single-version-clustered-intervals.json',intervals)
 primary=paired['primary'];gate=primary['gain']>=.01 and primary['gain_seed_cluster_95'][0]>0
 assert not gate, 'This report path intentionally preserves the existing champion; investigate changed input artifacts.'
 decision={'status':'retain_F2','candidate':'C2','candidate_promoted':False,'primary_paired':primary,
 'failed_gates':['No positive paired improvement; candidate point estimate regressed','One official host action lacked a preceding script call'],
 'champion_marker_unchanged':True,'strategy_changes_after_final_freeze':False,
 'relay_instruction_only_variant':'dist/secret-hunter-es-relay-fix.zip; host not retested due two-game cap',
 'budget':{k:budget[k] for k in ['full_games_completed','short_continuations_used','elapsed_wall_seconds']}}
 write(O/'decision.json',decision)
 lines=['# Secret Hunter loss-driven ES round', '',
 '**F2 remains the champion. The new C2 candidate was rejected. The 90% goal was not reached.**', '',
 f"On 40 fresh seed clusters (both seats), F2 won **867/1040 ({pct(867/1040)})** across the 13 primary opponents; C2 won **843/1040 ({pct(843/1040)})**. The paired difference is **−2.31 percentage points**, seed-cluster bootstrap 95% interval **−5.77 to +0.96**. This does not support promotion. The independent relay gate also failed once. The previous champion folder, ZIP and marker remain byte-identical.", '',
 '## Frozen confirmation', '',
 'The deck, installed hs_arena 0.2.2 runtime and 14-opponent manifest are unchanged. Greedy Mage is separate from the equally weighted 13-opponent primary pool. Every opponent has 80 games per arm. Shared seeds do not guarantee the same later random draws after actions diverge. These results do not estimate Mystery Bot, Astra or classmate performance.', '',
 '| Group | F2 W/N (rate; Wilson 95%) | C2 W/N (rate; Wilson 95%) | Paired difference pp (seed 95%) |',
 '|---|---:|---:|---:|']
 for g,label in [('primary','Primary 13, equal macro'),('base','Official Greedy Mage'),('all','All 14, equal macro')]:
  a,b=baseline['summary'][g],final['summary'][g];d=paired[g]
  lines.append(f"| {label} | {a['wins']}/{a['n']} ({pct(a['win_rate'])}; {interval(a['wilson95_descriptive'])}) | {b['wins']}/{b['n']} ({pct(b['win_rate'])}; {interval(b['wilson95_descriptive'])}) | {100*d['gain']:+.2f} ({interval(d['gain_seed_cluster_95'])}) |")
 lines+=['',f"Single-version seed-cluster 95% intervals for the primary macro are F2 **{interval(intervals['primary']['F2'])}%**, C2 **{interval(intervals['primary']['C2'])}%**. Wilson intervals above are descriptive and ignore within-seed dependence. Old F2 10-seed results are historical and are not pooled into this new test. No new point estimate or interval supports >90% primary performance.",'',
 '| Opponent | F2 wins / 80 | C2 wins / 80 | Difference pp |', '|---|---:|---:|---:|']
 for name,d in paired['by_opponent'].items():lines.append(f"| {name} | {d['a_wins']} ({pct(d['a_wins']/80)}) | {d['b_wins']} ({pct(d['b_wins']/80)}) | {100*d['gain']:+.2f} |")
 lines+=['','Per-opponent paired intervals and discordant counts are in `final-paired.json`; these exploratory subgroup comparisons are not multiplicity-adjusted. Zoo is the clearest regression (61 to 47 wins); search Paladin, tempo Paladin and control Mage also weaken. Gains on Shaman, Hunter and value Warlock do not offset those losses. Primary discordant pairs are 89 F2-only wins and 65 C2-only wins.', '',
 '## Implemented changes and paper adaptation', '',
 'Historical F2 losses exposed a missing Snake token in both exact projection and Beast identification. The latter undervalued Kill Command. C1 adds Snake coverage, exact Secret deployment/Secretkeeper growth, Houndmaster, Ooze, first-Juggler deployment and single-target Deadly Shot. C2 uses 21 interpretable end-turn coefficients. C3 adds a soft visible attack-exposure estimate. D1 isolates only the Snake correction. Unknown random triggers and hidden enemy Secrets remain excluded from exact proofs.', '',
 'The implemented ES uses two parents, four offspring, three generations, 21 normalized real-valued genes with separate evolving sigmas, plus categorical width/depth/node mutations. Each generation re-evaluates parents and offspring on a new shared seed block; elitist selection retains the best two. This follows the methodological ideas in [García-Sánchez et al.](https://arxiv.org/html/2410.19681v1), rather than claiming to reproduce its coevolution, decklists or competition result. We use bounded multiplicative log-normal sigma updates; this explicitly differs from the additive expression printed in equation 9 of the HTML. Fixed opponents replace prohibited self-play. See `SOURCES.md` and `evolution.json`.', '',
 '| Generation | Parent/offspring primary wins (each /104) | Retained |','|---|---|---|']
 for g in evolution['generations']:
  lines.append(f"| {g['index']} | "+', '.join(f"{f['name']}: {f['primary_wins']}" for f in g['fitness'])+' | '+', '.join(g['retained'])+' |')
 lines+=['','C2 survived unchanged in all three generations. E33 was the best evolved finalist in generation 3, but lost to the untrained C2 parent on independent validation. No gain is attributed to evolved weights. The training budget is much smaller than the paper’s 100-generation setting. Repeated development selection has substantial bias; final confirmation controls the promotion decision.', '',
 '## Initial paired screen\n\nAll five screen arms used the same four development seeds (104 primary and 8\nGreedy games per arm). F2/D1/C3 each won 92 primary games; C1/C2 each won 91.\nGreedy wins were 5 for F2/D1 and 6 for C1/C2/C3. No screen result established an\nimprovement. These tiny, repeatedly inspected blocks are selection data only.', '', '## Independent validation / ablation', '',
 '| Arm | Primary wins /208 | Greedy wins /16 | Interpretation |','|---|---:|---:|---|']
 labels={'B0':'Frozen F2','D1':'Snake-only correction','C1':'Broader exact coverage and Secret potential','C2':'Untrained 21-feature evaluator','E33':'Evolved feature/search parameters'}
 for a in validation['arms']:
  s=a['summary'];lines.append(f"| {a['candidate']} | {s['primary']['wins']} ({pct(s['primary']['win_rate'])}) | {s['base']['wins']} | {labels[a['candidate']]} |")
 lines+=['','C2 was selected before final seeds were opened. Its validation lead was only one game over C1/D1 and five over F2; the fresh confirmation did not replicate that apparent gain. D1 is not retroactively promoted after seeing C2 fail: it lacks its own fresh final confirmation.', '',
 '## Failure evidence and reliability', '',
 'Mechanism checks passed after the Snake fix: 13 test methods, 805/805 one-step comparisons from historical losses, plus 3 constructed real-engine lethal wins. The original failing Snake/Kill Command test is preserved. Offline diagnosis saved 34 early-divergence cases with 68 legal current-turn branches across the historical and final-regression audits. All endpoints are nonterminal; no counterfactual full-game win is claimed. `DIAGNOSTICS.md` records uncertainty and examples.', '',
 'The new static evaluation sometimes chooses two face damage instead of Explosive Trap against multiple fragile attackers. Expanded deterministic coverage also permits comparisons that omit random Juggler continuations. A better Secret/opponent-response model and safeguards around partially modelled combos are more promising next hypotheses than treating wider coverage as sufficient. Smaller/staged ES mutations and an independently confirmed minimal Snake fix remain untested follow-ups.', '',
 '| Measurement | F2 final | C2 final |','|---|---:|---:|']
 for metric,label in [('p50','Pure policy P50 ms'),('p95','Pure policy P95 ms'),('p99','Pure policy P99 ms'),('max','Pure policy maximum ms')]:
  lines.append(f"| {label} | {1000*baseline['latency_s'][metric]:.2f} | {1000*final['latency_s'][metric]:.2f} |")
 lines+=['',f"Across **{sum(x['latency_s']['n'] for x in results.values()):,}** Python decisions: **0 policy exceptions, 0 emergency fallbacks, 0 >2-second decisions**. All completed matches have zero own illegal actions, timeouts and forfeits. C2 node P95/P99/max: {final['nodes']['p95']}/{final['nodes']['p99']}/{final['nodes']['max']}. C2 exact-lethal coverage rejects {final['lethal_coverage_rejected']}/{final['main_decisions']} main states versus F2 {baseline['lethal_coverage_rejected']}/{baseline['main_decisions']}; broader coverage did not translate into higher win rate.", '',
 f"Supervised cold CLI P50/P95/P99/max: "+'/'.join(f"{1000*runtime['cold_latency_s'][str(q)]:.2f}" for q in [.5,.95,.99,1])+f" ms. Including forced hangs/crashes, maximum {runtime['all_latency_s']['1']:.3f} s, 0 over 2 s, 0 illegal fallback actions. Cold component costs are in `component-profile.json`. These are measured bounds, not a hard-real-time proof.", '',
 f"The exact research ZIP reproduced **{rep['same_outcomes']}/{rep['games']} outcomes and {rep['identical_action_traces']}/{rep['games']} action traces**. Two official client games passed with 73/73 exact actions. Two Luna-medium host games won, but **61/62** actual actions had matching script output: at game `386be7bf18554160`, seq 5, the host directly sent `end_turn` without running the script. Even though this was the only non-concede action, it violates the all-program relay requirement. This failure is retained, not counted as an exact-relay pass. Host game durations were 75.806 and 296.361 s; program latency is separate from host/tool latency.", '',
 'The separate relay-fix ZIP changes only `SKILL.md` to explicitly prohibit this shortcut. Source/config bytes are otherwise identical; two repeated official client games matched all 73 prior script actions. **The revised playbook has not been model-host retested**, because the two-game allowance is exhausted. Neither research ZIP is promoted. F2’s previous successful relay evidence is historical, not a guarantee against this newly observed host behavior.', '',
 '## Artifacts, budget and scope', '',
 f"Completed **{budget['full_games_completed']}/6000** full games: 5,992 pure Python, 4 official client, 2 official Luna relay. Charged **{budget['short_continuations_used']}/20000** short experimental cases, including conservative supplements; internal runtime search nodes are reported separately. Elapsed wall time at archival: {budget['elapsed_wall_seconds']/60:.1f} minutes (four-hour limit). The final pair plus reproduction used 2,296 games, exceeding the 25% reserve requirement. The remaining two games cannot support another balanced full-pool confirmation. No extra host smoke is allowed this round.", '',
 f"Verified {verify['protected_files_unchanged']} protected historical files, {verify['runtime_files_unchanged']} runtime files, 14 opponents, and {verify['public_observations_checked']:,} public policy inputs. The fixed deck SHA-256 is `{manifest['deck_sha256']}`. Research ZIP: `{manifest['zip']}`, {manifest['zip_bytes']:,} bytes compressed / {manifest['unpacked_bytes']:,} unpacked; SHA-256 `{manifest['zip_sha256']}`. Instruction-only revision: `{fixed['zip']}`, SHA-256 `{fixed['zip_sha256']}`. Both are below 10 MB and pass official static validation.", '',
 'Recommended artifact remains `dist/secret-hunter-program.zip` with the original `SECRET_HUNTER_CHAMPION.json`. Source/candidates, budget, hypotheses, hashes, splits and commands are archived alongside this report. See `REPRODUCE.md`. No formal submission, remote push, opponent modification, engine modification, cross-game policy memory or extra installed dependency was used.', '']
 p=baseline['summary']['base']['win_rate'];bonus=sum(math.comb(6,k)*p**k*(1-p)**(6-k)*(0 if k==0 else 1 if k<=2 else 2 if k<=4 else 3) for k in range(7))
 lines += [f"Using retained F2's new Greedy point estimate ({pct(p)}) in a simple independent six-game binomial approximation gives {bonus:.2f}/3 expected Bot-1 win-bonus points, or {5+bonus:.2f}/8 conditional on completing all six games. This noisy plug-in estimate is not an earned grade and ignores dependence. Mystery Bot, Astra and ladder scores remain unknown."]
 (O/'REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(decision))
if __name__=='__main__':main()
