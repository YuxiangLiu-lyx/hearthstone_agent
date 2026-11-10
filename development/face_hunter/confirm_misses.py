"""Reconstruct recorded games offline and validate screened lethals in the official engine.

Hidden deck recipes are used only to reconstruct the completed experiment. The planner
receives exactly the public seat observation; this tool is never included in the skill.
"""
import argparse
import json
from pathlib import Path
import sys

from hs_arena.agents.greedy_bot import GreedyBot
from hs_arena.deck import Deck
from hs_arena.engine import Engine
from development.face_hunter.report import observations


def confirm(finding):
    from lethal_planner import search
    root = Path(finding["run"])/"games"/finding["game"]
    metadata = json.loads((root/"game.json").read_text())
    decks = [Deck(p["hero_class"], tuple(p["deck"])) for p in metadata["players"]]
    engine = Engine(*decks, finding["seed"], max_turns=180)
    hunter = finding["candidate_seat"]
    rows = {i: observations(root, i) for i in (1, 2)}
    offsets = {1: 0, 2: 0}
    greedy = GreedyBot("reconstruction", decks[2-hunter])
    actual_line = []
    for _ in range(1000):
        seat, _ = engine.pending()
        view = engine.view(seat)
        if rows[seat]:
            row = rows[seat][offsets[seat]]; offsets[seat] += 1
            for key in ("phase", "turn", "you", "opponent", "legal_actions"):
                assert row["state"][key] == view[key], f"Reconstruction diverged at {key}"
            if seat == hunter and row["state"]["seq"] == finding["state"]["seq"]:
                unused_attack = finding["state"].get("hero_attack_available", False)
                for _ in range(25):
                    public = engine.view(hunter)
                    public["hero_attack_available"] = unused_attack
                    plan = search(public, budget_s=1, max_nodes=10000, beam_width=64)
                    if not plan["guaranteed"]:
                        return {"confirmed": False, "reason": "Continuation not found within verification budget", "actions": actual_line}
                    action = plan["first_action"]
                    if action["type"] == "attack" and action["attacker"] == public["you"]["hero"]["entity_id"]:
                        unused_attack = False
                    result = engine.step(hunter, action)
                    assert result.accepted, result
                    actual_line.append(action)
                    if engine.over:
                        return {"confirmed": engine.winner == hunter, "winner": engine.winner, "actions": actual_line}
                return {"confirmed": False, "reason": "Verification action limit", "actions": actual_line}
            action = row["action"]
        else:
            assert metadata["players"][seat-1]["kind"] == "greedy"
            action = greedy.decide(view).action
        assert engine.step(seat, action).accepted
    raise RuntimeError("Reconstruction action limit")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("audit"); p.add_argument("--out", required=True)
    args = p.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"face_hunter/scripts"))
    source = json.loads(Path(args.audit).read_text())
    results = []
    for finding in source["findings"]:
        try:
            check = confirm(finding)
        except Exception as error:
            check = {"confirmed": False, "error": str(error)}
        results.append({"run": finding["run"], "game": finding["game"], "seq": finding["state"]["seq"],
                        "turn": finding["state"]["turn"], **check})
    output = {"audit": args.audit, "candidates": len(results), "confirmed": sum(r["confirmed"] for r in results),
              "scope": "Engine-confirmed alternatives at public observations; non-exhaustive missed-lethal lower bound, one per game/turn.", "results": results}
    Path(args.out).write_text(json.dumps(output, indent=2)+"\n")
    print(json.dumps({k:v for k,v in output.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
