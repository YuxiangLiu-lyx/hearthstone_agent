"""Readable fixed-pool comparisons and paired course-tier interpretation."""
import json
from development.secret_hunter_astra_sprint.study import ROOT,RUN
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.selection import simulate

def table(lines,headers,rows):
 lines.extend(['','| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|'])
 lines.extend('| '+' | '.join(str(x) for x in row)+' |' for row in rows);lines.append('')

def row(name,r):
 lo,hi=r['gain_seed_cluster_95'];n=r['n_per_arm']
 return [name,f"{r['a_wins']}/{n}",f"{r['b_wins']}/{n}",f"{100*r['gain']:+.3f}",f"[{100*lo:+.3f}, {100*hi:+.3f}]",f"{100*r['gain_one_sided_90_lower']:+.3f}",f"{r['b_only_wins']}/{r['a_only_wins']}"]

def main():
 db=ledger.connect(RUN);rec=json.loads((ROOT/'docs/secret_hunter_astra_sprint/recommendation.json').read_text());arm=rec['challenger'];freeze=json.loads((RUN/'final-freeze.json').read_text());reports={}
 for b in ('final-core','final-guard'):
  assert db.execute('select status from batches where id=?',(b,)).fetchone()[0]=='done';reports[b]=json.loads((RUN/'batches'/b/'report.json').read_text())
 opening=(f'基线固定 DARCL2，唯一挑战者 {arm}。' if arm!='DARCL2' else '没有获得可晋级挑战者的完整证据；此次最终池仅验收原字节 DARCL2，不声称挑战者晋级或新的策略增益。')
 method=('置信区间重采完整来源种子 10,000 次（RNG 20261115），同种子的两个座位和所有对手共同抽取。三类 Astra 样本数相同，合并均值等于三代理等权胜率。百分点门槛用未四舍五入的数值判断。' if arm!='DARCL2' else '原版单臂验收只报告观察胜率与分层计数，没有可估计的候选配对增益区间。三类 Astra 样本数相同，合并均值等于三代理等权胜率。开发候选的配对区间见 DEVELOPMENT.md。')
 lines=['# 冻结最终统计','',opening+'全部种子、两座位、对手和 ZIP 在最终开封前冻结；两池补齐后才读取胜负。',method]
 headers=['家族/对手','DARCL2 胜/局',arm+' 胜/局','差值 pp','双侧95%区间 pp','单侧90%下界 pp','翻胜/翻败']
 for b,title in [('final-core','核心'),('final-guard','护栏')]:
  lines+=['','## '+title,''];c=reports[b]['comparisons'].get(arm)
  if not c:
   summary=reports[b]['arms']['DARCL2']
   table(lines,['家族/对手','DARCL2 胜/局','胜率'],[[name,f"{r['wins']}/{r['n']}",f"{100*r['win_rate']:.3f}%"] for collection in ('by_group','by_opponent') for name,r in summary[collection].items()])
   baseline_rows=[json.loads(r[0]) for r in db.execute('select result from tasks where batch=? and candidate=?',(b,'DARCL2'))]
   focus=[r for r in baseline_rows if r['group']=='astra'] if b=='final-core' else baseline_rows
   strata=[]
   for seat in (1,2):
    selected=[r for r in focus if r['seat']==seat];strata.append(['座位 '+str(seat),sum(r['score'] for r in selected),len(selected)])
   for first in (True,False):
    selected=[r for r in focus if (r['first_player']==r['seat'])==first];strata.append(['实际先手' if first else '实际后手',sum(r['score'] for r in selected),len(selected)])
   lines+=['仅列 Astra 分层。' if b=='final-core' else '护栏分层。']
   table(lines,['分层','胜','局'],strata)
   continue
  table(lines,headers,[row(name,r) for name,r in c['by_group'].items()])
  table(lines,headers,[row(name,r) for name,r in c['by_opponent'].items()])
  if c['primary']:
   lines+=['### Astra 座位与引擎实际先后手','']
   table(lines,headers,[row('座位 '+s,r) for s,r in c['primary_by_seat'].items()]+[row('实际先手' if s=='True' else '实际后手',r) for s,r in c['primary_by_actual_first'].items()])
  else:
   table(lines,headers,[row('座位 '+s,r) for s,r in c['by_seat'].items()]+[row('实际先手' if s=='True' else '实际后手',r) for s,r in c['by_actual_first'].items()])
 lines+=['## 晋级判定','']
 table(lines,['条件','结果'],[[k,'通过' if v else '未通过'] for k,v in rec['gates'].items()])
 rows={a:[json.loads(r[0]) for r in db.execute("select result from tasks where batch='final-core' and candidate=?",(a,))] for a in freeze['arms']}
 simulation=simulate(rows);ledger.atomic(RUN/'final-score-simulation.json',simulation);ledger.atomic(ROOT/'docs/secret_hunter_astra_sprint/final-score-simulation.json',simulation)
 lines+=['## 6/4/4 胜场档位解释','',
 '沿用选拔前固定的双座位平衡抽样：每次抽三个来源组，Bot 1 用六局；Bot 2、Astra 分别均匀抽一个家族代理，用前两个来源组的双座位四局。重复 50,000 次；若有两版，两版共用同一抽样配置，单版则只描述原版。假定零弃权，完成分为 5；Bot 1 的 5/6 胜和 Bot 2 的 3/4 胜进入最高胜场档位。',
 '这里只解释固定代理上的取舍，不校准或预测正式 Astra/课程成绩，不参与最终晋级门槛。历史 10 分实际回执的 Bot 2 为 2/4，尚未达到其最高档。']
 table(lines,['版本','模拟总分>10 频率','均值 max(总分−10,0)','Bot 1 达最高档频率','Bot 2 达最高档频率'],[[a,f"{100*r['frequency_score_above_10']:.3f}%",f"{r['mean_max_score_minus_10_zero']:.5f}",f"{100*r['bot1_cap_frequency']:.3f}%",f"{100*r['bot2_cap_frequency']:.3f}%"] for a,r in simulation['results'].items()])
 out=ROOT/'docs/secret_hunter_astra_sprint/STATISTICS.md';out.write_text('\n'.join(lines)+'\n');print(out)
if __name__=='__main__':main()
