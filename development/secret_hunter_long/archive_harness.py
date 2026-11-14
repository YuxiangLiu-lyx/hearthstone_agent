"""Recover dispatched harness versions from git and exact intermediate diffs."""
from collections import defaultdict
import difflib
import hashlib
import json
import subprocess
from development.secret_hunter_long.study import ROOT,RUN
from development.secret_hunter_mcgs.train import atomic

def main():
    wanted=defaultdict(set)
    for kind in ('mulligan','tactical'):
        for p in (RUN/(kind+'-labels')).glob('*.request.json'):
            for name,digest in json.loads(p.read_text()).get('harness_sha256',{}).items():
                name=name if '/' in name else 'development/secret_hunter_long/'+name
                wanted[name].add(digest)
    report={}
    for name,digests in wanted.items():
        remaining={h for h in digests if not (RUN/'harness-by-sha'/(h+'.json')).exists()}
        def save(raw,origin):
            h=hashlib.sha256(raw).hexdigest()
            if h not in remaining:return
            atomic(RUN/'harness-by-sha'/(h+'.json'),{'path':name,'sha256':h,'utf8_source':raw.decode(),'recovered_from':origin})
            remaining.remove(h)
        commits=subprocess.check_output(['git','log','--reverse','--format=%H','--',name],cwd=ROOT,text=True).splitlines()
        versions=[]
        for commit in commits:
            raw=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT);versions.append(raw);save(raw,commit)
        current=(ROOT/name).read_bytes();versions.append(current);save(current,'current working file')
        tried=0
        for left,right in zip(versions,versions[1:]):
            if not remaining:break
            a=left.decode().splitlines(True);b=right.decode().splitlines(True)
            chunks=[];n=0
            for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
                old=''.join(a[i:j]);new=''.join(b[k:l])
                if tag=='equal':chunks.append((None,old,new))
                else:chunks.append((n,old,new));n+=1
            if n>16:continue
            for mask in range(1<<n):
                raw=''.join(new if ix is not None and mask&(1<<ix) else old for ix,old,new in chunks).encode()
                save(raw,'exact SHA match from intermediate independent edits between committed versions');tried+=1
                if not remaining:break
        report[name]={'dispatched_versions':len(digests),'archived':len(digests)-len(remaining),'unresolved_hashes':sorted(remaining),'intermediate_variants_checked':tried}
    atomic(RUN/'harness-history-audit.json',report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
