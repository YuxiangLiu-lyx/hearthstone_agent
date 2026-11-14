"""Render auditable tables directly from completed experiment reports."""
import json
from development.secret_hunter_long.study import RUN, ROOT, HERE
from development.secret_hunter_mcgs import train


def pp(value):
    return f'{100 * value:+.3f}'


def interval(values):
    return '[' + ', '.join(pp(v) for v in values) + ']'


def table(lines, headers, rows):
    lines.extend(['', '| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |'])
    lines.extend('| ' + ' | '.join(str(x) for x in row) + ' |' for row in rows)
    lines.append('')


def main():
    db = train.connect(RUN)
    lines = ['# 完成批次的可核查统计表', '',
             '由 `development.secret_hunter_long.report_tables` 从 SQLite 和已完成报告生成。胜负都是终局结果。',
             '开发、选拔和最终留出分开列示；重复开发比较的区间不作多重选择后的显著性保证。主指标为 Astra/Bot2 家族等权；差值与区间单位均为百分点。',
             '所有区间重采完整来源种子。无主指标的护栏池只报告总胜率差。']
    for batch in db.execute("select * from batches where status='done' order by start"):
        path = RUN / 'batches' / batch['id'] / 'report.json'
        if not path.exists():
            continue
        report = json.loads(path.read_text())
        lines += [f"## {batch['id']}", '',
                  f"阶段 `{batch['phase']}`，{batch['seeds']} 组，来源种子 {batch['start']}–{batch['start'] + batch['seeds'] - 1}。"]
        rows = []
        for arm, summary in report['arms'].items():
            all_games = summary['all']
            comparison = report['comparisons'].get(arm)
            primary = comparison.get('primary') if comparison else None
            error_keys = ('illegal', 'timeouts', 'forfeits', 'harness_errors', 'opponent_errors', 'policy_errors', 'fallbacks', 'over_2s', 'public_input_violations')
            issues = ', '.join(f'{k}={all_games[k]}' for k in error_keys if all_games[k]) or '0'
            rows.append([arm, f"{all_games['wins']}/{all_games['n']}", f"{100 * all_games['win_rate']:.3f}%",
                         f"{comparison['all']['b_only_wins']}/{comparison['all']['a_only_wins']}" if comparison else '基线',
                         pp(primary['gain']) if primary else '—', interval(primary['gain_seed_cluster_95']) if primary else '—', issues])
        table(lines, ['候选', '胜/局', '总胜率', '翻胜/翻败', '主指标差', '主指标95%区间', '可靠性异常'], rows)
        rows = []
        for arm, comparison in report['comparisons'].items():
            for group, values in comparison['by_group'].items():
                rows.append([arm, group, f"{values['a_wins']}/{values['n_per_arm']}", f"{values['b_wins']}/{values['n_per_arm']}", pp(values['gain']), interval(values['gain_seed_cluster_95'])])
        if rows:
            table(lines, ['候选', '家族', '基线胜/局', '候选胜/局', '差', '95%区间'], rows)
        rows = []
        for arm, summary in report['arms'].items():
            latency = summary['latency_s']
            rows.append([arm, latency['n'], *(f"{latency[k]:.6f}" for k in ('p50', 'p95', 'p99', 'max'))])
        table(lines, ['候选', '决策数', 'P50秒', 'P95秒', 'P99秒', '最大秒'], rows)
        lines.append('development 阶段为 warm Python；cli_development、selection、final_core、final_guard 为完整 Python CLI。模型中转耗时另见真实链路审计。')
        if batch['phase'].startswith('final') or batch['id'].startswith('selection-'):
            for arm in json.loads(batch['arms'])[1:]:
                path = RUN / 'analysis' / f"{batch['id']}-B-{arm}-paired.json"
                if not path.exists():
                    continue
                paired = json.loads(path.read_text())
                for key, title in [('by_opponent', '每个对手'), ('by_actual_first', '实际先后手（True为先手）')]:
                    lines += ['', f'### {arm}：{title}']
                    rows = [[name, x['n_per_arm'], x['a_wins'], x['b_wins'], x['rescued'], x['lost_old_wins'], pp(x['gain']), interval(x['gain_seed_cluster_95'])] for name, x in paired[key].items()]
                    table(lines, ['层', '局/版', 'B胜', '候选胜', '翻胜', '翻败', '差', '95%区间'], rows)
    lines += ['', '## 不可变候选指纹', '', '有序30张、父代、变动文件与生成时间在 `development/secret_hunter_long/lineage.json`；采用或淘汰决定另记 `runs/long-20261114/decisions.json`。']
    lineage = json.loads((HERE / 'lineage.json').read_text())
    table(lines, ['候选', '父代', '替换张数', '保留暴龙王', '源码SHA-256'],
          [[x['name'], x['parent'] or '—', x['deck']['replacements'], x['deck']['krush_line'], f"`{x['sha256']}`"] for x in lineage])
    output = ROOT / 'docs/secret_hunter_long/STATISTICS.md'
    output.write_text('\n'.join(lines) + '\n')
    print(output)


if __name__ == '__main__':
    main()
