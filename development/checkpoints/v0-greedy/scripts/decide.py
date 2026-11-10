"""Stateless CLI: read only the supplied seat view and the bundled deck recipe."""
import argparse
import json
import sys
from pathlib import Path

from actions import fallback, legal

ROOT = Path(__file__).resolve().parents[1]


def response(state, force_fallback=False):
    if state["phase"] == "game_over":
        return {"seq": state["seq"], "game_over": True, "result": state.get("result")}
    if state["phase"] == "deck_submission":
        from hs_arena.deck import load_deck
        deck = load_deck(ROOT / "deck.json")
        action = {"type": "submit_deck", **deck.to_json()}
    else:
        action = None
        if not force_fallback:
            try:
                from policy import decide
                config_path = ROOT / "config.json"
                config = json.loads(config_path.read_text()) if config_path.exists() else {}
                action = decide(state, config)
                if not legal(state, action):
                    raise ValueError("policy returned an action outside the current legal templates")
            except Exception as error:
                print(f"policy fallback: {type(error).__name__}: {error}", file=sys.stderr)
        if action is None or not legal(state, action):
            action = fallback(state)
    return {"seq": state["seq"], "action": action}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("state", nargs="?", default="game/state.json")
    parser.add_argument("--fallback", action="store_true")
    args = parser.parse_args()
    state = json.loads(Path(args.state).read_text(encoding="utf-8"))
    print(json.dumps(response(state, args.fallback), separators=(",", ":")))
