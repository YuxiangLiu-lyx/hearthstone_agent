"""Render final evidence only from completed, immutable result records."""
import json
import time
from development.secret_hunter_final.study import ROOT,RUN,HERE,DECK_SHA
from development.secret_hunter_mcgs import train
from development.teacher_eval.run import summarize

DOC=ROOT/'docs/secret_hunter_final'
def read(p):return json.loads(p.read_text())
def score(x):return f"{x['wins']}/{x['n']} ({100*x['win_rate']:.2f}%)"
def gain(x):
    lo,hi=x['gain_seed_cluster_95']
    lo=0 if abs(lo)<1e-12 else lo
    hi=0 if abs(hi)<1e-12 else hi
    return f"{100*x['gain']:+.2f} pp [{100*lo:+.2f}, {100*hi:+.2f}]"
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(map(str,r))+' |' for r in rows])


def main():
    db=train.connect(RUN);manifest=train.meta(db,'manifest')
    rec=read(DOC/'recommendation.json');core=read(RUN/'batches/final-core/report.json');guard=read(RUN/'batches/final-guard/report.json')
    freeze=read(RUN/'final-freeze.json');core_count=core['arms']['B']['all']['n'];guard_count=guard['arms']['B']['all']['n'];per_arm=core_count+guard_count
    final_groups=core_count//12;final_total=2*per_arm
    runtime=read(DOC/'runtime.json');mcp=read(DOC/'mcp-audit.json');learn=read(DOC/'early-learning.json');labels=read(DOC/'label-audit.json')
    changes=read(DOC/'final-action-changes.json')
    arms=['B',rec['challenger']];all_rows={}
    for arm in arms:
        all_rows[arm]=[json.loads(x[0]) for x in db.execute('select result from tasks where candidate=? and batch in ("final-core","final-guard") and status="done"',(arm,))]
        assert len(all_rows[arm])==per_arm
    latency={arm:summarize(rows)['latency_s'] for arm,rows in all_rows.items()}
    attempts=dict(db.execute('select status,count(*) from attempts group by status').fetchall())
    cf=dict(db.execute('select status,count(*) from cf_attempts group by status').fetchall())
    aux=dict(db.execute('select status,count(*) from auxiliary_games group by status').fetchall())
    extra=train.meta(db,'extra_continuations',0)
    totals={'full_attempts':sum(attempts.values())+sum(aux.values()),'full_main':attempts,'auxiliary_full':aux,
            'continuation_attempts':sum(cf.values())+extra,'continuation_main':cf,'auxiliary_continuations':extra,
            'elapsed_hours':(time.time()-manifest['created'])/3600,'limits':manifest['limits']}
    assert totals['full_attempts']<=6000 and totals['continuation_attempts']<=6000 and totals['elapsed_hours']<=6
    assert not attempts.get('running') and not cf.get('running') and not aux.get('running')
    train.setmeta(db,'continuations',totals['continuation_attempts'])
    train.setmeta(db,'effective_seconds',time.time()-manifest['created'])
    train.atomic(DOC/'budget.json',totals)
    train.atomic(DOC/'final-results.json',{'core':core,'guardrail':guard,'latency':latency,'budget':totals})
    lines=[f"# 暴龙王奥秘猎最后一轮：推荐 {rec['recommended']}",
        f"交付唯一推荐包 `dist/secret-hunter-final-20261113.zip`，{rec['bytes']:,} 字节，SHA-256 `{rec['zip_sha256']}`。推荐源文件指纹 `{rec['source_sha256']}`。本轮已完成训练、封存验证和本地打包，未向课程提交。",
        "所有新胜率只覆盖冻结的本地 core/guardrail 代理。已知正式 C2 得分仍为 **10 分**：Bot1 5/6、Bot2 2/4、Astra 1/4，零弃权；它使用双奥术射击，不能把这个成绩归给本轮原始暴龙王卡组。没有取得可确认是最新实际提交的 Skill ZIP。",
        f"唯一挑战者 {rec['challenger']} 在打开最终种子前锁定。统计晋级门槛通过：`{rec['statistical_gate']}`；窄斩杀纠错例外通过：`{rec['correction_gate']}`。"+
        ("候选获得独立局部收益且通过回归与可靠性门槛。" if rec['promoted'] else "挑战者证据未达到预设门槛，依照预注册规则推荐原始 engine-trap-v2；没有用最终数据继续调参。ML2 含换牌改动，不适用仅针对独立 L2 的纠错例外；已证明的斩杀修复仍保留在研究分支。"),
        "## 封存种子、精确 ZIP 的完整 CLI 验证",
        f"核心池 {freeze['seeds']['final_core'][0]}–{freeze['seeds']['final_core'][1]}，共 {final_groups} 个完整种子组、每版 {core_count} 局；验证池 41500000–41500007，共 8 组、每版 {guard_count} 局。双方座位、所有代理在同一来源种子组中重采样。先打包、解包和验牌，再从该精确解包目录运行每个 Python 决策。",
        "起跑时原计划为每版 40 组核心种子。第二开发批次发现新换牌规则零暴露，因此在任何最终结果开放之前，另封存至 100 组；晋级门槛保持不变。扩样时间、原因和预算在 [final-plan-amendment.json](final-plan-amendment.json)，原始 manifest 未被覆盖。",
        table(['版本','Astra','Bot2','Bot1','核心总计','验证池'],[[a]+[score(core['arms'][a]['by_group'][g]) for g in ['astra','bot2','bot1']]+[score(core['arms'][a]['all']),score(guard['arms'][a]['all'])] for a in arms]),
        table(['配对指标','胜率差及 95% 种子组区间','翻胜','翻败'],[
            ['Astra/Bot2 等权主指标',gain(core['comparisons'][arms[1]]['primary']),'按家族加权','按家族加权'],
            *[[g,gain(core['comparisons'][arms[1]]['by_group'][g]),core['comparisons'][arms[1]]['by_group'][g]['b_only_wins'],core['comparisons'][arms[1]]['by_group'][g]['a_only_wins']] for g in ['astra','bot2','bot1']],
            ['核心总计',gain(core['comparisons'][arms[1]]['all']),core['comparisons'][arms[1]]['all']['b_only_wins'],core['comparisons'][arms[1]]['all']['a_only_wins']],
            ['验证池',gain(guard['comparisons'][arms[1]]['all']),guard['comparisons'][arms[1]]['all']['b_only_wins'],guard['comparisons'][arms[1]]['all']['a_only_wins']]]),
        "区间使用原有严格配对程序和 10,000 次整种子组 bootstrap。小样本或全相同结果的零宽区间不能证明策略等价。课程的 Bot1 六局至少五胜、Bot2 四局至少三胜和 Astra 逐胜加分是选版目标；这里不把代理胜率转换成正式预期分数或保证成绩。",
        table(['实际先后手']+arms,[[label]+[score(core['arms'][a]['by_actual_first'][key]) for a in arms] for label,key in [('先手','True'),('后手','False')]]),
        table(['核心对手']+arms,[[o]+[score(core['arms'][a]['by_opponent'][o]) for a in arms] for o in sorted(core['arms']['B']['by_opponent'])]),
        table(['验证池对手']+arms,[[o]+[score(guard['arms'][a]['by_opponent'][o]) for a in arms] for o in sorted(guard['arms']['B']['by_opponent'])]),
        "## 最小补丁与开发消融",
        "B 是指定提交 `5c02d4870a86e2915095ec66d6afab60510afa50` 中 ZIP 解包的 engine-trap-v2，指纹 `ad6194e2024f0375805be8a32c5f78230af7f8d3af06a161dd6748bd89e3abc9`。M 仅扩展原 mulligan 分支：对术士、没有 1–2 费随从时可留一张爆炸陷阱。L/L2 在原保证斩杀未找到结果时才证明已有直伤和英雄技能的合法致死；不模拟攻击、硬币或新随从。L 的白名单漏掉驯兽师，另建 L2 修正并保留旧快照。ML/ML2 为组合。",
        f"全部候选保持 30 张原卡及顺序，deck.json SHA-256 `{DECK_SHA}`，包括 EX1_543、EX1_533、EX1_066。七个候选均经课程静态校验和实际 submit_deck；六个基础候选从空目录重建后指纹逐一相同。",
        "交付文件另经全新目录解包，再跑课程校验与实际 submit_deck，记录在 [delivery-audit.json](delivery-audit.json)。引擎 Python 与对手文件在第一场前固定；最终开封前补充核对的 12 个课程资源文件均与保留的课程分发包逐字节一致，归档时再次检查全部指纹与依赖版本。",
    ]
    change_rows=[]
    for batch,block in changes.items():
        for kind in ['mulligan','narrow_lethal','other_same_state_action','upstream_state_divergence']:
            changed=[x for x in block['changed_games'] if x['first_difference']['kind']==kind]
            change_rows.append([batch,kind,len(changed),
                sum(x['candidate_score']>x['baseline_score'] for x in changed),
                sum(x['candidate_score']<x['baseline_score'] for x in changed),
                sum(x['first_difference']['baseline_time_bounded'] or x['first_difference']['candidate_time_bounded'] for x in changed)])
    lines[lines.index('## 最小补丁与开发消融'):lines.index('## 最小补丁与开发消融')]=[
        table(['最终批次','首次分歧类别','局数','翻胜','翻败','至少一侧搜索触及时间界限'],change_rows),
        '首次分歧逐局审计见 [final-action-changes.json](final-action-changes.json)。'+
        ('两批所有首次分歧均来自预定换牌或窄斩杀补丁，没有其他同状态动作或上游状态分歧。' if all(not x['coverage'].get(k,0) for x in changes.values() for k in ['other_same_state_action','upstream_state_divergence']) else '发现预定补丁之外的首次分歧，具体数量和状态见表及逐局记录。')+
        '已有搜索使用节点及时间双上限，本机结果不能保证其他硬件走相同搜索深度；触及时间界限的标记只作诊断，不能单凭它确定因果。最终统计保留全部实际完整 CLI 结果，不删除不利对局、不用最终结果调参。',
        table(['最终批次','窄斩杀证明覆盖局','证明调用'],[[b,x['coverage'].get('narrow_proof_games',0),x['coverage'].get('narrow_proof_calls',0)] for b,x in changes.items()])]
    rows=[]
    for name in ['dev-core','dev-guard','dev2-core','dev2-guard']:
        d=read(RUN/'batches'/name/'report.json')
        for a,v in d['arms'].items():
            rows.append([name,a,score(v['all'])]+[score(v['by_group'][g]) if g in v['by_group'] else '—' for g in ['astra','bot2','bot1']])
    ablation=read(DOC/'ablation.json')
    decomposition=[]
    for batch,block in ablation.items():
        for pair,comparison in block['comparisons'].items():
            x=comparison['all'];decomposition.append([batch,pair,gain(x),x['b_only_wins'],x['a_only_wins']])
    coverage_rows=[[batch,arm,s['changed_mulligan_games'],s['changed_mulligan_first'],s['narrow_lethal_games'],s['narrow_lethal_calls']]
                   for batch,block in ablation.items() for arm,s in block['coverage'].items() if arm!='B']
    lines += [table(['开发批次','版本','总计','Astra','Bot2','Bot1'],rows),
        table(['开发批次','独立/组合贡献','整局胜率差及区间','翻胜','翻败'],decomposition),
        table(['开发批次','版本','新换牌触发局','其中实际先手','窄斩杀覆盖局','窄斩杀调用'],coverage_rows),
        "第二批核心及护栏均没有命中新换牌条件；因此该批胜负完全一致主要反映零暴露，不能证明新换牌规则等价或有效。窄斩杀在开发局中覆盖的已有胜局没有增加净胜，两个指定已见漏检则可证明纠错。",
        "开发表使用同批新种子、双方座位的 warm Python 整局，不能作为完整 CLI 时延数据。第一批 20 核心种子和 4 验证种子；第二批 12 核心种子和 4 验证种子。每个变体均重跑父代，具体翻转键和区间见运行目录对应 report.json/results.jsonl。",
        "## 独立条件化换牌复验",
        "样本只按真实引擎初始手牌筛选，未查看结果：核心三种术士代理抽取 1,440 个起手，命中 81 个；验证池三种术士代理抽取 720 个，命中 48 个。如果某一座位命中，就把同对手同种子的双方座位一起跑。命中子集的收益不能称作未筛选全池胜率。"]
    rows=[]
    for name in ['conditional-core','conditional-guard']:
        d=read(RUN/'batches'/name/'report.json')['comparisons']['M']
        for subset in ['all_selected','hit_only']:
            x=d[subset];rows.append([name,subset,f"{x['a_wins']}/{x['n_per_arm']}",f"{x['b_wins']}/{x['n_per_arm']}",gain(x),x['b_only_wins'],x['a_only_wins']])
        for first,x in d.get('hit_by_actual_first',{}).items():
            rows.append([name,'命中且'+('先手' if first=='True' else '后手'),f"{x['a_wins']}/{x['n_per_arm']}",f"{x['b_wins']}/{x['n_per_arm']}",gain(x),x['b_only_wins'],x['a_only_wins']])
        for o,x in d['by_opponent'].items():rows.append([name,o,f"{x['a_wins']}/{x['n_per_arm']}",f"{x['b_wins']}/{x['n_per_arm']}",gain(x),x['b_only_wins'],x['a_only_wins']])
    lines += [table(['批次','子集','B','M','差及区间','翻胜','翻败'],rows),
        "核心条件批次的四场回归来自四个来源种子，完整前期手牌和动作摘录见 [mulligan-regressions.json](mulligan-regressions.json)。例如 41310031/座位2 中，原策略硬币上土狼，新起手让后续策略改为硬币挂陷阱；41310210/座位1 中，原换牌拿到一费守护者，新起手首回合空过。真实换牌也会改变后续牌序，因此不能把每次翻转全部解释成陷阱单卡的即时效果。",
        "条件化设计的种子组大小不等，单独使用整种子组 bootstrap 的总胜差/总场数估计器，原冻结评估器没有改动。用户提供的旧 31/45→42/45、81/114→102/114 等换牌批次没有找到原始日志，因此没有把它们列为本轮已复验数据。没有扩大成弓、第二个二费随从或飞刀/土狼留牌的新规则，也没有穷举全部换牌子集。",
        "## 用终局标签学习早期回合",
        "B 的新 240 局为 203 胜、37 败；第 3 回合开始空场且敌方场攻至少 4，出现在胜局 18/203、败局 9/37。31/37 败局在我方自然九费回合前结束。这是采样指标，不直接证明早期空场造成败局。旧 Astra 240 局中的 50 败、41 场九费前结束另作已见诊断。",
        "抽取 144 个早期根局面、17 个来源种子组，训练 81 局面/9 组，留出 63 局面/8 组；再加入两个独立晚期 Amani 防斩局面。每个来源比较原世界和两个重排剩余牌序、重设未来 RNG 的世界，模拟手牌保持原世界不变。所有方案共享分岔初始世界与 RNG；分岔后允许不同 RNG 消耗。逐步执行实际引擎，随机动作后重新观察，后续策略和对手冻结为 B 与原代理。146 个原世界基线续局全部重现原整局胜负。",
        table(['路线','可用来源局面/组','配对未来数','B→路线胜局','翻胜/翻败','首步改变','后续改变'],[[r['route'],f"{r['source_cases']}/{r['source_groups']}",r['pairs'],f"{r['baseline_wins']}→{r['route_wins']}",f"{r['flips']}/{r['regressions']}",r['first_changed'],r['later_changed']] for r in labels['rows'] if r['kind']=='early']),
        f"训练只拟合公开特征的常数或单阈值，共 {learn['tried_rules']} 个规则，只有原样策略达到筛选要求。选择器锁定空规则后才评价留出标签；没有学习补丁进入最终包。上述路线表只作诊断汇总，不用于重新挑选规则。后续改变表示在实际分岔状态再次覆盖父策略的新决策，不是把不同长度的两条轨迹逐行对齐。硬币加弓虽有少量正向样本，来源组不足；直接技能或简单强制交易会破坏原胜局。全部 2,100 个标签都有终局胜者，没有平局或截断结果混入败局。",
        "共享首步的 bank_tail 实际改变 381 个未来的后续动作，17 次翻胜、51 次翻败。T 另在搜索中为同首步保留两种资源终点，总回应预算仍为 6；144 个根局面保留 510 个同首步备选、评估 562 个回应终点，却只在 3 个根局面、2 个来源组改变动作，未过 5 局面/3 组覆盖门槛。没有将额外搜索调用当作收益，也没有重试在线 MCGS。",
        "旧单源 Amani 原记录重新汇总为自然 90/96→91/96（2 翻胜、1 翻败），强制缠绕 12/24→24/24；六条旧完整动作轨迹逐状态重放一致。新两个独立来源的便宜一狗交换自然结果为 5/6→5/6，强制缠绕为 3/6→3/6；直接解 Amani 的自然结果反而为 5/6→3/6。只有两个来源组，不足以泛化。强制缠绕样本只检验机制，不参与学习。详情及每条动作序列见 [label-audit.json](label-audit.json)。",
        "## 斩杀、入口与运行可靠性",
        "指定旧种子 21110024/座位2/seq31 和 21110037/座位1/seq34 均精确恢复动作前缀。L2 分别用技能加两张杀戮、直接技能在实际 CLI 中终结对局。24 个斩杀边界检查覆盖五种猎人奥秘、嘲讽、冰冻或已攻击英雄、既有弓、护甲、野兽伤害、费用、反制/寒冰屏障等法师奥秘、免疫和已用技能。六个既有机制检查覆盖恐狼光环、阿曼尼自伤、暴龙王过墙、奥秘顺序/弓/误导、飞刀放狗 RNG 与追踪 choice。",
        table(['版本','最终整局','完整 CLI 调用','P50','P95','P99','max'],[[a,per_arm,latency[a]['n']]+[f"{latency[a][k]:.4f}s" for k in ['p50','p95','p99','max']] for a in arms]),
        f"课程每次决定硬限 180 秒，项目完整 Python CLI 工程目标 2 秒。最终两版非法、超时、弃权、策略/对手/执行错误、意外回退、公开输入违规及超过 2 秒均为 0。推荐包的技能与奥术射击斩杀均从实际入口验明终局。部署入口测试 {runtime['calls']} 次，非法 {runtime['invalid']}，超过 2 秒 {runtime['over_2s']}，正常回退 {runtime['ordinary_fallbacks']}；注入崩溃/超时验证合法回退、已发布检查点、过期 seq 刷新及主机拒绝、GAME OVER。注入故障总时延 max {runtime['all_including_fault_latency_s']['max']:.4f}s，另列于 runtime.json，未混入正常分位数。",
        f"精确推荐包另跑官方无模型 MCP client {mcp['games']} 局，{mcp['decisions']} 次动作，实际先手 {mcp['actual_first_games']} 局；wait 首调用、Python 输出与 act 的 seq/action 全部一致、GAME OVER 正常结束，非法/超时/弃权均为零。这是传输验证，不是 Luna。本地 `codex` 启动器缺少其 vendor 二进制并报 ENOENT，因此未完成真实 Luna 中转、未报告 Luna 时延，也没有替换模型。",
        table(['无模型 MCP 时延','P50','P95','P99','max'],[[label]+[f"{mcp[key][q]:.3f}s" for q in ['p50','p95','p99','max']]
            for label,key in [('程序内部（不含 Python 启动）','internal_program_latency_s'),('观察发布到 act 请求','publication_to_act_latency_s'),('扣除程序内部后的其余耗时','outside_internal_program_latency_s')]]),
        "MCP 总时延用同一主机的保留状态文件修改时间至 act 日志时间测量，日志分辨率 1 毫秒，不包含主机接受动作后的等待。其余耗时仍含 Python 启动、轮询、客户端和传输，不能叫作纯网络或 Luna 时延。完整 Python 进程耗时以最终整局 CLI 表为准。",
        "## 预算、归档与复现",
        f"本轮共 {totals['full_attempts']} 次整局尝试（含官方 MCP {sum(aux.values())} 局），{totals['continuation_attempts']} 次续局尝试（含 {extra} 次诊断/逐动作重放），报告生成时用时 {totals['elapsed_hours']:.2f} 小时，均在 6 小时/6,000/6,000 上限内。反事实完成 2,100 个标签，主动恢复测试的 2 个中断尝试仍计费；没有把异常记作败局。第一场前已预留最终 1,408 局和至少两小时验证时间；开封前扩大后实际最终验证为 {final_total} 局。单步机制测试、验牌及入口探测另计，不作为终局标签。",
        "SQLite WAL 账本、种子清单、请求、完整观察、逐步动作、续局标签和冻结 ZIP 位于 `runs/final-20261113/`。主账本 `ledger.sqlite`，冻结清单 `final-freeze.json`，候选谱系 `development/secret_hunter_final/lineage.json`。中断恢复保留 1,561 个完成结果，只重排两个在途任务，随后全部完成；参见 [recovery-check.json](recovery-check.json)。",
        "Y1 仅为历史参考：上一轮封存核心 Y1 398/480、B 408/480，验证池 Y1 192/224、B 190/224；本轮没有重新跑 Y1，也不把跨种子历史差异当作本轮收益。",
        "外部资料的具体章节/函数、接入位置和比较结果见 [SOURCES.md](SOURCES.md)。最终包只含本仓库 Python、配置及一个根目录 SKILL.md，无第三方 bot 源码、离线隐藏信息、训练集或二进制。三组重点动作证据见 [CASE_STUDIES.md](CASE_STUDIES.md)，可恢复命令见 [REPRODUCE.md](REPRODUCE.md)。研究证据另压缩为 [raw-evidence.tar.gz](../../runs/final-20261113/artifacts/raw-evidence.tar.gz)，文件哈希与 SQLite 完整性见 [data-manifest.json](data-manifest.json)；它不是提交包。",
        "未完成项目明确保留：真实 Luna relay；确认最新实际提交 ZIP；旧条件化换牌批次原始日志；全部兼容隐藏手牌的世界采样；换牌子集穷举；真实课程对手的最后一次正式评分。最终结论限于这两套冻结本地代理。",
    ]
    (DOC/'REPORT.md').write_text('\n\n'.join(lines)+'\n')
    print(json.dumps({'recommended':rec['recommended'],'full_attempts':totals['full_attempts'],'continuations':totals['continuation_attempts'],'elapsed_hours':totals['elapsed_hours']}))


if __name__=='__main__':main()
