"""Verify exact frozen artifacts, or create an isolated ledger for replication."""
import argparse,importlib.metadata,json,os,shlex,shutil,tempfile,time
from pathlib import Path
from zipfile import ZipFile

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-run',type=Path,required=True);p.add_argument('--run',type=Path);p.add_argument('--verify-only',action='store_true');a=p.parse_args()
 source=a.source_run.resolve()
 if not a.verify_only:
  assert a.run,'Provide a new --run directory';destination=a.run.resolve()
  assert not destination.exists() and destination!=source and not destination.is_relative_to(source)
  os.environ['HUNTER_SPRINT_RUN']=str(destination)
 import hs_arena
 from development.secret_hunter_astra_sprint.study import ROOT,RUN,initialize,register,check
 from development.secret_hunter_astra_sprint.build import audit
 from development.secret_hunter_astra_sprint.cfqueue import connect
 from development.secret_hunter_astra_sprint import ledger
 from development.secret_hunter_program.common import sha
 from development.benchmarks.run import fingerprint
 old=json.loads((source/'manifest.json').read_text());freeze=json.loads((source/'final-freeze.json').read_text());records=json.loads((source/'release-candidates.json').read_text())
 assert [r['name'] for r in records]==freeze['arms']
 assert all(importlib.metadata.version(k)==v for k,v in old['versions'].items())
 assert all(sha(ROOT/path)==h for path,h in old['protected'].items())
 engine_root=Path(hs_arena.__file__).parent;expected={}
 for path,h in old['engine'].items():
  parts=Path(path).parts;expected[str(Path(*parts[parts.index('hs_arena')+1:]))]=h
 actual={str(p.relative_to(engine_root)):sha(p) for p in engine_root.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.xml','.txt')}
 assert actual==expected,'Course engine/resources differ'
 assert all(sha(ROOT/path)==h for path,h in freeze['analysis_sources'].items()),'Frozen statistical/release code differs'
 with tempfile.TemporaryDirectory(prefix='astra-frozen-reproduction-') as tmp:
  validated=[]
  for record in records:
   arm=record['name'];package=source/'frozen'/(arm+'.zip');assert sha(package)==record['zip_sha256']
   extract=Path(tmp)/arm
   with ZipFile(package) as z:
    members=z.infolist();assert {m.filename.split('/')[0] for m in members}=={'secret-hunter'}
    assert all(not m.filename.startswith('/') and '..' not in Path(m.filename).parts for m in members)
    assert sum(m.file_size for m in members)<=10_000_000 and package.stat().st_size<=10_000_000
    z.extractall(extract)
   exact=extract/'secret-hunter';assert fingerprint(exact)==freeze['fingerprints'][arm]
   validated.append((record,package,extract,audit(exact)))
  if a.verify_only:
   print(json.dumps({'verified':True,'arms':freeze['arms'],'engine_resources':len(actual),'seeds':freeze['seeds'],'ledger_created':False},indent=2));return
  assert RUN.is_relative_to(ROOT) and not RUN.exists()
  RUN.mkdir(parents=True);started=time.time();ledger.atomic(RUN/'start.json',{'started_utc':started,'deadline':started+36000,'purpose':'Replication of seen frozen source groups; not new holdout or strategy development.'})
  db=connect();db.execute('CREATE TABLE IF NOT EXISTS auxiliary_games (key TEXT PRIMARY KEY,status TEXT,started REAL,finished REAL,result TEXT)');db.commit()
  initialize(db);candidates=register(db);manifest=ledger.meta(db,'manifest')
  for key,bounds in freeze['seeds'].items():manifest['seed_blocks'][key]=bounds
  core=freeze['seeds']['final_core'];guard=freeze['seeds']['final_guard'];nc=core[1]-core[0]+1;ng=guard[1]-guard[0]+1
  manifest['final_target']={'per_arm_core':12*nc,'per_arm_guard':28*ng,'seeds_core':nc,'seeds_guard':ng}
  manifest['reproduction']={'source_run':str(source),'original_freeze_sha256':sha(source/'final-freeze.json'),'original_manifest_sha256':sha(source/'manifest.json'),'engine_paths_relocated_by_verified_relative_hashes':True}
  check(manifest);ledger.atomic(RUN/'manifest.json',manifest);ledger.setmeta(db,'manifest',manifest)
  new_records=[]
  for record,package,extract,validation in validated:
   arm=record['name'];(RUN/'frozen').mkdir(exist_ok=True);new_zip=RUN/'frozen'/package.name;shutil.copy2(package,new_zip);shutil.copytree(extract,RUN/'frozen'/arm)
   exact=RUN/'frozen'/arm/'secret-hunter';candidates[arm]['path']=str(exact.relative_to(ROOT))
   new_records.append({**record,'path':str(new_zip.relative_to(ROOT)),'extracted':str(exact.relative_to(ROOT)),'deck_audit':validation})
  ledger.setmeta(db,'candidates',candidates);ledger.setmeta(db,'selection_opened',True);ledger.setmeta(db,'selected_challenger',freeze['arms'][-1]);ledger.atomic(RUN/'release-candidates.json',new_records)
  ledger.atomic(RUN/'original-final-freeze.json',freeze)
  relocated={**freeze,'manifest_sha256':sha(RUN/'manifest.json'),'release_records':new_records,'release_records_sha256':sha(RUN/'release-candidates.json'),'reproduction':manifest['reproduction']}
  ledger.atomic(RUN/'final-freeze.json',relocated)
  for name in ('selection-plan.json','final-acceptance-plan.json','runtime-stress-cases.json'):
   if (source/name).exists():shutil.copy2(source/name,RUN/name)
  shutil.copytree(source/'tactical-sources',RUN/'tactical-sources')
  commands=[]
  for pool,key,batch in [('core','final_core','final-core'),('guardrail','final_guard','final-guard')]:
   lo,hi=freeze['seeds'][key]
   commands.append(['env','HUNTER_SPRINT_RUN='+str(RUN),'.venv/bin/python','-m','development.secret_hunter_astra_sprint.study','run','--batch',batch,'--arms',*freeze['arms'],'--start',str(lo),'--seeds',str(hi-lo+1),'--pool',pool,'--workers',str(freeze['workers']),'--final'])
   if freeze.get('interleave_arms'):commands[-1].append('--interleave-arms')
  record={'created':time.time(),'new_run':str(RUN),**manifest['reproduction'],'arms':freeze['arms'],'commands':commands,'scope':'Original frozen comparison reproduced; all source groups are already seen. Finish both pools before report.'}
  ledger.atomic(RUN/'reproduction.json',record);db.close();print(json.dumps(record,indent=2));print('\n'.join(shlex.join(c) for c in commands))
if __name__=='__main__':main()
