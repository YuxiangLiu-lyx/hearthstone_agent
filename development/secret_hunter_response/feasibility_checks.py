"""Check the corrected conditional draw and public scenario feasibility boundaries."""
import copy,json
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_response.accounting import reserve,finish
from development.secret_hunter_tactics import checks as c
from hearthstone.enums import Zone
import tactical_model as m
from public_response import prepare_reply
import response_search as rs
reserve('response-feasibility',short=80,seconds=120);rows=[]
for size in (2,10):
 e,i=c.fixture(own=['EX1_029'],enemy=['CS2_172']);e.step(i,{'type':'end_turn'});o=e.player(3-i);o.max_mana=10;o.used_mana=0
 for x in list(o.hand):x.zone=Zone.GRAVEYARD
 o.give('EX1_302')
 for _ in range(size-1):o.give('CS2_172')
 s=m.prepare(e.view(i));s['_reply_mana']=10;target=s['you']['board'][0]['entity_id'];pred=rs.play_hypothesis(s,{'card_id':'EX1_302'},(target,0));card=next(x for x in e.view(3-i)['you']['hand'] if x['card_id']=='EX1_302');assert e.step(3-i,{'type':'play_card','card':card['entity_id'],'target':target}).accepted
 real=e.view(i);key=lambda s:(s['opponent']['hand_size'],s['opponent']['deck_remaining'],s['opponent']['hero']['health'],len(s['you']['board']))
 assert key(pred)==key(real),(key(pred),key(real));rows.append({'initial_hand':size,'equal':True,'projection':key(real)})
e,i=c.fixture(enemy=['CS2_172']);s=e.view(i);s['public_opponent_evidence']={'shown_cards':['CS2_188'],'shown_card_counts':{'CS2_188':2},'cheap_minions_played':2};s['opponent']['max_mana']=4
assert_no_duplicates=all(h['card_id']!='CS2_188' for h in rs.hypotheses(s))

assert assert_no_duplicates
s['opponent']['hand_size']=0;s['opponent']['deck_remaining']=0
assert not rs.hypotheses(s)
write(ROOT/c.ARGS.out,{'conditional_draw':rows,'seen_two_copies_excluded':True,'empty_hand_and_deck_no_hypotheses':True})
finish('response-feasibility',actual_short=4)
print('passed 4 feasibility checks')
