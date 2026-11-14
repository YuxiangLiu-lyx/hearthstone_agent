"""Join immutable source lineage with actual batch usage and decisions."""
import json
from development.secret_hunter_long.study import ROOT, RUN, HERE
from development.secret_hunter_long.report_tables import table
from development.secret_hunter_mcgs import train


def main():
    db = train.connect(RUN)
    lineage = json.loads((HERE / 'lineage.json').read_text())
    decisions = json.loads((RUN / 'decisions.json').read_text())
    latest = {x['name']: x for x in decisions}
    recommendation_path = ROOT / 'docs/secret_hunter_long/recommendation.json'
    recommendation = json.loads(recommendation_path.read_text()) if recommendation_path.exists() else None
    lines = ['# 候选谱系与实际验证', '',
             '源码快照在创建后不改；状态决定另存，避免用后来的决定覆盖原始生成证据。',
             '只更换deck.json属于牌表配置变化；改变Python文件属于源码变化。离线小规则参数搜索若未过门槛，没有生成候选，也没有改变线上策略。',
             '完整有序30张、源码SHA-256、变动文件与时间在 `development/secret_hunter_long/lineage.json`；所有阶段决定在 `runs/long-20261114/decisions.json`。']
    rows = []
    for item in lineage:
        name = item['name']
        changes = item['changed_files']
        kind = '原始基线' if not changes else '源码改动' if any(p.endswith('.py') for p in changes) else '仅牌表配置'
        status = latest.get(name, {}).get('status', 'baseline' if name == 'B' else '已建快照，按批次验证')
        if recommendation and recommendation['recommended'] == name:
            status = '最终推荐'
        elif recommendation and recommendation['challenger'] == name:
            status = '最终挑战者未晋级'
        rows.append([name, item['parent'] or '—', item['generation'], kind, item['deck']['replacements'], status])
    table(lines, ['候选', '父代', '创建代', '改动类型', '相对B换卡数', '最新状态'], rows)
    for item in lineage:
        name = item['name']
        batches = [dict(r) for r in db.execute('select distinct b.id,b.phase,b.start,b.seeds,b.status from batches b join tasks t on t.batch=b.id where t.candidate=? order by b.start', (name,))]
        lines += ['', '## ' + name, '', item['hypothesis'], '',
                  '变动文件：' + (', '.join('`' + p + '`' for p in item['changed_files']) or '无；精确指定ZIP基线。'), '',
                  '源码SHA-256：`' + item['sha256'] + '`。']
        if name in latest:
            lines += ['', '决定：' + latest[name]['reason'], '', '证据：`' + latest[name]['evidence'] + '`。']
        if batches:
            table(lines, ['实际登记批次', '阶段', '来源种子', '组数', '状态'],
                  [[b['id'], b['phase'], f"{b['start']}–{b['start'] + b['seeds'] - 1}", b['seeds'], b['status']] for b in batches])
        else:
            lines += ['', '尚无整局批次。机制检查和条件标签与自然整局分开计。']
    rejected = [x for x in decisions if x['status'] == 'reject_without_build']
    if rejected:
        lines += ['', '## 未构建的学习提案']
        table(lines, ['提案', '原因', '证据'], [[x['name'], x['reason'], '`' + x['evidence'] + '`'] for x in rejected])
    output = ROOT / 'docs/secret_hunter_long/LINEAGE.md'
    output.write_text('\n'.join(lines) + '\n')
    print(output)


if __name__ == '__main__':
    main()
