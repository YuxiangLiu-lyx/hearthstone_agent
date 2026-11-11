"""Produce a report from completed frozen runs; never changes policy or raw scores."""
from collections import Counter
import argparse
import json
from pathlib import Path
from development.secret_hunter.bootstrap import ROOT,write
from development.secret_hunter.audit import readlines,skill_report
from development.secret_hunter.compare import compare
from development.benchmarks.run import wilson


def outcome(rows):
    def metrics(rs):
        n=len(rs);w=sum(r['score'] for r in rs)
        forfeits=sum(r['result']['reason'].startswith('forfeit') and r['result'].get('winner')!=r['seat'] for r in rs)
        voids=sum(r['result']['reason'].startswith('void') or r['result']['reason']=='aborted' for r in rs)
        draws=sum(r['result'].get('winner') is None for r in rs)-voids
        return {'games':n,'wins':w,'ordinary_losses':n-w-forfeits-draws-voids,'draws':draws,'own_forfeits':forfeits,
                'engine_voids':voids,'win_rate':w/n if n else None,'wilson95_descriptive':wilson(w,n),
                'illegal_actions':sum(r['result']['illegal_counts'].get(str(r['seat']),0) for r in rs),
                'timeouts':sum(r['result']['timeouts'].get(str(r['seat']),0) for r in rs),
                'early_exits':sum(r['result']['reason']=='forfeit_exit' and r['result'].get('winner')!=r['seat'] for r in rs),
                'course_failures':sum(r.get('course_failure',False) for r in rs)}
    primary=[r for r in rows if r['opponent']!='official-mage']
    return {'all':metrics(rows),'primary':metrics(primary),'base':metrics([r for r in rows if r['opponent']=='official-mage']),
            'by_opponent':{name:metrics([r for r in rows if r['opponent']==name]) for name in sorted({r['opponent'] for r in rows})},
            'primary_by_actual_first':{label:metrics([r for r in primary if ('not_started' if r['first_player'] is None else 'first' if r['first_player']==r['seat'] else 'second')==label]) for label in ('first','second','not_started')},
            'by_seat':{str(i):metrics([r for r in primary if r['seat']==i]) for i in (1,2)}}


def model_metrics(audit):
    usage=Counter();status=Counter();errors=Counter();rejects=Counter();model_ids=set();efforts=set()
    for a in audit['audits']:
        usage.update(a['usage']);status.update(a['selection_status']);errors.update(a['tool_errors'])
        rejects.update(a['rejected_events'])
        model_ids.add(a['model']);efforts.add(a['effort'])
    return {**{k:v for k,v in audit.items() if k!='audits'},'usage_reported_by_host':dict(usage),
            'selection_status':dict(status),'tool_errors':dict(errors),'rejected_events':dict(rejects),'model_ids':list(model_ids),'effort':list(efforts),
            'api_request_count':None,'api_request_note':'Not exposed by official CLI event stream; tool commands and MCP calls are exact observed counts.',
            'cost_usd':None,'cost_note':'Existing account launcher; monetary cost/quota not exposed; no paid service provisioned.'}


def rate(m):
    if not m['games']:return 'unavailable'
    lo,hi=m['wilson95_descriptive'];return f"{m['wins']}/{m['games']} ({100*m['win_rate']:.1f}%; descriptive Wilson 95% {100*lo:.1f}–{100*hi:.1f}%)"


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',choices=['C4','C5'],default='C5');args=parser.parse_args()
    version=args.version;v=version.lower();suffix='-C4' if version=='C4' else ''
    names={'script_A':'secret-a0-python-confirmation' if version=='C4' else 'secret-a0-c5-python-confirmation',
           'script_C':f'secret-{v}-python-confirmation',
           'model_off':f'secret-{v}-ablation-confirmation','hybrid_C':f'secret-{v}-model-confirmation'}
    data={}
    for arm,name in names.items():
        p=ROOT/'experiments'/name
        assert (p/'summary.json').exists(),f'{name} is not finished'
        rows=readlines(p/'results.jsonl');data[arm]=outcome(rows)
        data[arm]['run']=str(p.relative_to(ROOT))
        if arm in ('model_off','hybrid_C'):
            a=skill_report(p);write(ROOT/f'docs/secret_hunter/{version}-{arm}-final-model-audit.json',a)
            data[arm]['model']=model_metrics(a)
    a=ROOT/'experiments'/names['model_off'];b=ROOT/'experiments'/names['hybrid_C']
    keys=lambda p:{(r['opponent'],r['seed'],r['seat']) for r in readlines(p/'results.jsonl')}
    matched=keys(a)==keys(b)
    paired=compare(a,b) if matched else {'unavailable':'External failures left unmatched partial schedules; no paired gain claimed.'}
    python_paired=compare(ROOT/'experiments'/names['script_A'],ROOT/'experiments'/names['script_C'])
    report={'status':'research-only','reason':'Official skill has no independent submission path for main-model stalls; actual workflow defects/forfeits are retained.',
            'population':'Frozen historical pool; Greedy separate; equal weights across 13 other opponents, seeds and seats.',
            'arms':data,'model_paired':paired,'python_paired':python_paired,'frozen_release':json.loads((ROOT/('dist/secret-hunter-c4-research.manifest.json' if version=='C4' else 'dist/secret-hunter-agent.manifest.json')).read_text()),
            'budget':json.loads((ROOT/'docs/secret_hunter/budget.json').read_text()),
            'limitations':[f"Only {2 if version=='C4' else 1} real-model seed clusters; Wilson intervals ignore clustering and are descriptive.",
                           'No evidence about Mystery Bot, Astra or classmates. No 90% guarantee.',
                           'Model API request count and monetary cost unavailable; host-reported tokens and actual tool calls recorded.',
                           'Tactical regression families are development evidence, not a broad held-out skill exam.']}
    write(ROOT/f'docs/secret_hunter/final-results{suffix}.json',report)
    lines=['# Fixed-deck Secret Hunter: final research report','','Status: **RESEARCH ONLY**. No formal submission or remote push was performed.',
           'The deck is unchanged. The official main model is Luna/medium. The official',
           'skill interface cannot guarantee a submission while the main model stalls.',
           'Observed workflow defects and forfeits are included below, not removed from scores.','',
           '## Frozen complete-game results','','Draws count as losses. Forfeits remain in denominators. Primary means the 13',
           'frozen non-base opponents; Greedy Mage is separate and never double-weighted.','',
           '| Arm | Transport | Greedy Mage | Primary pool |','|---|---|---|---|']
    for arm in names:
        d=data[arm];lines.append(f"| {arm} | {'actual Luna skill' if arm in ('model_off','hybrid_C') else 'Python, no model'} | {rate(d['base'])} | {rate(d['primary'])} |")
    lines+=['','Python results do not estimate the hybrid system. The real model-off arm uses',
            'identical C4 tools, deck and prompt, changing only model_authority to false.',
            'The comparison is intent-to-treat: any actual noncompliance remains measured.',
            'Off is a requested/configured authority restriction. The selector returns the default,',
            'but only Luna owns act, so this is not an enforceable removal of its ability to deviate.',
            'Any default disagreement in that arm contaminates a pure causal strategy ablation.',
            'The paired estimate concerns the complete configured systems, including compliance.','']
    pc=python_paired['primary'];plo,phi=pc['gain_seed_cluster_95']
    lines += [f"Primary Python C-minus-A gain: {100*pc['gain']:+.2f} percentage points;",
              f"20-seed-cluster bootstrap 95% interval [{100*plo:+.2f}, {100*phi:+.2f}].",
              'C4 and C5 use different confirmation seeds; their raw rates are not a paired version comparison.','']
    if matched:
        c=paired['primary'];interval=c['gain_seed_cluster_95']
        interval_text=(f"seed-cluster bootstrap interval [{100*interval[0]:+.2f}, {100*interval[1]:+.2f}]." if interval else 'No seed-cluster confidence interval is estimable from one cluster.')
        lines += [f"Primary hybrid-minus-off gain: {100*c['gain']:+.2f} percentage points;",
                  interval_text,
                  f"Only {c['seed_clusters']} seed clusters: this interval is unstable and does not establish a robust advantage.",'']
    lines+=['## Per-opponent real-model comparison','','| Opponent | Off wins/games | Hybrid wins/games | Hybrid forfeits |',
            '|---|---:|---:|---:|']
    for name,h in data['hybrid_C']['by_opponent'].items():
        off=data['model_off']['by_opponent'].get(name,{'wins':0,'games':0})
        lines.append(f"| {name} | {off['wins']}/{off['games']} | {h['wins']}/{h['games']} | {h['own_forfeits']} |")
    lines+=['','## Execution, model authority and latency','']
    for arm in ('model_off','hybrid_C'):
        d=data[arm];m=d['model'];t=m['latency_publication_to_mcp_act'];tool=m['tool_latency'];o=d['all']
        lines += [f"**{arm}:** {o['wins']} wins, {o['ordinary_losses']} ordinary losses, {o['draws']} draws, {o['own_forfeits']} own forfeits, {o['engine_voids']} engine voids.",
                  f"Illegal actions {o['illegal_actions']}; timeouts {o['timeouts']}; early exits {o['early_exits']}; course failures {o['course_failures']}.",
                  f"Structured selections {m['model_choices']}; actual default disagreements {m['different_from_default']}; validation bypasses {m['validation_bypassed']}; missing preparations {m['missing_prepare']}; changed validated actions {m['selection_mismatch']}.",
                  f"Publication-to-act seconds: P50 {t.get('p50',0):.3f}, P95 {t.get('p95',0):.3f}, P99 {t.get('p99',0):.3f}, max {t.get('max',0):.3f}; n={t['n']}.",
                  f"Worker calculation seconds: P50 {tool.get('p50',0):.4f}, P95 {tool.get('p95',0):.4f}, P99 {tool.get('p99',0):.4f}, max {tool.get('max',0):.4f}.",
                  f"Actual shell commands {m['actual_tool_commands']}; MCP calls {m['mcp_calls']}; deep requests {m['deep_requests']}; selection status {m['selection_status']}; worker errors {m['tool_errors']}; commands outside the helper {len(m['other_commands'])} (listed in JSON audit).",
                  f"Unsubmitted/failed decisions: `{json.dumps(m['unsubmitted_decisions'])}`; all-decision timing including those failures: `{json.dumps(m['all_decisions_elapsed_including_failures'])}`.",
                  f"Deck submission seconds: `{json.dumps(m['deck_submission_latency'])}`. Observed phases: `{json.dumps(m['phase_counts'],sort_keys=True)}`.",
                  f"Rejected stale/duplicate requests: `{json.dumps(m['rejected_events'])}`. Tool/late fallbacks: {sum(m['tool_errors'].values()) + m['selection_status'].get('late_default',0)} events across {m['decisions']} actions (counts may overlap).",
                  f"Reported token usage: `{json.dumps(m['usage_reported_by_host'],sort_keys=True)}`.",'',
                  '| Primary stratum | Wins / games | Descriptive interval |',
                  '|---|---:|---|']
        for label,metric in {**d['primary_by_actual_first'],**{'seat '+k:v for k,v in d['by_seat'].items()}}.items():
            if metric['games']:lines.append(f"| {label} | {metric['wins']}/{metric['games']} | {rate(metric)} |")
        lines.append('')
    lines+=['Model choices and disagreements demonstrate authority, not automatically contribution.',
            'Additional shell commands can be permitted reads of the own skill/playbook; their',
            'presence is not automatically an execution defect. Actual action deviations are separate.',
            'The paired outcomes measure the tradeoff. Exact model API request counts and dollar',
            'cost are not exposed by this local official CLI. No alternative model or paid service',
            'was used. Reported input tokens include repeated cached context and are not unique tokens.','',
            '## Actual strategic decisions','',
            'Examples are recorded choices, not causal explanations for the final game result.','',
            '| Game / seq | Default action | Actual action | Recorded model reason |',
            '|---|---|---|---|']
    examples=[]
    for audit in json.loads((ROOT/f'docs/secret_hunter/{version}-hybrid_C-final-model-audit.json').read_text())['audits']:
        for d in audit['decisions']:
            if d['different_from_default'] and d.get('selection') and not d['selection_mismatch']:
                examples.append(d)
                break
        if len(examples)==4:break
    for d in examples:
        reason=d['selection'].get('reason','').replace('|','/').replace('\n',' ')
        lines.append(f"| {d['game']} / {d['seq']} | `{json.dumps(d['default'])}` | `{json.dumps(d['action'])}` | {reason} |")
    lines += ['',
            '## Research evidence and limits','',
            'See [sources and knowledge ledger](SOURCES.md), [iteration decisions](ITERATIONS.md),',
            '[architecture](ARCHITECTURE.md), [timing contract](CONTRACT.md),',
            '[timing experiments](TIMING-EVIDENCE.md), [capability evidence](CAPABILITIES.md),',
            '[extracted mechanism/timing checks](checks-extracted.json), [actual-game tactical replays](replay-tactics.json),',
            '[budget](budget.json), [all-model usage](USAGE.md) and [resume instructions](RESUME.md).',
            'The supported solver recalled all 30 known-positive development variants in ten actual',
            'game families; 48 returned proofs were followed to real-engine wins. Random effect',
            'microfixtures are separately counted. Unsupported effects remain unknown. Public opponent',
            'tendencies are uncalibrated counts; no hidden-archetype accuracy claim is made.','',
            'Tool workers are killed/reaped on hard timeout. The 40-second adoption window rejects',
            'late suggestions only when the selector runs. Neither cancels main-model generation.',
            'Initial deck submission has no prestarted rescue controller. Normal observed latency',
            'does not prove unconditional compliance with the official 180-second deadline.','',
            'The broad 90% primary-pool goal is not established. Even a point estimate above 90%',
            'would require stronger independent statistical evidence. The conclusion applies only',
            'to this fixed historical pool, not unknown course opponents.','',
            '## Artifact','',
            '[Submission ZIP](../../dist/secret-hunter-agent.zip) is one valid root directory.',
            '[Manifest](../../dist/secret-hunter-agent.manifest.json) binds source, configuration,',
            'deck, extracted files and ZIP hashes. Frozen real-model confirmation runs use that',
            'extracted directory. The official hs-arena play CLI is separately exercised against',
            'Greedy on the extraction. Previous 205 protected files remain unchanged.',
            'Keep the script baseline and this research hybrid separately. Do not describe this',
            'package as safe for formal submission while the documented execution limits remain.']
    text='\n'.join(lines)+'\n'
    if version=='C5':text=text.replace('identical C4 tools','identical C5 tools')
    else:text=text.replace('../../dist/secret-hunter-agent.zip','../../dist/secret-hunter-c4-research.zip').replace('../../dist/secret-hunter-agent.manifest.json','../../dist/secret-hunter-c4-research.manifest.json')
    (ROOT/f'docs/secret_hunter/REPORT{suffix}.md').write_text(text)
    print(json.dumps({arm:d['primary'] for arm,d in data.items()}))


if __name__=='__main__':main()
