"""Reconstruct two recorded matches exactly and export offline, player-view replays."""
import hashlib,json,math
from pathlib import Path
from hs_arena.deck import deck_from_ids
from hs_arena.engine import Engine

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'dist/replays/zoo-v7'
SOURCE=ROOT/'development/experiments/zoo-v7-holdout-strength'
CASES=[('victory','search-paladin-s100400-p2',2,'搜索圣骑士','海巨人施压，灵魂之火收尾'),
       ('defeat','adversarial-priest-v1-s100409-p1',1,'强控制牧师','连续清场与嘲讽，资源被耗尽')]
ZH={
 'Flame Imp':'烈焰小鬼','Voidwalker':'虚空行者','Argent Squire':'银色侍从','Abusive Sergeant':'叫嚣的中士',
 'Soulfire':'灵魂之火','Mortal Coil':'死亡缠绕','Dire Wolf Alpha':'恐狼前锋','Knife Juggler':'飞刀杂耍者',
 'Acidic Swamp Ooze':'酸性沼泽软泥怪','Harvest Golem':'麦田傀儡','Damaged Golem':'损坏的傀儡',
 'Shattered Sun Cleric':'破碎残阳祭司','Scarlet Crusader':'血色十字军战士','Dark Iron Dwarf':'黑铁矮人',
 'Defender of Argus':'阿古斯防御者','Argent Commander':'银色指挥官','Sea Giant':'海巨人',
 'The Coin':'幸运币',"Gul'dan":'古尔丹','Uther Lightbringer':'乌瑟尔·光明使者','Anduin Wrynn':'安度因·乌瑞恩',
 'Life Tap':'生命分流','Reinforce':'援军','Lesser Heal':'次级治疗术',"Sen'jin Shieldmasta":'森金持盾卫士',
 'Chillwind Yeti':'冰风雪人','Guardian of Kings':'列王守卫','Argent Protector':'银色保卫者','Faerie Dragon':'精灵龙',
 'Consecration':'奉献','Holy Nova':'神圣新星','Earthen Ring Farseer':'大地之环先知','Sunwalker':'烈日行者',
 'Cabal Shadow Priest':'秘教暗影祭司','Silver Hand Recruit':'白银之手新兵','Silver Hand Knight':'白银之手骑士',
 'Squire':'侍从','Aldor Peacekeeper':'奥尔多卫士','Blessing of Kings':'王者祝福','Truesilver Champion':'真银圣剑',
 'Boulderfist Ogre':'石拳食人魔','Temple Enforcer':'圣殿执行者',
}
def name(entity):
    n=entity.get('name','未知目标') if isinstance(entity,dict) else str(entity)
    return ZH.get(n,n)

def card(c):
    fields=('entity_id','card_id','name','type','cost','attack','health','max_health','armor','hero_class',
            'can_attack','frozen','immune','divine_shield','taunt','stealth','windfury','poisonous','deathrattle',
            'silenced','spell_damage','playable','durability','text')
    out={k:c[k] for k in fields if k in c};out['zh']=name(c)
    return out

def snapshot(engine,seat):
    s=engine.view(seat);out={'turn':s['turn'],'phase':s['phase'],'active':None if engine.over else engine.pending()[0]}
    for side in ('you','opponent'):
        p=s[side]
        v={'hero':card(p['hero']),'mana':p['mana'],'max_mana':p['max_mana'],'deck_remaining':p['deck_remaining'],
           'board':[card(c) for c in p['board']], 'hand_size':len(p['hand']) if side=='you' else p['hand_size'],
           'weapon':card(p['weapon']) if p.get('weapon') else None,
           'power':{'zh':name(p['hero_power']),'cost':p['hero_power']['cost'],'usable':p['hero_power']['usable']},
           'secrets':len(p.get('secrets',[])) if side=='you' else p.get('secrets_count',0)}
        if side=='you':v['hand']=[card(c) for c in p['hand']]
        out[side]=v
    return out

def action_label(a,view,actor,seat):
    who='我方' if actor==seat else '对手'
    entities={c['entity_id']:c for side in ('you','opponent') for c in view[side]['board']+[view[side]['hero']]}
    entities.update({c['entity_id']:c for c in view['you']['hand']})
    target=name(entities.get(a.get('target'),{}))
    if a['type']=='play_card':
        c=entities[a['card']]
        return f"{who}打出 {name(c)}"+(f' → {target}' if 'target' in a else ''),c['card_id'],a['card'],a.get('target')
    if a['type']=='attack':return f"{name(entities[a['attacker']])} → {target}",'',a['attacker'],a['target']
    if a['type']=='hero_power':return f"{who}使用 {name(view['you']['hero_power'])}"+(f' → {target}' if 'target' in a else ''),'',view['you']['hero']['entity_id'],a.get('target')
    if a['type']=='mulligan':return f"{who}替换 {len(a['replace'])} 张起手牌",'',None,None
    if a['type']=='end_turn':return f'{who}结束回合','',None,None
    return f'{who}完成选择','',None,None

def event_label(e,seat):
    who='我方' if e.get('player')==seat else '对手'
    kind=e['event']
    if kind=='damage':return f"{name(e)} 受到 {e['amount']} 点伤害"
    if kind=='heal':return f"{name(e)} 恢复 {e.get('amount',0)} 点生命"
    if kind=='death':return f"{who} {name(e)} 阵亡"
    if kind=='summon':return f"{who}召唤 {name(e)}"
    if kind=='draw':return f'{who}抽一张牌'
    if kind=='discard':return f'{who}弃掉一张牌'
    if kind=='game_over':return '对局结束：'+('动物园获胜' if e['winner']==seat else '动物园落败')
    if kind=='turn_start':return f"进入第 {math.ceil(e['turn']/2)} 轮 · {'我方' if e['player']==seat else '对手'}回合"
    return None

def build_case(slug,game_id,seat,opponent,subtitle):
    folder=SOURCE/game_id
    game=json.loads((folder/'game.json').read_text());result=json.loads((folder/'result.json').read_text())
    decks={p['index']:deck_from_ids(p['hero_class'],p['deck']) for p in game['players']}
    engine=Engine(decks[1],decks[2],game['seed'],max_turns=180)
    logs={i:[json.loads(l) for l in (folder/f'p{i}/observations.jsonl').read_text().splitlines()] for i in (1,2)}
    offsets={1:0,2:0};public=engine.take_public_events()
    frames=[{'index':0,'turn':0,'actor':None,'kind':'start','label':'起手准备 · 从动物园视角观看',
             'state':snapshot(engine,seat),'details':[],'source':None,'target':None,'card_id':'','note':'可以逐步查看每个动作，或点击播放。对手手牌只显示数量。'}]
    chapters=[{'frame':0,'title':'起手与展开'}]
    counters={'you':{'cards':0,'attacks':0,'taps':0},'opponent':{'cards':0,'attacks':0,'taps':0}}
    observed_fields=('phase','turn','you','opponent','legal_actions')
    while not engine.over:
        actor,_=engine.pending();row=logs[actor][offsets[actor]];offsets[actor]+=1
        view=engine.view(actor)
        for field in observed_fields:assert view[field]==row['state'][field],(game_id,row['state']['seq'],field)
        a=row['action'];label,cid,source,target=action_label(a,view,actor,seat)
        turn=view['turn'];accepted=engine.step(actor,a);assert accepted.accepted,(game_id,a,accepted)
        events=engine.take_public_events();public.extend(events)
        state=snapshot(engine,seat);index=len(frames)
        details=[event_label(e,seat) for e in events];details=[d for d in details if d]
        own_deaths=sum(e['event']=='death' and e.get('player')==seat for e in events)
        note=''
        if cid=='EX1_586':
            cost=next(c['cost'] for c in view['you']['hand'] if c['entity_id']==a['card'])
            note=f'海巨人以 {cost} 费登场，将铺场转化为大型威胁。';chapters.append({'frame':index,'title':f'{cost} 费海巨人'})
        if cid in ('CS1_112','CS2_093'):
            note=f"{name(next(c for c in view['you']['hand'] if c['entity_id']==a['card']))}结算；我方 {own_deaths} 个随从阵亡。"
            chapters.append({'frame':index,'title':'范围清场' if cid=='CS2_093' else '神圣新星'})
        if cid=='EX1_091':note='秘教暗影祭司夺取银色侍从；控制权改变会立即反映在场面中。';chapters.append({'frame':index,'title':'侍从被夺取'})
        if engine.over:note='；'.join(details)+'。'
        side='you' if actor==seat else 'opponent'
        counter={'play_card':'cards','attack':'attacks','hero_power':'taps'}.get(a['type'])
        if counter:counters[side][counter]+=1
        frames.append({'index':index,'turn':turn,'actor':actor,'kind':a['type'],'label':label,'state':state,
                       'details':details,'source':source,'target':target,'card_id':cid,'note':note})
    assert engine.winner==result['winner']
    assert offsets=={i:len(logs[i]) for i in (1,2)}
    original_public=[json.loads(l) for l in (folder/'replay.jsonl').read_text().splitlines()]
    assert public==original_public,(game_id,'public replay mismatch')
    last_turn_start=next(i for i,f in enumerate(frames) if f['turn']==result['turns'])
    chapters.append({'frame':last_turn_start,'title':'终局回合'});chapters.append({'frame':len(frames)-1,'title':'对局结果'})
    payload={'slug':slug,'title':'动物园 · '+('胜利回放' if slug=='victory' else '失败回放'),
      'subtitle':subtitle,'opponent':opponent,'seat':seat,'seed':game['seed'],'game_id':game_id,
      'first':result['first_player']==seat,'winner':result['winner'],'won':result['winner']==seat,'turns':result['turns'],
      'rounds':math.ceil(result['turns']/2),'policy':'Zoo v7 · 海巨人动物园','frames':frames,'chapters':chapters,'counters':counters,
      'replay_sha256':hashlib.sha256((folder/'replay.jsonl').read_bytes()).hexdigest(),
      'source_replay':str((folder/'replay.jsonl').relative_to(ROOT)),
      'validation':{'observations_checked':sum(offsets.values()),'public_events_matched':len(public),'terminal_winner_matched':True},
      'recap':(['第 7 轮：侍从先下，海巨人以 5 费登场。','第 9 轮：海巨人与指挥官压低血线，灵魂之火终结。'] if slug=='victory' else
               ['神圣新星与嘲讽随从限制前期进攻。','海巨人进入场面，但对手持续交换、治疗并夺取侍从。','第 9 轮再次神圣新星清场，雪人完成最后一击。'])}
    # The exported spectator state never includes the opponent's hidden hand.
    assert all('hand' not in f['state']['opponent'] for f in frames)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/f'{slug}.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    template=(ROOT/'development/visualizations/replay_template.html').read_text()
    embedded=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    (OUT/f'{slug}.html').write_text(template.replace('__TITLE__',payload['title']).replace('__DATA__',embedded))
    return {k:payload[k] for k in ('slug','title','seed','game_id','won','turns','rounds','validation','replay_sha256')}

def main():
    reports=[build_case(*case) for case in CASES]
    (OUT/'index.html').write_text((ROOT/'development/visualizations/index_template.html').read_text())
    (OUT/'verification.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(reports,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
