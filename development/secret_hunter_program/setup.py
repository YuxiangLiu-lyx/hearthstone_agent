"""Freeze the program-only research contract before any comparisons."""
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 d=ROOT/'docs/secret_hunter_program';root=ROOT/'secret-hunter-program';root.mkdir(exist_ok=False);(root/'scripts').mkdir()
 for name in ['base_policy','actions','evaluator','state_features','secret_policy','action_validator','lethal_planner','tactical_model','next_turn']:
  shutil.copy2(ROOT/f'secret-hunter-agent/scripts/{name}.py',root/f'scripts/{name}.py')
 shutil.copy2(ROOT/'secret-hunter-agent/deck.json',root/'deck.json')
 cfg={'version':'P0-program-baseline','parent':'C5-default-Python','guide_rules':True,'risk_summaries':True,'search_budget_s':0.15,'search_nodes':1600,'scoring':False,'turn_search':False,'secret_rules':False,'total_budget_s':2.0,'search_soft_s':1.5}
 write(root/'config.json',cfg)
 for name in ('opponent_manifest.json','runtime.json'):shutil.copy2(ROOT/'docs/secret_hunter'/name,d/name)
 splits={'development':{'start':73000,'seeds':6},'validation':{'start':73500,'seeds':10},'confirmation':{'start':173000,'seeds':30},'smoke':{'start':273000,'seeds':2},'seats':[1,2],'pairing':['opponent','seed','seat'],'note':'Same seed does not imply identical later draws or random events after policies diverge. Old holdouts are development data.'}
 write(d/'splits.json',splits)
 write(d/'budget.json',{'started_utc':'2026-11-11T05:54:40+00:00','deadline_utc':'2026-11-11T09:54:40+00:00','limits':{'full_games':6000,'short_continuations':20000,'wall_seconds':14400},'reserved_final_games':1680,'runs':[],'short_continuations':[]})
 protected={str(p.relative_to(ROOT)):digest(p) for folder in ('secret-hunter-agent','development/secret_hunter','docs/secret_hunter','dist') for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 write(d/'protected-before.json',protected)
 write(d/'freeze.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'deck_sha256':digest(root/'deck.json'),'opponent_manifest_sha256':digest(d/'opponent_manifest.json'),'runtime_sha256':digest(d/'runtime.json'),'baseline_policy_parent':'Existing C5 default action; model selection removed. Baseline and all candidates use the exact fixed deck.','splits_sha256':digest(d/'splits.json')})
 print('Frozen',len(protected),'protected files')
if __name__=='__main__':main()
