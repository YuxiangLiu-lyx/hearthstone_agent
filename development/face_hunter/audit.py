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
    args = p.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"face_hunter/scripts"))
    from lethal_planner import search
    counts, findings = Counter(), []
    for run in args.runs:
        root = Path(run)
        metrics = json.loads((root/"metrics.json").read_text())
        for game in metrics["results"]:
            folder = root/"games"/game["game_id"]
            for row in observations(folder, game["candidate_seat"]):
                if (row.get("action") or {}).get("type") != "end_turn":
                    continue
                counts["end_turns"] += 1
                plan = search(row["state"], budget_s=.3, max_nodes=3200)
                counts["supported"] += plan["supported"]
                counts["bounded_out"] += plan["bounded_out"]
                if plan["guaranteed"]:
                    counts["model_detected_end_turn_misses"] += 1
                    findings.append({"run": run, "game": game["game_id"], "seed": game["seed"],
                                     "candidate_seat": game["candidate_seat"], "state": row["state"], "plan": plan})
    result = {"scope": "Only observed end_turn decisions; conservative public tactical model; bounded beam search, not exhaustive. Positive findings require engine replay confirmation before calling them proven misses.",
              "counts": dict(counts), "findings": findings}
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"scope": result["scope"], "counts": result["counts"]}, indent=2))


if __name__ == "__main__":
    main()
