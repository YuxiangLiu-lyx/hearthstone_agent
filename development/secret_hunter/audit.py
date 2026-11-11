"""Read only recorded observations; separate protocol/model behavior from outcomes."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics
import shlex

from development.secret_hunter.bootstrap import ROOT,write


def readlines(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()] if path.exists() else []


def quantiles(xs):
    if not xs:return {'n':0}
    s=sorted(xs)
    return {'n':len(s),'mean':statistics.mean(s),'max':max(s),
            **{f'p{int(q*100)}':s[min(len(s)-1,math.ceil(q*len(s))-1)] for q in (.5,.95,.99)}}


def skill(game,seat):
    p=game/f'p{seat}';logs=readlines(p/'seat/scratch/decisions.jsonl')
    preparations=[r for r in logs if r['event']=='prepared']
    selections=[r for r in logs if r['event']=='model_selection']
    pre={r['seq']:r for r in preparations}
    sel={r['seq']:r for r in selections}
    calls=readlines(p/'seat/mcp_calls.jsonl');detail=[]
    for call in calls:
        if call['tool']!='act':continue
        seq=call['arguments']['seq'];a=call['arguments']['action'];state_path=p/'decisions'/f'{seq:05d}.state.json'
        s=json.loads(state_path.read_text());prepared=pre.get(seq);selection=sel.get(seq)
        default=prepared['candidates'][prepared['default_id']]['action'] if prepared else None
        detail.append({'game':game.name,'seq':seq,'phase':s['phase'],'action':a,'default':default,
                       'model_needed':prepared.get('model_needed') if prepared else None,
                       'selected':selection is not None,'selection':selection,
                       'different_from_default':default is not None and a!=default,
                       'outside_candidates':bool(prepared and a not in [c['action'] for c in prepared['candidates']]),
                       'validation_bypassed':bool(prepared and prepared['model_needed'] and not selection),
                       'missing_prepare':prepared is None,
                       'selection_mismatch':bool(selection and a!=selection['action']),
                       'elapsed_s':call['time']-(s['deadline_epoch_s']-s['timeout_s']),
                       'remaining_s':s['deadline_epoch_s']-call['time']})
    transcript=readlines(p/'seat/session_1.jsonl')
    commands=[e['item'] for e in transcript if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
    other_commands=[]
    for command in commands:
        raw=command.get('command','')
        try:
            outer=shlex.split(raw);inner=shlex.split(outer[outer.index('-c')+1]) if '-c' in outer else outer
            helper=len(inner)>=2 and inner[0].endswith('python') and inner[1]=='scripts/decide.py'
        except (ValueError,IndexError):helper=False
        if not helper:other_commands.append(raw)
    seatmeta=json.loads((p/'seat/seat.json').read_text()) if (p/'seat/seat.json').exists() else {}
    acted={r['seq'] for r in detail};unsubmitted=[]
    states=[json.loads(f.read_text()) for f in sorted((p/'decisions').glob('*.state.json'))]
    over=next((s for s in reversed(states) if s['phase']=='game_over'),None)
    for s in states:
        if s['phase']=='game_over' or s['seq'] in acted:continue
        end=(over['deadline_epoch_s']-over['timeout_s']) if over else None
        unsubmitted.append({'seq':s['seq'],'phase':s['phase'],'elapsed_to_game_end_s':None if end is None else end-(s['deadline_epoch_s']-s['timeout_s']),
                            'reason':(over.get('result') or {}).get('reason') if over else 'still_pending'})
    return {'decisions':detail,'tool_elapsed_s':[r['tool_elapsed_s'] for r in preparations],
            'rejected_events':dict(Counter(r['event'] for r in logs if r['event'].startswith('rejected_'))),
            'deep_requests':sum(r.get('deep',False) for r in preparations),'commands':len(commands),
            'other_commands':other_commands,
            'selection_requests':len(selections),
            'selection_status':dict(Counter(r['status'] for r in selections)),
            'tool_errors':dict(Counter(r['tool_error'] for r in preparations if r['tool_error'])),
            'has_client_mcp_env':any(r.get('has_client_mcp_env',False) for r in preparations),
            'mcp_calls':len(calls),'usage':seatmeta.get('usage',{}),'model':seatmeta.get('model_id'),
            'effort':seatmeta.get('effort'),'unsubmitted_decisions':unsubmitted}


def skill_report(folder):
    rows=readlines(folder/'results.jsonl')
    if rows:games=[(folder/'games'/r['game'],r['seat']) for r in rows]
    else:games=[(p,1) for p in folder.glob('g_*') if (p/'result.json').exists()]
    audits=[skill(p,i) for p,i in games];decisions=[d for a in audits for d in a['decisions']]
    unsubmitted=[d for a in audits for d in a['unsubmitted_decisions']]
    return {'games':len(games),'decisions':len(decisions),'model_choices':sum(d['selected'] for d in decisions),
            'phase_counts':dict(Counter(d['phase'] for d in decisions)),
            'latency_by_phase':{phase:quantiles([d['elapsed_s'] for d in decisions if d['phase']==phase]) for phase in sorted({d['phase'] for d in decisions})},
            **{key:sum(d[key] for d in decisions) for key in ('different_from_default','outside_candidates','validation_bypassed','missing_prepare','selection_mismatch')},
            'latency_publication_to_mcp_act':quantiles([d['elapsed_s'] for d in decisions]),
            'deck_submission_latency':quantiles([d['elapsed_s'] for d in decisions if d['phase']=='deck_submission']),
            'unsubmitted_decisions':unsubmitted,
            'all_decisions_elapsed_including_failures':quantiles([d['elapsed_s'] for d in decisions]+[d['elapsed_to_game_end_s'] for d in unsubmitted if d['elapsed_to_game_end_s'] is not None]),
            'tool_latency':quantiles([t for a in audits for t in a['tool_elapsed_s']]),
            'actual_tool_commands':sum(a['commands'] for a in audits),'mcp_calls':sum(a['mcp_calls'] for a in audits),
            'selection_requests':sum(a['selection_requests'] for a in audits),
            'other_commands':[c for a in audits for c in a['other_commands']],
            'deep_requests':sum(a['deep_requests'] for a in audits),'audits':audits,
            'note':'MCP act entry is a conservative approximation of submission time; no model cancellation claim.'}


def sample(folder):
    rows=readlines(folder/'results.jsonl');counts=Counter();samples=[];times=[]
    for row in rows:
        obs=readlines(folder/'games'/row['game']/f"p{row['seat']}"/'observations.jsonl')
        groups={}
        for z in obs:
            s=z['state'];info=z['info'];a=z['action'];times.append(z['elapsed_s'])
            if s['phase']!='main':continue
            counts['main']+=1;status=info['lethal']['status'];counts[status]+=1
            if status=='unsupported':groups.setdefault('unsupported',z)
            if not row['score'] and s['turn']>=5:groups.setdefault('early_loss_decision',z)
            if row['score'] and s['you']['hero']['health']<=10:groups.setdefault('close_win',z)
            if s['turn']>=9:groups.setdefault('ordinary_midgame',z)
            if a['type']=='attack' and a['attacker']==s['you']['hero']['entity_id'] and a['target']!=s['opponent']['hero']['entity_id']:
                target=next(m for m in s['opponent']['board'] if m['entity_id']==a['target'])
                remaining=sum(m['attack'] for m in s['opponent']['board'] if m['entity_id']!=a['target'])
                if s['you']['hero']['health']-target['attack']<=remaining+4:
                    counts['risky_hero_trade_signal']+=1;groups.setdefault('risky_hero_trade_signal',z)
            plans={c['plan'] for c in info['candidates']}
            if 'pressure' in plans and 'trade' in plans:groups.setdefault('plan_disagreement',z)
        for kind,z in groups.items():samples.append({'case_family':row['game'],'category':kind,'outcome':row['score'],
                                                   'opponent_for_development_only':row['opponent'],**z})
    return {'counts':dict(counts),'latency':quantiles(times),'cases':samples,
            'diagnostic_change':'Stratify whole-game observations by early loss, ordinary midgame, close win, plan disagreement, tool coverage and risky hero trade. Do not infer causality from terminal health.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('--mode',choices=['skill','sample'],required=True);p.add_argument('--out',required=True);a=p.parse_args()
    report=skill_report(Path(a.folder)) if a.mode=='skill' else sample(Path(a.folder));write(a.out,report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('audits','cases')}))


if __name__=='__main__':main()
