"""Official-engine counterfactuals for public attack replies and tactical plans."""
import copy,json,time,unittest
from pathlib import Path
from development.secret_hunter_tactics import checks as c
from development.secret_hunter_program.common import ROOT,write
from tactical_model import prepare,transition
from public_response import prepare_reply,attack,attacks,worst_reply
from race_plan import value,hand_damage
from program_policy import decide
from tactics_rank import mulligan
from secret_policy import rank

BASE=json.loads((c.CANDIDATE/'config.json').read_text())
CFG={**BASE,'combat_guides':True,'race_plan':True,'public_response':True,'opening_plan':True}
EVIDENCE=[]

def projection(s):
    return [(k,s[k]['hero']['health'],s[k]['hero'].get('armor'),
             [(x['card_id'],x['attack'],x['health'],bool(x.get('divine_shield')),bool(x.get('taunt'))) for x in s[k]['board']],
             (s[k].get('weapon') or {}).get('durability')) for k in ('you','opponent')]+[
             [x['card_id'] for x in s['you'].get('secrets',[])]]

class Tactics(unittest.TestCase):
    def test_response_matches_engine(self):
        count=0
        for secrets in [[],['EX1_610'],['EX1_611'],['EX1_554'],['EX1_610','EX1_611'],['EX1_611','EX1_610'],['EX1_554','EX1_611'],['EX1_611','EX1_554']]:
            for own,enemy in [(['EX1_531','EX1_554t'],['CS2_172','CS2_200']),(['NEW1_032'],['EX1_008','CS2_179']),(['EX1_534'],['CS2_200']),(['EX1_531'],['EX1_029','EX1_531'])]:
                e,i=c.fixture(own=own,enemy=enemy,hand=secrets)
                e.player(i).summon('EX1_536')
                for cid in secrets:c.play(e,i,cid)
                s=prepare_reply(prepare(e.view(i)))
                e.step(i,{'type':'end_turn'})
                for a in attacks(s):
                    r=attack(s,a)
                    self.assertIsNotNone(r,(secrets,own,enemy,a))
                    branch=copy.deepcopy(e);self.assertTrue(branch.step(3-i,a).accepted)
                    self.assertEqual(projection(r),projection(branch.view(i)),(secrets,own,enemy,a))
                    count+=1
        EVIDENCE.append({'mechanism':'visible attack response with ordered Secrets','exact_engine_branches':count})

    def test_monotone_damage_and_hand_clock(self):
        e,i=c.fixture();s=prepare(e.view(i));values=[]
        for hp in range(15,0,-1):
            s['opponent']['hero']['health']=hp;values.append(value(s,CFG))
        self.assertTrue(all(b>a for a,b in zip(values,values[1:])),values)
        self.assertEqual(hand_damage((('EX1_539',3,False),),5,False,7),5)
        self.assertEqual(hand_damage((('EX1_539',3,False),),5,True,7),7)
        self.assertEqual(hand_damage((('EX1_531',2,True),('EX1_539',3,False)),5,False,7),5)
        self.assertEqual(hand_damage((('EX1_531',2,True),('EX1_539',3,False)),7,False,7),7)
        self.assertEqual(hand_damage((('EX1_539',3,False),('EX1_539',3,False)),8,True,7),12)
        EVIDENCE.append({'mechanism':'continuous face value and mana-constrained hand clock','values_hp_15_to_1':values})

    def test_hounds_hyena_lethal_real_engine(self):
        # Three 1/1 Taunts force Beast sacrifices; the ready Hyena must grow before attacking.
        e,i=c.fixture(own=['EX1_531'],enemy=['CS2_065']*3,hand=['EX1_538'],mana=3,enemy_hp=8)
        for m in e.player(3-i).field:m.damage=2
        actions=[]
        for _ in range(8):
            if e.over:break
            r=c.search(e.view(i),budget_s=.8,max_nodes=12000)
            self.assertTrue(r['guaranteed'],r);a=r['first_action'];actions.append(a)
            self.assertTrue(e.step(i,a).accepted)
        self.assertTrue(e.over);self.assertEqual(e.winner,i)
        EVIDENCE.append({'mechanism':'Hounds trades before grown Hyena attack','engine_winner':i,'actions':actions})

    def test_danger_response_and_trap_not_auto_clear(self):
        e,i=c.fixture(own=['EX1_531'],enemy=['CS2_172','CS2_172'],hand=['EX1_610'],hp=6)
        s=prepare(e.view(i));r=worst_reply(s,CFG,time.monotonic()+1,300)
        self.assertTrue(r['visible_lethal_found'])
        c.play(e,i,'EX1_610');s=prepare(e.view(i));r=worst_reply(s,CFG,time.monotonic()+1,300)
        self.assertFalse(r['visible_lethal_found'])
        self.assertEqual(len(s['opponent']['board']),2) # Deployment itself kills nothing.
        e,i=c.fixture(own=['NEW1_032'],enemy=['CS2_200','CS2_200'],hp=6)
        r=worst_reply(prepare(e.view(i)),CFG,time.monotonic()+1,300)
        self.assertTrue(r['visible_lethal_found']) # One attacker clears the Taunt, second hits face.
        EVIDENCE.append({'mechanism':'survival witness through Taunt; contingent Explosive protection','cases':3})

    def test_small_trade_protects_juggler(self):
        e,i=c.fixture(own=['EX1_554t','NEW1_019'],enemy=['CS2_200'],mana=2,hp=8)
        e.player(i).used_mana=2;e.player(3-i).field[0].damage=6
        actions=[]
        for _ in range(5):
            s=e.view(i);a,info=decide(s,CFG);actions.append(a)
            self.assertTrue(e.step(i,a).accepted)
            if a['type']=='end_turn':break
        self.assertFalse(e.player(3-i).field)
        self.assertEqual([m.id for m in e.player(i).field],['NEW1_019'])
        EVIDENCE.append({'mechanism':'1/1 Snake removes 6/1 Ogre and preserves Juggler','actions':actions})

    def test_safe_face_setup_and_immediate_lethal_priority(self):
        e,i=c.fixture(own=['EX1_531'],enemy=['CS2_172'],mana=2,hp=25,enemy_hp=3)
        e.player(i).used_mana=2
        s=e.view(i);a,info=decide(s,CFG)
        self.assertEqual(a,{'type':'attack','attacker':s['you']['board'][0]['entity_id'],'target':s['opponent']['hero']['entity_id']},info)
        e,i=c.fixture(own=['EX1_531'],enemy=['CS2_200'],mana=2,hp=6,enemy_hp=4)
        s=e.view(i);a,info=decide(s,CFG)
        self.assertEqual(info['reason'],'guaranteed_lethal')
        for _ in range(4):
            if e.over:break
            s=e.view(i);a,info=decide(s,CFG);self.assertTrue(e.step(i,a).accepted)
        self.assertTrue(e.over);self.assertEqual(e.winner,i)
        EVIDENCE.append({'mechanism':'safe face damage sets up next-turn power; current lethal outranks lethal incoming','engine_terminal_win':True})

    def test_coin_followup_guard(self):
        e,i=c.fixture(hand=['GAME_005','NEW1_019'],mana=1)
        s=e.view(i);a,info=decide(s,{**CFG,'coin_coverage_guard':True})
        self.assertEqual(a.get('card'),next(x['entity_id'] for x in s['you']['hand'] if x['card_id']=='GAME_005'),info)
        self.assertTrue(e.step(i,a).accepted)
        s=e.view(i);a,info=decide(s,{**CFG,'coin_coverage_guard':True})
        self.assertEqual(a.get('card'),next(x['entity_id'] for x in s['you']['hand'] if x['card_id']=='NEW1_019'),info)
        self.assertTrue(e.step(i,a).accepted)
        self.assertEqual([m.id for m in e.player(i).field],['NEW1_019'])
        EVIDENCE.append({'mechanism':'Coin -> newly affordable Juggler is not pruned by incomplete search','engine_board':['NEW1_019']})

    def test_combo_order_and_curve(self):
        e,i=c.fixture(enemy=['CS2_172']*3,hand=['NEW1_019','EX1_538'],mana=5)
        s=e.view(i);ranked=rank(s,CFG,time.monotonic()+1);a,info=decide(s,CFG)
        self.assertEqual(a.get('card'),next(x['entity_id'] for x in s['you']['hand'] if x['card_id']=='NEW1_019'),info)
        # Canonical opening fixture checks support, duplicates and expensive bricks.
        hand=[{'entity_id':n,'card_id':cid,'cost':cost,'type':kind} for n,(cid,cost,kind) in enumerate([
            ('EX1_080',1,'MINION'),('EX1_610',2,'SPELL'),('EX1_534',6,'MINION'),('EX1_543',9,'MINION')],1)]
        s['you']['hand']=hand;s['opponent']['hero']['hero_class']='WARLOCK'
        self.assertEqual(mulligan(s)['replace'],[3,4])
        EVIDENCE.append({'mechanism':'Juggler before Hounds; Keeper/Secret opening curve','action':a,'reason':info['reason']})

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tactics))
    out={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'fixtures':c.FIXTURES,'evidence':EVIDENCE}
    write(ROOT/'docs/secret_hunter_tactics/tactical-checks.json',out)
    from development.secret_hunter_tactics.accounting import record_cases
    record_cases('tactical checks',c.FIXTURES+sum(x.get('exact_engine_branches',0) for x in EVIDENCE))
    raise SystemExit(not result.wasSuccessful())
