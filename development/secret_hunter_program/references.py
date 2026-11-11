"""Fetch public research references outside the submitted skill; no runtime network."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
CACHE=Path('/tmp/secret-hunter-program-references-20261111')


def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Secret-Hunter-Research'})
    with urllib.request.urlopen(req,timeout=30) as response:return response.read()


def repository(repo):
    try:
        meta=json.loads(fetch('https://api.github.com/repos/'+repo))
        commit=json.loads(fetch('https://api.github.com/repos/'+repo+'/commits/'+meta['default_branch']))['sha']
        tree=json.loads(fetch('https://api.github.com/repos/'+repo+'/git/trees/'+commit+'?recursive=1'))['tree']
        paths=[x['path'] for x in tree if x['type']=='blob']
        names=('minisimulator.cs','ai.cs','behaviorface.cs','behaviorcontrol.cs','penalitymanager.cs','rulesengine.cs',
               'parametricgreedyagent.cs','coevolutionary.py','lessons.py','progressive-rag.md')
        selected=[p for p in paths if p.lower().split('/')[-1] in names or p.lower().split('/')[-1] in ('license','license.md','license.txt')]
        if repo.endswith('/HB'):
            selected += [p for p in paths if '/ai/Playfield/' in p and p.endswith('.cs')][:3]
            selected += [p for p in paths if '/behavior/' in p.lower() and ('hunter' in p.lower() or 'face' in p.lower() or '猎' in p)][:4]
        if repo.startswith('ChuckHearthstone'):
            selected=selected[:8]
        items=[]
        for path in sorted(set(selected)):
            url=f'https://raw.githubusercontent.com/{repo}/{commit}/{path}'
            try:
                body=fetch(url);dest=CACHE/repo/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
                items.append({'path':path,'url':url,'local':str(dest),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)})
            except Exception as exc:items.append({'path':path,'error':str(exc)})
        return {'repo':repo,'commit':commit,'license':meta.get('license'),'files':items,
                'selected_tree_paths':selected,'tree_file_count':len(paths)}
    except Exception as exc:return {'repo':repo,'error':str(exc)}


def main():
    CACHE.mkdir(exist_ok=True)
    repos=['noHero123/silverfish','ChuckHearthstone/sliverfishes-silverfish','lijhnihaoa/HB','fergunet/SabberStone','barnabys-drew/hearthstone-ai-coach']
    with ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(repository,repos))
    for name,url in [('course-hw2.md','https://bu-agenticai-class-fall26.vercel.app/materials/assignments/hw2.md'),
                     ('paper.html','https://arxiv.org/html/2410.19681v1')]:
        try:
            body=fetch(url);(CACHE/name).write_bytes(body)
            results.append({'url':url,'local':str(CACHE/name),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)})
        except Exception as exc:results.append({'url':url,'error':str(exc)})
    (ROOT/'docs/secret_hunter_program/reference-fetch.json').write_text(json.dumps(results,indent=2)+'\n')
    for r in results:print(json.dumps({k:v for k,v in r.items() if k not in ('files','all_path_list','selected_tree_paths')}|{'file_count':len(r.get('files',[]))}))


if __name__=='__main__':main()
