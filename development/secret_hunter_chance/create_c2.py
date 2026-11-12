"""Response-aware ablation of chance endpoint scoring; preserve C1 unchanged."""
import shutil,json
from pathlib import Path
root=Path('development/secret_hunter_chance/candidates')
shutil.copytree(root/'C1',root/'C2',ignore=shutil.ignore_patterns('__pycache__'))
p=root/'C2/scripts/chance_search.py';s=p.read_text()
s=s.replace('def evaluate(s, action, cfg, deadline, report):', '''class UnsupportedResponse(Exception):
    pass


def score_endpoint(endpoint, before, cfg, deadline, report):
    if min(endpoint[k]['hero']['health'] for k in ('you','opponent'))<=0:
        return utility(endpoint,cfg)
    from public_response import worst_reply
    reply=worst_reply(endpoint,cfg,deadline,16)
    report['nodes']+=reply['nodes']
    report['reply_bounded']=report.get('reply_bounded',0)+int(reply.get('bounded',False))
    if time.monotonic()>=deadline:raise TimeoutError
    if not reply['supported']:raise UnsupportedResponse
    after=max(-200.0,min(200.0,reply['value']))
    if reply['visible_lethal_found']:after=-200.0
    return .15*before+.85*after


def evaluate(s, action, cfg, deadline, report):''')
s=s.replace("else:v,endpoint=continuation(child,cfg,deadline,report)\n", "else:v,endpoint=continuation(child,cfg,deadline,report)\n        v=score_endpoint(endpoint,v,cfg,deadline,report)\n")
s=s.replace("expected=sum(p*continuation(x,cfg,deadline,report,cap=16)[0] for p,x in d['outcomes'])", "expected=0.0\n                for p,x in d['outcomes']:\n                    before,end=continuation(x,cfg,deadline,report,cap=16)\n                    expected+=p*score_endpoint(end,before,cfg,deadline,report)")
s=s.replace("    except TimeoutError:", "    except UnsupportedResponse:\n        report['complete']=False;report['reason']='unsupported_visible_response';report.pop('action',None)\n    except TimeoutError:")
p.write_text(s)
p=root/'C2/config.json';cfg=json.loads(p.read_text());cfg['chance_budget_s']=.55;p.write_text(json.dumps(cfg,indent=2)+'\n')
