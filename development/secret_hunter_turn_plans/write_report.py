"""Render the completed independent comparison without manually copying totals."""
import json
from development.secret_hunter_turn_plans.study import ROOT,RUN


def rate(value):return f'{value*100:.2f}%'


def score(row):return f"{row['wins']}/{row['n']} ({rate(row['win_rate'])})"


def interval(pair):
    low,high=pair['gain_seed_cluster_95']
    return f"{pair['gain']*100:+.2f} pp [{low*100:+.2f}, {high*100:+.2f}]"


def main():
    docs=ROOT/'docs/secret_hunter_turn_plans'
    final=json.loads((docs/'final-results.json').read_text())
    core=final['batches']['final-core'];guard=final['batches']['final-guard'];names=final['freeze']['arms']
    runtime=json.loads((docs/'runtime-E2-finish-minions.json').read_text())
    isolated=json.loads((docs/'runtime-E2-finish-minions-isolated.json').read_text())
    random=json.loads((docs/'runtime-juggler-hounds.json').read_text())
    data=json.loads((docs/'data-manifest.json').read_text())
    audits={b:json.loads((RUN/'batches'/b/'audit-engine-trap-v2.json').read_text()) for b in ('final-core','final-guard')}
    incremental=core['comparisons']['engine-trap-v2 -> E2-finish-minions']['primary']
    reliable=all(v['games'][k]==0 for v in final['combined_final_reliability'].values()
                 for k in ('illegal','timeouts','policy_errors','over_2s','harness_errors'))
    promoted=incremental['gain_seed_cluster_95'][0]>0 and reliable and guard['comparisons']['engine-trap-v2 -> E2-finish-minions']['all']['gain']>=0
    recommendation='Promote E2-finish-minions.' if promoted else 'Do not promote E2-finish-minions. Keep engine-trap-v2 as the next research parent and Y1 as the cumulative-gain control.'
    lines=['# Original Krush Secret Hunter: completed turn-plan iteration','',
        recommendation,'',
        'Every win rate in this report is against the existing frozen **local proxy opponents**. The main result is the independent frozen-code comparison below. Historical reproduction, adaptive development, selected conditional continuations, and post-freeze diagnostics are kept separate. A positive point estimate whose interval crosses zero is not described as a confirmed population gain.','',
        '## Independent final comparison','',
        'Final core seeds 31100000–31100039 and guard seeds 31200000–31200007 were reserved before development. After selecting E2, exact fingerprints were frozen before opening these seeds. All three arms use the same seeds, both seats, and unchanged opponent versions. Each arm completes 480 core plus 224 guard games; all 2,112 games use the complete Python CLI for every in-game atomic decision. Deck submission is separately checked through the actual CLI and course deck validator.','',
        '| Version | Astra | Bot2 | Greedy | Core total | Astra + Bot2 equal-family score |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for name in names:
        r=core['arms'][name];g=r['by_group'];macro=(g['astra']['win_rate']+g['bot2']['win_rate'])/2
        lines.append(f"| {name} | {score(g['astra'])} | {score(g['bot2'])} | {score(g['bot1'])} | {score(r['all'])} | {rate(macro)} |")
    lines+=['','Strict pairing uses `(opponent, seed, seat)`. The primary interval resamples all opponents and both seats together within each of 40 complete seed groups (10,000 bootstrap samples). Greedy is excluded from the primary score.','',
        '| Comparison | Primary gain, 95% seed-group interval | Astra gain, interval | Core gain, interval | Core flips / regressions |',
        '| --- | ---: | ---: | ---: | ---: |']
    for label,p in core['comparisons'].items():
        a=p['all'];lines.append(f"| {label} | {interval(p['primary'])} | {interval(p['astra'])} | {interval(a)} | {a['b_only_wins']} / {a['a_only_wins']} |")
    lines+=['','A zero-width bootstrap interval from identical observed outcomes does not establish policy equivalence, especially when the new action almost never triggers. Source selection and these fixed proxies limit generalization. No final outcome was used to change the candidate.','',
        '| Core opponent | Y1 | engine-trap-v2 | E2-finish-minions |','| --- | ---: | ---: | ---: |']
    for opponent in sorted(core['arms']['Y1']['by_opponent']):
        lines.append('| '+opponent+' | '+' | '.join(score(core['arms'][n]['by_opponent'][opponent]) for n in names)+' |')
    lines+=['','| Actual move order | Y1 | engine-trap-v2 | E2-finish-minions |','| --- | ---: | ---: | ---: |']
    for first,label in [('True','First'),('False','Second')]:
        lines.append('| '+label+' | '+' | '.join(score(core['arms'][n]['by_actual_first'][first]) for n in names)+' |')
    lines+=['','## Guardrail regression','',
        'The fourteen existing guard opponents use eight new complete seed groups, both seats. These seeds were also reserved before development. Small subgroup estimates are descriptive.','',
        '| Version | Guard total |','| --- | ---: |']
    for name in names:lines.append(f"| {name} | {score(guard['arms'][name]['all'])} |")
    for label,p in guard['comparisons'].items():
        a=p['all'];lines.append(f"\n- {label}: {interval(a)}; {a['b_only_wins']} flips, {a['a_only_wins']} regressions.")
    lines+=['','| Guard opponent | Y1 | engine-trap-v2 | E2-finish-minions |','| --- | ---: | ---: | ---: |']
    for opponent in sorted(guard['arms']['Y1']['by_opponent']):
        lines.append('| '+opponent+' | '+' | '.join(score(guard['arms'][n]['by_opponent'][opponent]) for n in names)+' |')
    lines+=['','## Action coverage and incremental effect','',
        '| E2 game-level stage | Core / 480 | Guard / 224 |','| --- | ---: | ---: |']
    for label,key in [('One of the three public contexts observed','hit'),('A deterministic continuation saved','plans_saved'),
                      ('A next action passed the state/legal checks','valid_continuation'),
                      ('A different legal continuation existed','different_legal_continuation'),
                      ('An action actually changed after the fresh-plan guard','changed')]:
        values=[audits[b]['arms']['E2-finish-minions']['game_funnel'].get(key,0) for b in ('final-core','final-guard')]
        lines.append(f'| {label} | {values[0]} | {values[1]} |')
    lines+=['','Context counts and continuation counts describe different entry conditions, so the context row is not a strict denominator for all cached plans. A different valid continuation can be rejected by E2 in favor of fresh replanning. Exact paired flips/regressions are reported above; cache hits by themselves are not improvements.','',
        '## Historical reproduction and development decisions','',
        'The supplied `hearthstone_astra_0066a30.zip` restored commit `0066a304931ae89415e6eff2a6735c2d6026b7d0`; every embedded checksum passed. Rebuilding engine-trap-v2 reproduces fingerprint `ad6194e2024f0375805be8a32c5f78230af7f8d3af06a161dd6748bd89e3abc9`. Reaggregation gives the reported Astra 176/240 versus 188/240, 19 flips and seven regressions; complete core 389/480 versus 406/480. A 24-game old-seed full-CLI audit matches every archived outcome. Three original public turns were replayed through the full CLI for restored and new versions.','',
        '| Completed development screen | Y1 | engine-trap-v2 | E2 | E3 broad continuation | E4 narrow trap continuation |',
        '| --- | ---: | ---: | ---: | ---: | ---: |',
        '| Eight seed groups, 96 games/arm | 93 | 91 | 91 | 87 | Not run |',
        '| Six new seed groups, 72 games/arm | 47 | 52 | 52 | Rejected | 52 |','',
        'E3 changed actions in 72/96 games and lost four parent wins without gaining any. E2 changed one game in the first screen and zero in the second; its outcomes matched its parent throughout both. E4 had one cache-hit game and zero action changes in its 72-game screen. E2 was selected as a narrow research challenger, not predeclared a winner.','',
        'Before the authentic archive arrived, independent R-series reconstructions were tested separately: one-seed pilot 10/12 each for Y1/R0/R1; four-seed screen Y1 43/48, R0 42/48, R1/R4 41/48. R2/R3 were built but not fully screened; R5/R6 screening was interrupted on recovery of the actual parent. These are not engine-trap-v2 results. All parent snapshots and rejected variants remain in `development/secret_hunter_turn_plans/lineage.json`.','',
        '## Complete-turn labels and learned rules','',
        'The corrected grouped sample contains 63 public source cases from original-deck proxy wins and losses. Source seed determines the split across arms, opponents, both seats, and related states. Four paired future samples per source compare the current turn with alternate full turns; validation uses disjoint source groups and future indices. Subsequent own turns use frozen Y1, and the opponent remains frozen. Legal reactive replanning follows observed random outcomes.','',
        '- Corrected main continuation batch: 1,960 terminal trajectories; 60 initial-hand-only forced-Coil hypotheses excluded. A later strict stress batch fixes empty-hand next-draw conditioning and excludes already-enraged Amani: 400 terminal trajectories, 60 explicitly inapplicable jobs.',
        '- Natural labels alone fit constants or one public-feature threshold, with a one-win complexity penalty and a minimum two-win training improvement. Keeper improved 27/44 to 29/44 on training groups but fell from 37/40 to 36/40 on held-out groups. It was rejected. Knife/Wolf and Amani fitting selected unchanged replanning.',
        '- The recovered Golem case adds 192 terminal continuations: verified Secretkeeper completion improves 28/48 to 34/48, with nine flips and three regressions. It is one source game, not 48 independent examples.',
        '- An explicitly post-freeze Amani diagnostic adds 720 terminal continuations. A cheap one-Hound trade preserves Highmane and gives 91/96 natural wins versus 90/96 (two flips, one regression), and 24/24 forced-Coil wins versus 12/24. The natural improvement is only one win in one known source game; it was not used to alter the final strategy. Bow gives 88/96 naturally despite strong forced defense.','',
        'A further 120 strict no-Coil response controls (including additional draws) preserve 22/24 wins for replan and cheap trading, versus 21/24 for Bow/Companion. The five corrected/diagnostic sets therefore contain 3,392 terminal trajectories. Preliminary runs and interrupted jobs remain separately named in the full archive and are excluded from these corrected totals. Eight complete stored-action replays reproduce every public state and terminal winner, including a positive Golem completion, a natural win harmed by a legal Bow route, and cheap prevention of the forced Amani lethal. Ten selected natural cases lost every tested route. See [CASE_STUDIES.md](CASE_STUDIES.md) for executed sequences, all three problem-specific tables, sampling caveats, and coverage gaps.','',
        'The observed bottleneck is primarily when to trust a generated full turn: legal deterministic commitment can override a better fresh decision. The famous missing follow-up is real but rare. The archived 96-game trap audit has only two targeted-deathrattle opportunities, both rejected by the old gate. The separate historical 144-game screen lacks per-decision logs in the supplied archive, so its zero-trigger claim is distinguished from the independently recounted 96-game funnel.','',
        'In the final core regression `(astra-sticky-proxy, 31100027, seat 1)`, E2 completes a Leper Gnome play after fresh replanning prefers end turn. The opponent uses Amani to kill it, enabling a 5/2 Amani. The existing public model predicts this visible trade exactly. The earlier search keeps only one endpoint per first action: its pre-response score prefers Gnome (-20.36 versus -22.56), but the response-adjusted score prefers stopping (-22.90 versus -24.04). Both plans begin with the same Wolf trade. This identifies loss of a useful endpoint before response evaluation, followed by harmful commitment, rather than a missing Enrage rule. No final seed was used to modify the candidate; see `final-core-action-changes.json`.','',
        '## Reliability and course compliance','',
        '| Version | Final games | Full CLI calls | P95 | P99 | Maximum | Illegal / timeout / fallback / over 2 s |',
        '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for name,r in final['combined_final_reliability'].items():
        g=r['games'];t=r['latency_s'];lines.append(f"| {name} | {g['n']} | {r['calls']} | {t['p95']:.3f} s | {t['p99']:.3f} s | {t['max']:.3f} s | {g['illegal']} / {g['timeouts']} / {g['fallbacks']} / {g['over_2s']} |")
    lines+=['',f"The E2 cold/concurrent/fault suite has {runtime['n']} calls, {runtime['invalid']} invalid outputs, and {runtime['over_2s']} calls over two seconds. Ordinary P99/max is {runtime['ordinary_latency_s']['max']:.3f} s; all fault-injected calls peak at {runtime['latency_s']['max']:.3f} s. There are {runtime['ordinary_fallbacks']} ordinary fallbacks and {runtime['injected_fault_fallbacks']} expected injected-failure fallbacks. A worker that publishes and then hangs returns its checked checkpoint. Eight stale-observation tests return refresh requests without submitting an old action.",
        '',f"After all heavy game workers stopped, the isolated stale-observation rerun completed {isolated['n']} calls with {isolated['invalid']} invalid outputs and {isolated['over_2s']} calls above two seconds (maximum {isolated['latency_s']['max']:.3f} s). Six additional Juggler/Hounds CLI calls all choose legal Hounds plays, with no fallbacks and maximum {random['latency_s']['max']:.3f} s.",
        '',
        'The deck is the exact ordered Y1 list, SHA-256 `54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4`, including Krush `EX1_543`, Misdirection `EX1_533`, and Ooze `EX1_066`. Six actual CLI deck submissions pass the course validator. Their intentional prepared-deck startup fallback flags are separate from in-game failure fallbacks. All 329 installed course Python files and all protected opponent/pool fingerprints remain unchanged.',
        '',
        'Five inherited mechanism tests pass: Wolf aura removal, Coil activating Amani, Krush attacking after a nine-mana Taunt clearance, secret order/Bow/Misdirection, and Juggler plus Hounds. Four Explosive Trap differential cases also match the original engine. Both frozen ZIPs pass course static validation after extraction and preserve the exact tested source fingerprints. They contain one skill folder, Python code and small text configuration only. No environment, binary, external model, hidden-information sampler, or research dataset is shipped. A live Luna relay match was not completed or counted; validation uses the complete Python CLI with local proxies.',
        '',
        '## Recommendation and next experiment','',recommendation,'',
        'Preserve face pressure as the default. First test retaining a few resource-distinct full-turn endpoints per first action, rather than discarding all but the highest pre-response score; keep the total response budget comparable. The next tactical hypothesis is a cheap exchange that removes just enough opposing attack to survive a possible Amani self-ping while retaining Highmane or burn. Count the next draw even when the opponent currently has zero cards. Collect more independent original-deck source games before fitting that condition; forced stress success alone is insufficient. For Knife/Wolf, collect genuinely resource-limited held-out cases and examples where removing Wolf unlocks profitable attacks. Broader forced commitment should remain rejected.',
        '',
        'Code, twelve immutable candidate snapshots, final freeze, exact deck audit, development lineage, aggregate data, raw local evidence archive, replay commands, latency/fault tests, and ZIP fingerprints are provided. See [REPRODUCE.md](REPRODUCE.md), [data-manifest.json](data-manifest.json), [final-results.json](final-results.json), and `dist/secret-hunter-turn-plans/manifest.json`. The research branch began at `c2bc11f0a88f2e20dcd951a056042bcb40426041`; implementation checkpoint `110c406` preserves the tested candidates. No submission or remote publication was performed.','']
    lines += [f"The study completes {final['budget']['completed_full_games']:,} full games across historical rechecks, development, partial superseded screens, and independent validation. There are {data['all_offline_attempt_count']:,} charged offline continuation attempts including rejected/superseded runs, under the recorded 6,000-attempt cap. Final core throughput is {final['throughput']['final-core']['games_per_minute']:.1f} games/minute and guard throughput {final['throughput']['final-guard']['games_per_minute']:.1f} games/minute at three workers. Final aggregation occurs {final['budget']['elapsed_wall_s']/3600:.2f} hours after the four-hour-budget study began. No training worker is intentionally left running after delivery.",'']
    (docs/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps({'report':str(docs/'REPORT.md'),'promoted':promoted,'recommendation':recommendation}))


if __name__=='__main__':main()
