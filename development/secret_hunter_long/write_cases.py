"""Readable action-by-action evidence from exact actual-engine replay audits."""
import json
from development.secret_hunter_long.study import ROOT,RUN

CASES=[
 ('51401009-astra-board-proxy-s2','翻胜：T2 奥术射击移除恐狼',
  'B 在 T2 继续站奥秘守护者，T3 才以软泥怪换恐狼；DARC 在 T2 花一费奥术射击移除恐狼，软泥怪继续打脸。DARC 到 T6 用狗逐一拆墙和随从后压至对手 6 血，T7 技能、恐狼、毒蛇完成终结。B 在 T6 虽放出七只狗，却未攻破场面，随后失败。这里验证了一个真实前期使用奥术射击后翻胜的完整轨迹。'),
 ('51401008-bot2-trade-proxy-s1','回归：暴龙王完成真实终结',
  '两版前五回合执行相同动作。T6 B 挂爆炸陷阱并放狗；DARC 挂陷阱、技能加奥术射击打脸。B 到 T9 自身仅 3 血，对手 6 血，打出暴龙王并冲锋；雷欧克加攻令此次攻击造成 9 点伤害，终局对手 −3 血。DARC 到 T9 没有这张冲锋终结牌，技能后对手仍 7 血，次回合输掉。这证明暴龙王在本轨迹确实完成致死攻击，并不证明其它低费打牌路径都必败。'),
 ('51401047-astra-sticky-proxy-s2','回归：早解场没有转化为胜率',
  'DARC T1 奥术射击杀烈焰小鬼，硬币加麻风侏儒，暂时保全生命；B T1 硬币飞刀、T2 土狼，T3 动物伙伴得到米莎，随后驯兽师强化。B T6 以米莎、杀戮命令和技能把对手压至 2 血，T7 麻风侏儒撞银色侍从触发亡语完成过墙致死。DARC 的伙伴和随机消耗轨迹不同，T7 杀戮用于解收割机，T9 空场且对方五随从，最终失败。不能把早期少掉血等同于终局收益。')]

def names(s):
    return {x['entity_id']:x.get('name',str(x['entity_id'])) for side in ('you','opponent')
            for x in s[side].get('hand',[])+s[side]['board']+[s[side]['hero']]}

def action(s,a):
    n=names(s);kind=a['type'];txt=kind
    if kind=='play_card':txt+=' '+n.get(a['card'],str(a['card']))
    if kind=='attack':txt+=' '+n.get(a['attacker'],str(a['attacker']))
    if 'target' in a:txt+=' → '+n.get(a['target'],str(a['target']))
    if kind=='mulligan':txt+=' 换走 '+(', '.join(n.get(x,str(x)) for x in a['replace']) or '无')
    if kind=='choose':txt+=' '+str(a)
    if kind=='play_card' and 'position' in a:txt+=f"，站位 {a['position']}"
    return txt.replace('|','\\|')

def board(side):
    return '，'.join(f"{c['name']} {c['attack']}/{c['health']}" for c in side['board']) or '空'

def main():
    lines=['# 逐动作案例', '', '三组 B/DARC 严格同 `(opponent, seed, seat)` 配对，共六局已用真实课程引擎重放。每个动作前公开状态、动作合法性、动作执行及最终胜者都核对一致；审计在 `runs/long-20261114/case-replay-audit.json`。',
     '', '下表是所有己方实际动作及动作后的己方公开状态。完整 JSON 同时保存双方每一步动作、前后公开状态、合法动作集合；表内 T 为己方最大法力水晶，硬币不改变这个编号。不同牌表从初始牌库公开计数即不同，后续摸牌和随机数消耗也会分岔；案例解释机制，不能单独证明换卡因果收益。总体价值由新种子的成对终局比较决定。', '']
    for suffix,title,summary in CASES:
        lines += ['## '+title,'',summary,'']
        for arm in ('B','DARC'):
            path=RUN/'case-replays'/f'case-{arm}-{suffix}.json';r=json.loads(path.read_text());seat=r['own_actions'][0]['player']
            lines += [f"### {arm}：{'胜' if r['winner']==seat else '负'}",'',f"原始逐步状态：[JSON](../../{path.relative_to(ROOT)})。双方总动作 {r['steps']}，己方动作 {len(r['own_actions'])}。",'',
              '| 步 | T | 实际动作 | 动作后生命 我/敌 | 动作后己方场面 | 动作后敌方场面 |',
              '|---:|---:|---|---|---|---|']
            for ix,x in enumerate(r['own_actions'],1):
                s=x['before_public'];z=x['after_public']
                lines.append(f"| {ix} | {s['you']['max_mana']} | {action(s,x['action'])} | {z['you']['hero']['health']}/{z['opponent']['hero']['health']} | {board(z['you'])} | {board(z['opponent'])} |")
            lines.append('')
    (ROOT/'docs/secret_hunter_long/CASE_STUDIES.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
