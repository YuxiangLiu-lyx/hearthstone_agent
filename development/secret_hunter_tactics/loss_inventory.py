"""Post-freeze loss audit; no candidate changes or new selection on final seeds."""
import copy,json,sys,collections
from development.secret_hunter_program.common import ROOT,write,readlines
from development.secret_hunter_tactics.accounting import record_cases
from hs_arena.engine import Engine
from hs_arena.deck import load_deck
src=ROOT/'development/secret_hunter_tactics/release/secret-hunter-program';sys.path.insert(0,str(src/'scripts'))
from lethal_planner import search,damage_upper_bound
from tactical_model import supported
from state_features import effective_health
from evaluator import threat
from development.secret_hunter_tactics.diagnose import label
folder=ROOT/'experiments/tactics-final-confirmation';rows=readlines(folder/'results.jsonl')
specs={x['name']:x for x in json.loads((ROOT/'docs/secret_hunter_program/opponent_manifest.json').read_text())['opponents']}
losses=[];probes=[];confirmed=[];charged=0
for row in [r for r in rows if not r['score']]:
    g=folder/'games'/row['game'];seat=row['seat'];obs=readlines(g/f'p{seat}/observations.jsonl');main=[z for z in obs if z['state']['phase']=='main']
    last=main[-1]['state'] if main else None
    losses.append({'game':row['game'],'opponent':row['opponent'],'turn':row['result'].get('turns'),
      'last_own_decision_turn':last['turn'] if last else None,'own_hp':last['you']['hero']['health'] if last else None,
      'enemy_hp':last['opponent']['hero']['health'] if last else None,
      'visible_incoming_before_taunts':threat(last['opponent']) if last else None,
      'unsupported_lethal_states':sum(not z['info'].get('lethal',{}).get('supported',False) for z in main),
      'bounded_lethal_states':sum(z['info'].get('lethal',{}).get('bounded_out',False) for z in main),
      'mulligan':next((z['action'] for z in obs if z['state']['phase']=='mulligan'),None),
      'policy_errors':[z['info']['error'] for z in obs if z['info'].get('error')]})
    chosen=[z for z in main if supported(z['state']) and effective_health(z['state']['opponent']['hero'])<=15
      and damage_upper_bound(z['state'])>=effective_health(z['state']['opponent']['hero'])
      and not z['info'].get('lethal',{}).get('guaranteed')][:2]
    for z in chosen:
        found=None
        for mode in ('base','proof'):
            result=search({**z['state'],'planning_mode':mode},budget_s=.4,max_nodes=8000,beam_width=64,max_depth=18);charged+=1
            probes.append({'game':row['game'],'seq':z['state']['seq'],'mode':mode,'found':result['guaranteed'],'nodes':result['nodes'],'bounded':result['bounded_out']})
            if result['guaranteed']:found=(mode,result);break
        if found is None:continue
        mode,result=found
        both={p:readlines(g/f'p{p}/observations.jsonl') for p in (1,2)};idx={1:0,2:0}
        own=load_deck(src/'deck.json');other=load_deck(ROOT/specs[row['opponent']]['deck']);e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'])
        while not e.over:
            who,_=e.pending();old=both[who][idx[who]]
            if who==seat and old['state']['seq']==z['state']['seq']:break
            assert e.step(who,old['action']).accepted;idx[who]+=1
        line=[];available=z['state'].get('hero_attack_available',z['state']['you']['hero'].get('can_attack',False))
        while not e.over and e.pending()[0]==seat and len(line)<20:
            s=e.view(seat);s.update(planning_mode=mode,hero_attack_available=available)
            r=search(s,budget_s=1,max_nodes=16000,beam_width=96,max_depth=20);charged+=1
            if not r['guaranteed']:break
            a=r['first_action'];line.append(label(s,a));assert e.step(seat,a).accepted
            if a.get('attacker')==s['you']['hero']['entity_id']:available=False
        confirmed.append({'game':row['game'],'opponent':row['opponent'],'seq':z['state']['seq'],'turn':z['state']['turn'],'mode':mode,
           'original_action':label(z['state'],z['action']),'original_info':z['info'],'state':z['state'],'line':line,
           'terminal':e.over,'winner':e.winner if e.over else None,'own_seat':seat,'counterfactual_win':e.over and e.winner==seat})
        charged+=1
        break
report={'losses':losses,'loss_count':len(losses),'primary_losses':sum(r['opponent']!='official-mage' for r in losses),
 'by_opponent':dict(collections.Counter(r['opponent'] for r in losses)),
 'deeper_probes':probes,'confirmed_counterfactuals':confirmed,'charged_short_cases':charged,
 'scope':'At most two early supported low-enemy-health states per lost final game. Deeper base and explicit extended-proof probes are offline diagnostics, not release behavior. Engine-confirmed terminal alternatives alone support local changed outcomes. Other losses remain unresolved; no model changes after final freeze.'}
record_cases('post-freeze loss inventory and deeper lethal probes',charged);write(ROOT/'docs/secret_hunter_tactics/final-loss-inventory.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in ('losses','deeper_probes','confirmed_counterfactuals')}))
print('probes',len(probes),'confirmed',len(confirmed),'terminal_wins',sum(c['counterfactual_win'] for c in confirmed))
for c in confirmed:print(c['game'],c['turn'],c['mode'],c['counterfactual_win'],c['line'])
