"""Readable, reproducible tables from the four closed development reports."""
import argparse
import json
from pathlib import Path


def row(label, value):
    n = value['n_per_arm']
    lo, hi = value['gain_seed_cluster_95']
    return (f"| {label} | {value['a_wins']}/{n} → {value['b_wins']}/{n} | "
            f"{100 * value['gain']:+.3f} | [{100 * lo:+.3f}, {100 * hi:+.3f}] | "
            f"{value['b_only_wins']} / {value['a_only_wins']} |")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-run', type=Path, required=True)
    args = parser.parse_args()
    lines = ['# 已完成开发对照', '',
             '每轮为不同的 40 个新来源种子、每个核心对手双座位。只能比较同一行的 DARCL2 与候选。'
             '以下区间为完整来源种子配对 bootstrap 的描述性 95% 区间；自适应开发结果不代替独立最终晋级。'
             '翻胜 / 翻败均以 DARCL2 为对照。没有读取未完成 DA2 确认或资源试跑的胜负。', '']
    for batch, arm in [('round1-recall', 'RJC'), ('round2-ranker', 'PRR'),
                       ('round3-arcane', 'DA2'), ('round4-hand-resource', 'EHC')]:
        report = json.loads((args.source_run / 'batches' / batch / 'report.json').read_text())
        contrast = report['comparisons'][arm]
        lines += [f'## {arm}：{report["start"]}–{report["start"] + 39}', '',
                  '| 对手或合计 | DARCL2 → 候选 | 差值 pp | 95% 区间 pp | 翻胜 / 翻败 |',
                  '| --- | --- | --- | --- | --- |']
        lines += [row(name, value) for name, value in contrast['by_opponent'].items()]
        lines += [row('Astra 三代理等权', contrast['primary']), row('Bot 2 两代理合计', contrast['by_group']['bot2']), '']
        lines += ['| Astra 分层 | DARCL2 → 候选 | 差值 pp | 95% 区间 pp | 翻胜 / 翻败 |',
                  '| --- | --- | --- | --- | --- |']
        lines += [row('输入座位 ' + name, value) for name, value in contrast['primary_by_seat'].items()]
        lines += [row('引擎实际先手' if name == 'True' else '引擎实际后手', value)
                  for name, value in contrast['primary_by_actual_first'].items()]
        lines += ['', f"Astra 单侧 90% 下界：{100 * contrast['primary']['gain_one_sided_90_lower']:+.3f} pp。", '']
    lines += ['这些实验未运行新的护栏胜率比较。DA2 的 +0.833 pp 小样本点估计及负的单侧下界，'
              '均不能支持“正式 Astra 多赢一局”的结论。正式 10 分回执与课程档位解释见最终报告。', '']
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
