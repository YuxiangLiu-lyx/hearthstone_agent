"""Paired comparisons with seed-cluster resampling; never select on holdout."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import statistics

from development.benchmarks.run import wilson


def paired(left, right):
    key = lambda r: (r["seed"], r["opponent"], r["candidate_seat"])
    a, b = ({key(r): r for r in rows} for rows in (left, right))
    keys = sorted(a.keys() & b.keys())
    clusters = defaultdict(list)
    for k in keys:
        clusters[k[0]].append(int(a[k]["won"]) - int(b[k]["won"]))
    units = [statistics.mean(v) for v in clusters.values()]
    rng = random.Random(598)
    samples = sorted(statistics.mean(rng.choices(units, k=len(units))) for _ in range(10000))
    return {"paired_games": len(keys), "seed_clusters": len(units),
            "delta": statistics.mean(units), "cluster_bootstrap95": [samples[249], samples[9749]],
            "gains": sum(a[k]["won"] and not b[k]["won"] for k in keys),
            "losses": sum(b[k]["won"] and not a[k]["won"] for k in keys)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--arm", action="append", required=True, help="LABEL=directory,directory")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    result, all_rows = {"arms": {}, "comparisons": {}}, {}
    lines = ["# Paired strategy comparison", "",
             "Wilson intervals describe the sampled opponent mixture. Paired differences use",
             "10,000 bootstrap draws of whole seed clusters (analysis RNG seed 598).",
             "These exploratory intervals do not adjust for sequential selection or multiple comparisons.", "",
             "| Arm | Wins | Rate | Wilson 95% | Mean turns | Mean hero damage | Policy errors |",
             "|---|---:|---:|---|---:|---:|---:|"]
    for spec in args.arm:
        label, paths = spec.split("=", 1)
        metrics = [json.loads((Path(path) / "metrics.json").read_text()) for path in paths.split(",")]
        rows = [r for m in metrics for r in m["results"]]
        assert len({(r["seed"], r["opponent"], r["candidate_seat"]) for r in rows}) == len(rows)
        all_rows[label] = rows
        wins, n = sum(r["won"] for r in rows), len(rows)
        lo, hi = wilson(wins, n)
        summary = {"sources": paths.split(","), "wins": wins, "games": n, "win_rate": wins/n,
                   "wilson95": [lo, hi], "mean_turns": statistics.mean(r["turns"] for r in rows),
                   "mean_hero_damage": statistics.mean(r["hero_damage"] for r in rows),
                   **{k: sum(m[k] for m in metrics) for k in ("policy_errors", "illegal", "timeouts", "early_exits")}}
        result["arms"][label] = summary
        lines.append(f"| {label} | {wins}/{n} | {wins/n:.1%} | {lo:.1%}–{hi:.1%} | {summary['mean_turns']:.2f} | {summary['mean_hero_damage']:.2f} | {summary['policy_errors']} |")
    lines += ["", "| Difference | Paired games | Change | Cluster 95% | Gains / losses |",
              "|---|---:|---:|---|---:|"]
    labels = list(all_rows)
    for i, left in enumerate(labels):
        for right in labels[:i]:
            stats = paired(all_rows[left], all_rows[right])
            result["comparisons"][f"{left}-{right}"] = stats
            lo, hi = stats["cluster_bootstrap95"]
            lines.append(f"| {left} − {right} | {stats['paired_games']} | {100*stats['delta']:+.1f} pp | {100*lo:+.1f} to {100*hi:+.1f} pp | {stats['gains']} / {stats['losses']} |")
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out/"comparison.json").write_text(json.dumps(result, indent=2)+"\n")
    (out/"comparison.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
