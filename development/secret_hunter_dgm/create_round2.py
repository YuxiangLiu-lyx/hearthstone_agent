"""Follow coverage and negative first-round evidence without editing ancestors."""
import json,shutil
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_dgm.create_round1 import child,W,D
from development.secret_hunter_dgm.deck_guard import check

def main():
 c=child('C2','C1','One unsupported alternative response must not discard already comparable roots; unsupported baseline still blocks override.')
 p=c/'scripts/chance_search.py';s=p.read_text();s=s.replace("            result=evaluate(initial,a,cfg,deadline,report)","            try:\n                result=evaluate(initial,a,cfg,deadline,report)\n            except UnsupportedResponse:\n                report['excluded_response_roots']=report.get('excluded_response_roots',0)+1\n                continue")
 p.write_text(s)
 e=child('E1','K1','Revive archived M2 opaque enemy draw and enemy-only Mage body coverage with the original deck; test local ability without claiming inherited win gain.')
 shutil.copyfile(ROOT/'development/secret_hunter_next/candidates/M2/scripts/tactical_model.py',e/'scripts/tactical_model.py')
 s1=child('S1','C2','Choose among three own-turn endpoints after public visible responses, instead of responding only to the single best raw endpoint.')
 p=s1/'scripts/chance_search.py';s=p.read_text().replace("    best = (utility(s,cfg), s); frontier", "    best = (utility(s,cfg), s); shortlist=[best]\n    def finish():\n        scored=[]\n        for raw,end in shortlist:\n            try:scored.append((score_endpoint(end,raw,cfg,deadline,report),raw,end))\n            except UnsupportedResponse:continue\n        if not scored:raise UnsupportedResponse\n        _,raw,end=max(scored,key=lambda x:x[0])\n        return raw,end\n    frontier")
 s=s.replace('                    return best','                    return finish()').replace('    return best\n','    return finish()\n')
 s=s.replace("                if v > best[0]:best = (v,child)","                if v > best[0]:best = (v,child)\n                shortlist.append((v,child));shortlist.sort(key=lambda x:x[0],reverse=True);del shortlist[3:]")
 p.write_text(s)
 for n in ('C2','E1','S1'):check(W/n)
if __name__=='__main__':main()
