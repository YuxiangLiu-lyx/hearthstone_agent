"""Human-readable card exposure strata, without attributing indirect effects."""
import json
from development.secret_hunter_long.study import ROOT, RUN
from development.secret_hunter_long.report_tables import table


CARDS = {'B': [('EX1_543', '暴龙王'), ('EX1_162', '恐狼'), ('EX1_066', '软泥怪'), ('EX1_533', '误导')],
         'DARC': [('DS1_185', '奥术射击')], 'DWOLF': [('EX1_162', '两恐狼合计')],
         'KO': [('EX1_066', '两软泥怪合计'), ('EX1_543', '暴龙王')],
         'WOOZE': [('EX1_162', '两恐狼合计'), ('EX1_066', '两软泥怪合计')]}


def row(arm, name, layer, summary, card):
    c = summary['cards'][card]
    return [arm + '/' + name, layer, f"{summary['wins']}/{summary['n']}",
            f"{c['initial_copies']}/{c['replaced_copies']}",
            f"{c['received_copies']}/{c['ever_playable_copies']}/{c['played_copies']}",
            f"{c['games_played']}/{c['wins_when_played']}",
            f"{c['damage'].get('enemy_hero', 0)}/{c['damage'].get('enemy_minion', 0)}"]


def main():
    lines = ['# 卡位曝光分层', '', '只统计实际观察与执行，不把“出场局获胜”当作卡牌因果收益。入手/可打/打出按实体计；同名双卡是两张合计。',
             '场次按对局计，因此双卡实体次数可超过场次。伤害仅为该实体直接伤害，恐狼光环、奥秘及误导的间接贡献未归因。',
             '回合以己方自然最大法力标记，硬币可使牌提前使用。完整首次可打与延迟分布保存在每批analysis JSON。']
    headers = ['版本/卡', '层', '胜/局', '起手/换走', '入手/可打/打出', '出场局/其中胜局', '对英雄/随从直接伤害']
    for batch in ('deck-screen', 'coverage-core', 'mechanism-core', 'two-card'):
        path = RUN / 'analysis' / (batch + '.json')
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        lines += ['', '## ' + batch, '', f'原始表：`runs/long-20261114/analysis/{batch}.json`。']
        rows = []
        histograms = []
        for arm, choices in CARDS.items():
            if arm not in data:
                continue
            for card, name in choices:
                rows.append(row(arm, name, '全部', data[arm]['all'], card))
                c = data[arm]['all']['cards'][card]
                histograms.append([arm + '/' + name,
                    ', '.join(f'T{k}:{v}' for k, v in sorted(c['first_playable_mana_turns'].items(), key=lambda x: int(x[0]))) or '—',
                    ', '.join(f'T{k}:{v}' for k, v in sorted(c['play_mana_turns'].items(), key=lambda x: int(x[0]))) or '—'])
        table(lines, headers, rows)
        table(lines, ['版本/卡', '首次可打回合:实体数', '实际使用回合:次数'], histograms)
        for key, title in [('by_actual_first', '实际先后手'), ('by_duration', '对局时长'), ('by_opponent', '对手')]:
            lines += ['', '### ' + title]
            rows = []
            for arm, choices in CARDS.items():
                if arm not in data:
                    continue
                for card, name in choices:
                    for layer, summary in data[arm][key].items():
                        label = ('先手' if layer == 'True' else '后手') if key == 'by_actual_first' else layer
                        rows.append(row(arm, name, label, summary, card))
            table(lines, headers, rows)
    output = ROOT / 'docs/secret_hunter_long/CARD_STATISTICS.md'
    output.write_text('\n'.join(lines) + '\n')
    print(output)


if __name__ == '__main__':
    main()
