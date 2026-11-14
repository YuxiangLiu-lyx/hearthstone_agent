"""Independent standard-library emergency entry; prints only a protocol envelope."""
import json
from pathlib import Path
from action_validator import fallback
ROOT=Path(__file__).resolve().parents[1]

def basic(state):
    if state['phase']=='game_over':return None
    if state['phase']=='deck_submission':
        deck=json.loads((ROOT/'deck.json').read_text())
        return {'type':'submit_deck','hero_class':deck['hero_class'],'cards':deck['cards']}
    return fallback(state)

def main():
    state=json.loads((ROOT/'game/state.json').read_text())
    action=basic(state)
    print(json.dumps({'seq':state['seq'],'action':action} if action else {'game_over':state['phase']=='game_over'}))
if __name__=='__main__':main()
