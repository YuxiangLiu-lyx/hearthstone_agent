"""Conservative missed-lethal audit of observed end-turn decisions, offline only."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from development.face_hunter.report import observations


def main():
    p = argparse.ArgumentParser()
    p.add_argument("runs", nargs="+")
    p.add_argument("--out", required=True)
    p.add_argument("--all-main", action="store_true", help="Screen lost turns before resource commitments")
    args = p.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"face_hunter/scripts"))
    from lethal_planner import search
    counts, findings = Counter(), []
    for run in args.runs:
        root = Path(run)
        metrics = json.loads((root/"metrics.json").read_text())
        for game in metrics["results"]:
            folder = root/"games"/game["game_id"]
            found_turns = set()
            for row in observations(folder, game["candidate_seat"]):
                state = row["state"]
                if state["phase"] != "main":
                    continue
                if args.all_main:
                    if state["turn"] in found_turns or (game["won"] and game["turns"] == state["turn"]):
                        continue
                elif (row.get("action") or {}).get("type") != "end_turn":
                    continue
                counts["decisions_checked"] += 1
                plan = search(state, budget_s=.3, max_nodes=3200)
                counts["supported"] += plan["supported"]
                counts["bounded_out"] += plan["bounded_out"]
                if plan["guaranteed"]:
                    counts["model_detected_misses"] += 1
                    found_turns.add(state["turn"])
                    findings.append({"run": run, "game": game["game_id"], "seed": game["seed"],
                                     "candidate_seat": game["candidate_seat"], "state": row["state"], "plan": plan})
    scope = "Observed main decisions in turns that did not win; first finding per game/turn" if args.all_main else "Only observed end_turn decisions"
    result = {"scope": scope + "; conservative public tactical model; bounded beam search, not exhaustive. Positive findings require engine replay confirmation before calling them proven misses.",
              "counts": dict(counts), "findings": findings}
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"scope": result["scope"], "counts": result["counts"]}, indent=2))


if __name__ == "__main__":
    main()
