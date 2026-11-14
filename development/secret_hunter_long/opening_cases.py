"""Exact action/turn/terminal replay of one opening rescue and one regression."""
import json
import time
from development.secret_hunter_long.study import RUN,HERE,ROOT
from development.secret_hunter_long.learn_mulligan import dataset
from development.secret_hunter_long.mulligan import setup
from development.secret_hunter_long.tactical import visible
from development.secret_hunter_long.write_cases import action,board
from development.secret_hunter_mcgs import train

def main():
    m=json.loads((RUN/'mulligan-sources/manifest-B-51421000.json').read_text())
    rows=dataset(m,'train')+dataset(m,'validation');chosen=[]
    for sign in (1,-1):
        choices=[r for r in rows if r['outcomes']['trap_no_low']['win']-r['outcomes']['baseline']['win']==sign]
        chosen.append(sorted(choices,key=lambda r:(r['source']['seed'],r['source']['opponent_spec']['name'],r['source']['seat']))[0])
    setup('B')
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    from development.secret_hunter_tactics.run import opponent
    from action_validator import legal
    db=train.connect(RUN);audits=[];lines=['# 独立留牌确认的逐动作案例','',
      '从锁定规则的新确认批次各取一个翻胜和回归。这里核对初始手牌、完整双方动作序列、回合与最终胜者；旧标签没有逐步公开状态哈希，因此不声称与旧状态逐字段比较。下表状态由当前冻结引擎重放所得。两版后续出牌均固定 B，BM 只改初始留牌，144 个起手已另外验证真实 CLI 与该干预相同。','',
      '相同初始种子的换牌张数不同会改变后续摸牌和随机数消耗，不能把整局翻转全部归给陷阱某次伤害。条件样本不是全池胜率。','']
    for row in chosen:
        src=row['source'];seat=src['seat'];spec=src['opponent_spec'];delta=row['outcomes']['trap_no_low']['win']-row['outcomes']['baseline']['win']
        lines += ['## '+('翻胜' if delta>0 else '回归')+'：'+src['case'],'']
        notes={
          'm-B-51421041-astra-board-proxy-s2':'两条轨迹前两回合都先奥秘守护者再飞刀。保留陷阱的一侧 T3 挂爆炸陷阱，对方恐狼攻击英雄时，实际清掉飞刀、恐狼、虚空行者三只随从，己方仍28血；最终T9以麻风侏儒撞随从触发亡语致死。原换牌一侧T3打出动物伙伴后失去场面，T7被压至5血并败。',
          'm-B-51421012-astra-board-proxy-s1':'保留陷阱的一侧T2确实用爆炸清掉战利品贮藏者和银色侍从，却仍在T9败北；原换牌一侧得到奥秘守护者与软泥怪的前期站场，随后弓接攻击取得胜利。一次漂亮清场不能单独证明起手选择更好。'}
        if src['case'] in notes:lines += [notes[src['case']],'']
        for route in ('baseline','trap_no_low'):
            key='opening-case-'+src['case']+'-'+route;path=RUN/'opening-case-replays'/(key+'.json')
            existing=db.execute('select * from auxiliary_games where key=?',(key,)).fetchone()
            if existing:
                assert existing['status']=='done';result=json.loads(path.read_text())
            else:
                assert db.execute('select count(*) from attempts').fetchone()[0]+db.execute('select count(*) from auxiliary_games').fetchone()[0]<train.meta(db,'manifest')['limits']['full_games']
                with db:db.execute('insert into auxiliary_games values (?,?,?,?,?)',(key,'running',time.time(),None,None))
                try:
                    label=row['outcomes'][route];decks={seat:load_deck(HERE/'candidates/B/deck.json'),3-seat:load_deck(ROOT/spec['deck'])}
                    e=Engine(decks[1],decks[2],src['seed'],max_turns=180);records=[]
                    def step(active,a):
                        before=visible(e.view(seat));own=e.view(active);assert legal(own,a)
                        assert e.step(active,a).accepted
                        records.append({'player':active,'action':a,'before_public':before,'after_public':visible(e.view(seat))})
                    assert [(c['entity_id'],c['card_id']) for c in e.view(seat)['you']['hand']]==[tuple(x) for x in src['opening_hand']]
                    if e.pending()[0]!=seat:
                        other=e.pending()[0];step(other,opponent(spec).fn(e.view(other)))
                    step(seat,{'type':'mulligan','replace':label['job']['replace']})
                    for r in label['trace']:
                        assert not e.over and e.pending()[0]==r['seat'] and e.turn==r['turn']
                        step(r['seat'],r['action'])
                    assert e.over and e.winner==label['winner']
                    result={'key':key,'source':src['case'],'route':route,'winner':e.winner,'own_win':e.winner==seat,
                      'initial_hand_actions_turns_terminal_verified':True,'original_state_hashes_available':False,'all_actions':records,
                      'own_actions':[r for r in records if r['player']==seat]}
                    train.atomic(path,result)
                    with db:db.execute("update auxiliary_games set status='done',finished=?,result=? where key=?",(time.time(),json.dumps({'path':str(path),'own_win':result['own_win']}),key))
                except Exception as exc:
                    with db:db.execute("update auxiliary_games set status='error',finished=?,result=? where key=?",(time.time(),json.dumps({'error':repr(exc)}),key))
                    raise
            audits.append({'key':key,'own_win':result['own_win'],'path':str(path)})
            lines += [f"### {route}：{'胜' if result['own_win'] else '负'}",'',f"[完整双方 JSON](../../{path.relative_to(ROOT)})",'',
             '| 步 | T | 实际动作 | 动作后生命 我/敌 | 己方场面 | 敌方场面 |','|---:|---:|---|---|---|---|']
            for ix,r in enumerate(result['own_actions'],1):
                s=r['before_public'];z=r['after_public']
                lines.append(f"| {ix} | {s['you']['max_mana']} | {action(s,r['action'])} | {z['you']['hero']['health']}/{z['opponent']['hero']['health']} | {board(z['you'])} | {board(z['opponent'])} |")
            lines.append('')
    train.atomic(RUN/'opening-case-replay-audit.json',audits)
    (ROOT/'docs/secret_hunter_long/OPENING_CASES.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(audits))

if __name__=='__main__':main()
