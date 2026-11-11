"""Append frozen candidate provenance and evidence; never promote automatically."""
import argparse,json
from development.secret_hunter_program.common import ROOT,sha,write
from development.benchmarks.run import fingerprint
p=argparse.ArgumentParser();p.add_argument('candidate');p.add_argument('--parent',required=True);p.add_argument('--hypothesis',required=True);p.add_argument('--direction',required=True);a=p.parse_args()
base=ROOT/'development/secret_hunter_next/candidates'/a.candidate;path=ROOT/'docs/secret_hunter_next/candidates.json'
rows=json.loads(path.read_text()) if path.exists() else []
assert a.candidate not in {x['candidate'] for x in rows}
rows.append({'candidate':a.candidate,'parent':a.parent,'direction':a.direction,'hypothesis':a.hypothesis,'source_sha256':fingerprint(base),'config_sha256':sha(base/'config.json'),'deck_sha256':sha(base/'deck.json'),'status':'frozen_development','runs':[]})
write(path,rows)
