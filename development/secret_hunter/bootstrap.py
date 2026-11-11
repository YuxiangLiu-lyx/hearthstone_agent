"""Freeze authorized inputs before any Secret Hunter experiments."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def files(path):
    path = Path(path)
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(path.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py', '.json', '.md', '.zip')}


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def main():
    from hs_arena.cards import load
    from hs_arena.deck import validate_deck_data
    import hs_arena
    deck = {'name': 'Classic Secret Hunter - BU CS598', 'hero_class': 'HUNTER', 'cards': [
        'EX1_029','EX1_029','EX1_080','EX1_080','DS1_184','EX1_162','EX1_531','EX1_531',
        'EX1_533','EX1_554','EX1_066','EX1_610','EX1_610','EX1_611','EX1_611','NEW1_019',
        'NEW1_019','EX1_536','EX1_536','EX1_538','EX1_538','EX1_539','EX1_539','EX1_617',
        'NEW1_031','NEW1_031','DS1_070','EX1_534','EX1_534','EX1_543']}
    write(ROOT/'secret-hunter-agent/deck.json', deck)
    catalog = load()
    errors = validate_deck_data(deck)
    audit = {'errors': errors, 'cards': [{**catalog[c], 'card_id': c, 'copies': n}
                                       for c,n in Counter(deck['cards']).items()],
             'deck_sha256': sha(ROOT/'secret-hunter-agent/deck.json'),
             'multiset_sha256': hashlib.sha256(json.dumps(sorted(deck['cards'])).encode()).hexdigest()}
    write(ROOT/'docs/secret_hunter/card-audit.json', audit)
    assert not errors, errors
    population = json.loads((ROOT/'development/opponents/zoo-research.json').read_text())
    entries=[]
    for spec in population:
        dependencies = files(ROOT/spec['policy']) if spec.get('policy') else files(ROOT/'development/opponents')
        dependencies.update(files(ROOT/'development/checkpoints/v3-paladin-relay-champion/scripts'))
        if spec['mode']=='official':
            p=Path(hs_arena.__file__).parent/'agents/greedy_bot.py'
            dependencies['installed:hs_arena/agents/greedy_bot.py']=sha(p)
        entries.append({**spec, 'source_head': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                        'deck_data': json.loads((ROOT/spec['deck']).read_text()),
                        'deck_sha256': sha(ROOT/spec['deck']), 'dependencies': dependencies})
    write(ROOT/'docs/secret_hunter/opponent_manifest.json', {
        'population': 'development/opponents/zoo-research.json',
        'population_sha256': sha(ROOT/'development/opponents/zoo-research.json'),
        'reason': 'Latest complete Control Priest validation reused this exact historical 14-opponent pool.',
        'primary': [o['name'] for o in population if o['name']!='official-mage'],
        'base_reported_separately': 'official-mage', 'weighting': 'equal opponent, equal seed and seat',
        'opponents': entries})
    protected={}
    for p in ('submission','control_priest','face_hunter','dist','development/opponents','development/checkpoints'):
        protected.update(files(ROOT/p))
    write(ROOT/'docs/secret_hunter/protected-before.json', protected)
    runtime=Path(hs_arena.__file__).parent
    engine_files={str(p.relative_to(runtime)):sha(p) for p in sorted(runtime.rglob('*'))
                  if p.is_file() and p.suffix in ('.py','.json','.xml')}
    write(ROOT/'docs/secret_hunter/runtime.json', {'version':'0.2.2','installed_files':engine_files,
          'aggregate_sha256':hashlib.sha256(json.dumps(engine_files,sort_keys=True).encode()).hexdigest()})
    print(json.dumps({'deck_valid':True,'unique_cards':len(set(deck['cards'])),'opponents':len(entries)}))


if __name__=='__main__': main()
