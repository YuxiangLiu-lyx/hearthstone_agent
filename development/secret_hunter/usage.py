"""Aggregate observed model work without pooling incompatible quality scores."""
from collections import Counter
import json
from development.secret_hunter.audit import skill_report
from development.secret_hunter.bootstrap import ROOT,write


def main():
    ledger=json.loads((ROOT/'docs/secret_hunter/budget.json').read_text())
    assert ledger['outstanding_reserved']['skill']==0,'Model schedules still active'
    rows=[];usage=Counter();counts=Counter()
    for run in ledger['runs']:
        if run['mode']!='skill':continue
        report=skill_report(ROOT/run['out']);tokens=Counter()
        for a in report['audits']:tokens.update(a['usage'])
        fields=('games','decisions','model_choices','selection_requests','actual_tool_commands','mcp_calls','deep_requests')
        item={'run':run['out'],**{k:report[k] for k in fields},'host_reported_tokens':dict(tokens),
              'game_wall_s_sum':run['game_wall_s_sum']}
        rows.append(item);usage.update(tokens);counts.update({k:report[k] for k in fields})
    assert counts['games']==ledger['completed_totals']['skill']
    result={'totals':dict(counts),'host_reported_tokens':dict(usage),'runs':rows,
            'api_request_count':None,'monetary_cost_usd':None,
            'limitations':['Official CLI does not expose exact model API request count or monetary cost.',
                           'Input includes repeated cached context, not unique tokens.',
                           'Game wall seconds are summed across parallel matches, not elapsed calendar time.',
                           'Quality scores are not pooled across versions, development, confirmation and injected faults.']}
    write(ROOT/'docs/secret_hunter/total-model-usage.json',result)
    lines=['# Observed model work','','No pooled quality win rate is computed across these different purposes and versions.','',
           '| Run | Games | Actions | Shell commands | MCP calls | Summed game seconds |',
           '|---|---:|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['run']} | {r['games']} | {r['decisions']} | {r['actual_tool_commands']} | {r['mcp_calls']} | {r['game_wall_s_sum']:.1f} |")
    lines+=['',f"Totals: `{json.dumps(dict(counts),sort_keys=True)}`.",
            f"Host-reported tokens: `{json.dumps(dict(usage),sort_keys=True)}`.",'',
            'Exact model API request count and dollar cost are not exposed by the official CLI.',
            'Cached input is included in input usage; input tokens are not unique context tokens.',
            'Summed durations include parallel work and are not calendar elapsed time.',
            'No extra paid service was provisioned. See [machine-readable totals](total-model-usage.json).']
    (ROOT/'docs/secret_hunter/USAGE.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'totals':dict(counts),'host_reported_tokens':dict(usage)}))


if __name__=='__main__':main()
