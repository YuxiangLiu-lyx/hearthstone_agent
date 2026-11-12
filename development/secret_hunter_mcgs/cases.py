"""Course-engine fixtures and submission-2 extraction; labels stay offline."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

from hs_arena.deck import load_deck, Deck
from hs_arena.engine import Engine
from hearthstone.enums import Zone

ROOT = Path(__file__).resolve().parents[2]
DECK = ROOT/'development/secret_hunter_dgm/candidates/Y1/deck.json'
DECK_SHA = '54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4'


def fixture(own=(), enemy=(), hand=(), mana=3, hp=30, enemy_hp=30,
            opponent_class='WARLOCK', opponent_hand=(), seed=71):
    assert hashlib.sha256(DECK.read_bytes()).hexdigest()==DECK_SHA
    d=load_deck(DECK)
    e=Engine(d, Deck(opponent_class, d.cards), seed)
    for i in (1,2):
        assert e.step(i, {'type':'mulligan','replace':[]}).accepted
    e.game.current_player=e.player(1);e.game.turn=2*mana-1
    p,q=e.player(1),e.player(2)
    for pl in (p,q):
        for c in list(pl.hand):c.zone=Zone.SETASIDE
        pl.max_mana=mana;pl.used_mana=0;pl.temp_mana=0
    p.hero.damage=p.hero.max_health-hp;q.hero.damage=q.hero.max_health-enemy_hp
    for cid in own:p.summon(cid).turns_in_play=1
    for cid in enemy:q.summon(cid).turns_in_play=1
    for cid in hand:p.give(cid)
    for cid in opponent_hand:q.give(cid)
    e._mark_seen();return e


def extract(archive, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    raw=Path(archive).read_bytes()
    with zipfile.ZipFile(archive) as z:
        data=json.loads(z.read('games.json'))
        (output/'official-results.md').write_bytes(z.read('results.md'))
    rows=[];games=[];replies=[]
    for g in data['games']:
        history=[];obs=g['observations'];student=g['student_seat']
        games.append({k:g.get(k) for k in ('game_id','opponent','student_seat','outcome','finish_reason')})
        for ix, row in enumerate(obs):
            s=row['state'];history.extend(s.get('events',[]))
            if s['phase'] not in ('main','choice'):continue
            record={'source_game':g['game_id'],'split':'development','deck_family':'C2',
                    'state':s,'history':list(history),'original_action':row['action'],
                    'audit':{'outcome':g['outcome'],'opponent':g['opponent']}}
            rows.append(record)
            if row['action'].get('type')=='end_turn':
                following=[]
                for later in obs[ix+1:]:
                    following.extend(later['state'].get('events',[]))
                    if later['state']['phase'] in ('main','choice','game_over'):break
                replies.append({'source_game':g['game_id'],'seq':s.get('seq'),
                                'state':s,'history':list(history),'public_response':following,
                                'audit':record['audit']})
    for name, rs in (('decisions',rows),('responses',replies)):
        (output/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rs))
    summary={'sha256':hashlib.sha256(raw).hexdigest(),'games':games,'decisions':len(rows),
             'responses':len(replies),'wins':sum(g['outcome']=='win' for g in games),
             'counts':dict(Counter((g['opponent']+':'+g['outcome']) for g in games)),
             'label_rule':'Future events/outcome are labels only; grouped by source game. Source seeds unavailable.',
             'deck':'C2 dual Arcane Shot; NEVER merged with original Krush deck win rates.'}
    (output/'manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary
