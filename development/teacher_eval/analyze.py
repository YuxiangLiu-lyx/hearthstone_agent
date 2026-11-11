"""Extract public evidence; never treat observed tokens or pooled copies as deck slots."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import json

from hs_arena.cards import load
from hs_arena.deck import validate_deck_data
from development.secret_hunter_program.common import ROOT, sha, write

RAW = ROOT / 'experiments/teacher-submission-1/raw'
OUT = ROOT / 'docs/teacher_eval'
DATA = ROOT / 'development/teacher_eval'


def extract(data):
    catalog = load()
    games = []
    groups = defaultdict(list)
    bounds = defaultdict(Counter)
    evidence = defaultdict(lambda: defaultdict(list))
    names = {}
    submitted = set()
    fixtures = []
    for game in data['games']:
        seat = game['student_seat']
        revealed = {}
        turns = {}
        enemy_attacks = Counter()
        event_keys = set()
        classes = set()
        for record in game['observations']:
            state, action = record['state'], record.get('action') or {}
            you, enemy = state.get('you'), state.get('opponent')
            if action.get('type') == 'submit_deck':
                submitted.add((action['hero_class'], tuple(sorted(action['cards']))))
            if enemy:
                classes.add(enemy['hero']['hero_class'])
            if state['phase'] == 'main':
                row = turns.setdefault(state['turn'], {'turn': state['turn'], 'plays': []})
                row.update(own_health=you['hero']['health'], enemy_health=enemy['hero']['health'],
                           own_board=len(you['board']), enemy_board=len(enemy['board']))
                if action.get('type') == 'play_card':
                    card = next(c for c in you['hand'] if c['entity_id'] == action['card'])
                    row['plays'].append(card['card_id'])
                if action.get('type') == 'end_turn':
                    row['end_seq'] = state['seq']
                    row['unspent_mana'] = you['mana']
            for event in state.get('events', []):
                # Events can be repeated in snapshots. Entity identity deduplicates card sightings.
                if event.get('player') == 3-seat and event['event'] in ('play_card', 'secret_revealed'):
                    cid = event.get('card_id')
                    if cid and cid != 'GAME_005' and cid in catalog:
                        eid = event.get('entity_id')
                        if eid is not None:
                            revealed[eid] = cid
                            names[cid] = catalog[cid]['name']
                        elif cid not in revealed.values():
                            # A revealed Secret has no entity id in this export: prove one copy only.
                            revealed['anonymous:'+cid] = cid
                            names[cid] = catalog[cid]['name']
                key = (state['turn'], json.dumps(event, sort_keys=True))
                if key in event_keys:
                    continue
                event_keys.add(key)
                if you and event.get('event') == 'attack' and event.get('player') == 3-seat:
                    target = event.get('target', {})
                    target_id = target.get('entity_id') if isinstance(target, dict) else target
                    enemy_attacks['face' if target_id == you['hero']['entity_id'] else 'minion'] += 1
        counts = Counter(revealed.values())
        group = game['opponent']
        for cid, count in counts.items():
            bounds[group][cid] = max(bounds[group][cid], count)
            evidence[group][cid].append({'game_id': game['game_id'], 'distinct_played_entities': count})
        row = {k: game[k] for k in ('game_id', 'opponent', 'student_seat', 'outcome',
                                    'finish_reason', 'student_forfeit', 'illegal_actions', 'timeouts')}
        row.update(opponent_classes=sorted(classes), revealed_copies=dict(counts),
                   turns=list(turns.values()), opponent_attack_targets=dict(enemy_attacks),
                   final_turn=game['observations'][-1]['state']['turn'])
        games.append(row)
        groups[group].append(row)
        if game['outcome'] == 'loss':
            main = [r for r in game['observations'] if r['state']['phase'] == 'main']
            for label, record in [('opening', main[0]), ('last_decision', main[-1])]:
                fixtures.append({'source_game': game['game_id'], 'label': label,
                                 'scope': 'Original WARLOCK observation; not a counterfactual Hunter game.',
                                 **record})
    assert len(submitted) == 1, 'Different submitted decks need separate analyses'
    hero, cards = next(iter(submitted))
    summary = {name: {'games': len(rows), 'wins': sum(r['outcome']=='win' for r in rows),
                     'losses': sum(r['outcome']=='loss' for r in rows),
                     'draws': sum(r['outcome']=='draw' for r in rows),
                     'forfeits': sum(r['student_forfeit'] for r in rows),
                     'illegal_actions': sum(r['illegal_actions'] for r in rows),
                     'timeouts': sum(r['timeouts'] for r in rows)} for name, rows in groups.items()}
    return {'metadata': {k:v for k,v in data.items() if k!='games'}, 'summary': summary,
            'submitted_deck': {'hero_class':hero,'cards':list(cards)}, 'games':games,
            'opponent_evidence': {name: {'minimum_observed_slots':sum(counts.values()),
                'cards':[{'card_id':cid,'name':names[cid],'observed_min_copies':n,
                          'evidence':evidence[name][cid]} for cid,n in sorted(counts.items())],
                'limitation':'Maximum within-game copy count, conditional on the same deck across games. Unseen slots and full deck identity are unknown.'}
                for name,counts in bounds.items()}}, fixtures


def build_population(report):
    decks = DATA / 'decks'
    decks.mkdir(exist_ok=True)
    known = {group: {r['card_id']:r['observed_min_copies'] for r in values['cards']}
             for group, values in report['opponent_evidence'].items()}
    astra = {cid:2 for cid in known['astra']}
    assert sum(astra.values()) == 30
    alternate = dict(astra)
    # Retain every revealed card and all demonstrated second copies.
    for cid in ('EX1_029','EX1_393','EX1_096','CS2_188'):
        assert known['astra'][cid] == 1
        alternate[cid] = 1
    alternate.update(EX1_556=2, EX1_067=2)
    hunter = {cid:2 for cid in known['bot2']}
    # Unobserved slots are an explicit hypothesis, never a recovered teacher list.
    for cid in ('CS2_188','DS1_184'):
        if sum(hunter.values()) < 30:
            hunter[cid] = min(2,30-sum(hunter.values()))
    definitions = [('astra-doubled', 'WARLOCK', astra, 'astra'),
                   ('astra-sticky', 'WARLOCK', alternate, 'astra'),
                   ('bot2-face', 'HUNTER', hunter, 'bot2')]
    hypotheses = []
    for name, hero, counts, group in definitions:
        deck = {'hero_class':hero,'cards':[cid for cid,n in sorted(counts.items()) for _ in range(n)]}
        assert not validate_deck_data(deck), validate_deck_data(deck)
        assert all(counts.get(cid,0)>=n for cid,n in known[group].items())
        write(decks/f'{name}.json',deck)
        hypotheses.append({'name':name,'observed_group':group,'assumed_counts':counts,
                           'deck':str((decks/f'{name}.json').relative_to(ROOT)),
                           'status':'plausible local proxy, NOT recovered official deck'})
    zoo = 'development/candidates/v7-zoo-strength'
    pop = [
        {'name':'astra-board-proxy','group':'astra','mode':'frozen','policy':zoo,'deck':hypotheses[0]['deck']},
        {'name':'astra-tempo-proxy','group':'astra','mode':'tempo','deck':hypotheses[0]['deck']},
        {'name':'astra-sticky-proxy','group':'astra','mode':'frozen','policy':zoo,'deck':hypotheses[1]['deck']},
        {'name':'bot2-face-proxy','group':'bot2','mode':'aggressive','deck':hypotheses[2]['deck']},
        {'name':'bot2-trade-proxy','group':'bot2','mode':'search','deck':hypotheses[2]['deck']},
        {'name':'bot1-mage-proxy','group':'bot1','mode':'official','deck':'hs-arena-0.2.2/decks/greedy_mage.json'}]
    write(DATA/'core.json',pop)
    write(OUT/'deck-hypotheses.json',hypotheses)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,default=RAW/'games.json')
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    report,fixtures=extract(json.loads(args.input.read_text()))
    report['source_sha256']=sha(args.input)
    write(OUT/'analysis.json',report)
    write(DATA/'submitted-warlock.json',report['submitted_deck'])
    write(OUT/'recorded-loss-fixtures.json',fixtures)
    build_population(report)
    write(RAW.parent/'manifest.json',{'files':{p.name:sha(p) for p in sorted(RAW.iterdir()) if p.is_file()},
          'original_paths':['games.json','results.md'],'submission_number':report['metadata']['submission_number'],
          'scope':'Teacher-returned submission-1 evidence; not Secret Hunter validation.'})
    print(json.dumps({'summary':report['summary'],'evidence':{g:v['minimum_observed_slots'] for g,v in report['opponent_evidence'].items()}},indent=2))


if __name__=='__main__':
    main()
