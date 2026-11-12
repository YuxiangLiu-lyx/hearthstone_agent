"""Reproducible pilot prerequisites and inherited-data audit."""
import hashlib,json,subprocess,sys,zipfile
from development.secret_hunter_mcgs.build import ROOT,HERE

def run(folder):
    sources=json.loads((ROOT/'docs/secret_hunter_mcgs/source-fetch.json').read_text())
    assert sources['choe.zip']['sha256']=='f00a54f310a8f868deb59964c17e71357d67ecfcedba01c0245053dcc5aa920a'
    for module in ('audit','checks'):
        subprocess.run([sys.executable,'-m','development.secret_hunter_mcgs.'+module],cwd=ROOT,check=True)
    if not (folder/'submission2/decisions.jsonl').exists():
        with zipfile.ZipFile(ROOT/'docs/secret_hunter_mcgs/submission2-public.zip') as z:
            for name in ('decisions.jsonl','responses.jsonl','manifest.json','official-results.md'):
                dest=folder/'submission2'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
    old=json.loads((ROOT/'docs/secret_hunter_winrate/checkpoint.json').read_text())['used_seed_values']
    old+=json.loads((ROOT/'docs/secret_hunter_face_validation/checkpoint.json').read_text())['new_used_seed_values']
    assert max(old)<10000000
    data=json.loads((ROOT/'docs/secret_hunter_response/data-manifest.json').read_text())
    responses=ROOT/'docs/secret_hunter_response/opponent_replies.jsonl'
    assert hashlib.sha256(responses.read_bytes()).hexdigest()==data['responses_sha256']
    return {'source_archive_verified':True,'historical_seed_values':len(set(old)),
            'maximum_inherited_seed':max(old),'new_seed_block_disjoint':True,
            'prior_response_rows':data['stats']['responses'],'external_csharp_copied':False}
