"""Audit recorded Priest decisions and inherited lethal priority, without replay guessing."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from development.face_hunter.report import observations


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run"); p.add_argument("--out", required=True)
    args = p.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"control_priest/scripts"))
    import base_policy
    root = Path(args.run)
    metrics = json.loads((root/"metrics.json").read_text())
    config = json.loads((root/"config.json").read_text())["config"]
    counters, cards, examples = Counter(), Counter(), {}
    differences = []
    for game in metrics["results"]:
        rows = observations(root/"games"/game["game_id"], game["candidate_seat"])
        reduced = {}
        for index, row in enumerate(rows):
            s, a = row["state"], row["action"]
            if s["phase"] != "main":
                continue
            counters["main_decisions"] += 1
            expected = base_policy.rank_actions(s, config)[0]
            if expected[0] >= 100000:
                counters["inherited_immediate_lethals"] += 1
                if a != expected[1]:
                    differences.append({"game": game["game_id"], "seq": s["seq"], "expected": expected[1], "actual": a})
            if a["type"] != "play_card":
                continue
            c = next(c for c in s["you"]["hand"] if c["entity_id"] == a["card"])
            cid = c["card_id"]; cards[cid] += 1
            if cid == "EX1_196":
                reduced[a.get("target")] = s["turn"]
            after = rows[index+1]["state"] if index+1 < len(rows) else None
            if cid in ("EX1_091", "CS1_113", "EX1_334") and a.get("target") and after and after["turn"] == s["turn"]:
                acquired = any(m["entity_id"] == a["target"] for m in after["you"]["board"])
                if acquired:
                    label = "temporary_steals" if cid == "EX1_334" else "permanent_steals"
                    counters[label] += 1
                    examples.setdefault(label, {"game": game["game_id"], "seq": s["seq"], "before": s, "action": a, "after": after})
                    if cid == "EX1_091" and reduced.get(a["target"]) == s["turn"]:
                        counters["scarlet_then_cabal"] += 1
                        examples.setdefault("scarlet_then_cabal", {"game": game["game_id"], "seq": s["seq"], "before": s, "action": a, "after": after})
    result = {"run": args.run, "counts": dict(counters), "played_cards": dict(cards),
              "lethal_priority_differences": differences,
              "scope": "Observed actions and adjacent public states only. This verifies inherited direct-lethal priority, not exhaustive missed-lethal absence. Steals without a following same-turn observation are not counted.",
              "examples": examples}
    Path(args.out).write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("examples", "played_cards")}, indent=2))
    assert not differences


if __name__ == "__main__":
    main()
