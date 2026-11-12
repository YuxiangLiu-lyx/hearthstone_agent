"""Create isolated response-search arms without altering the frozen Y1 parent."""
import json,shutil
from development.secret_hunter_program.common import ROOT,write
from development.benchmarks.run import fingerprint
D=ROOT/'docs/secret_hunter_response';W=ROOT/'development/secret_hunter_response'
def main():
 archive=json.loads((D/'candidates.json').read_text())
 for name,hidden in [('B1',False),('C1',True)]:
  dest=W/'candidates'/name
  shutil.copytree(W/'candidates/Y1',dest,ignore=shutil.ignore_patterns('__pycache__','scratch'))
  cfg=json.loads((dest/'config.json').read_text());cfg.update(version='response-'+name,parent='Y1',response_search=True,response_hypotheses=hidden,response_budget_s=.30,response_candidates=5,response_nodes=240,response_margin=1.0)
  write(dest/'config.json',cfg)
  p=dest/'scripts/program_policy.py';s=p.read_text();old="    except Exception as exc:\n";insert="""                if config.get('response_search') and time.monotonic()<deadline:
                    from response_search import plan as response_plan
                    response=response_plan(state,ranked,best,config,deadline)
                    info['response']=response;info['nodes']+=response.get('nodes',0)
                    if response.get('action'):
                        save(response['action'],'public_response_endpoint');info['search_used']=True
""";assert old in s;s=s.replace(old,insert+old);p.write_text(s)
  p=dest/'scripts/state_features.py';s=p.read_text();s=s.replace("'face_attacks':face,","'shown_card_counts':{cid:sum(e.get('card_id')==cid for e in shown) for cid in {e['card_id'] for e in shown}},\n           'face_attacks':face,");p.write_text(s)
  archive[name]={'parent_ids':['Y1'],'status':'provisional','hypothesis':('End both public turns, retain distinct complete-turn endpoints and explicitly search the known-hand next turn.' if not hidden else 'Same candidate generator and budget as B1, with small public-compatible response scenarios; no learned coefficients.'),'source_sha256':fingerprint(dest)}
 write(D/'candidates.json',archive)
if __name__=='__main__':main()
