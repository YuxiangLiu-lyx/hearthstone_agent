"""Load the existing lineage, protected files and seed reservations without resetting."""
import json
from development.secret_hunter_program.common import ROOT,sha
from development.benchmarks.run import fingerprint
D=ROOT/'docs/secret_hunter_response'
def main():
 state=json.loads((D/'checkpoint.json').read_text())
 for name,digest in json.loads((D/'protected.json').read_text()).items():assert sha(ROOT/name)==digest,name
 for arm,digest in state['candidate_hashes'].items():assert fingerprint(ROOT/'development/secret_hunter_response/candidates'/arm)==digest,arm
 b=json.loads((D/'budget.json').read_text());print(json.dumps({'candidate_status':state['candidate_status'],'used_and_reserved_seed_count':len(state['used_seed_values']),'full_charged':sum(r['full'] for r in b['runs']),'short_charged':sum(r['short'] for r in b['runs']),'open_reservations':[r['name'] for r in b['runs'] if r['status']=='reserved'],'final_opened':state['final_opened'],'next':'Read REPORT.md, failure-diagnostics.json and checkpoint.json. A new Codex research round must propose changes and pre-register new final seeds; this scheduler does not generate policies autonomously.'},indent=2))
if __name__=='__main__':main()
