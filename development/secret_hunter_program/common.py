"""Small artifact helpers for reproducible program-only research."""
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')
def readlines(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()] if Path(path).exists() else []
def quantiles(xs):
    if not xs:return {'n':0}
    s=sorted(xs)
    return {'n':len(s),'mean':statistics.mean(s),'max':s[-1],**{f'p{int(q*100)}':s[min(len(s)-1,math.ceil(q*len(s))-1)] for q in (.5,.95,.99)}}
