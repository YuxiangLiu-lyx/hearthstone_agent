"""Verify complete paired coverage and report the historical 1,120-game suite."""
import argparse
import json
from pathlib import Path

from development.face_hunter.compare import paired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    roots = [Path(args.baseline), Path(args.candidate)]
    configs = [json.loads((root / "config.json").read_text()) for root in roots]
    metrics = [json.loads((root / "metrics.json").read_text()) for root in roots]
    for key in ("population", "population_code_sha256", "opponent_versions", "seeds", "seat_swap"):
        assert configs[0][key] == configs[1][key], key
    population, seeds = configs[0]["population"], configs[0]["seeds"]
    assert len(population) == 14 and len(seeds) == 40
    expected = {(seed, spec["name"], seat) for seed in seeds for spec in population for seat in (1, 2)}
    reliability = []
    for root, metric in zip(roots, metrics):
        assert len(metric["results"]) == metric["attempted"] == metric["games"] == len(expected) == 1120
        actual = {(row["seed"], row["opponent"], row["candidate_seat"]) for row in metric["results"]}
        assert actual == expected
        executions = [json.loads(line) for line in (root / "execution-results.jsonl").read_text().splitlines()]
        assert len(executions) == len({row["game"] for row in executions}) == 1120
        assert not json.loads((root / "execution-errors.json").read_text())
        defects = {
            "candidate_exceptions": sum(len(row["candidate_errors"]) for row in executions),
            "opponent_exceptions": sum(len(row["opponent_errors"]) for row in executions),
            "both_player_illegal_actions": sum(sum(row["result"]["illegal_counts"].values()) for row in executions),
            "both_player_timeouts": sum(sum(row["result"]["timeouts"].values()) for row in executions),
            "forfeits_or_voids": sum(row["result"]["reason"].startswith("forfeit") or row["result"]["reason"] in
                                    ("void_engine_error", "harness_error", "aborted") for row in executions),
        }
        assert not any(defects.values()), (root, defects)
        reliability.append(defects)
    baseline, candidate = metrics
    comparison = paired(candidate["results"], baseline["results"])
    assert comparison["paired_games"] == 1120 and comparison["seed_clusters"] == 40
    result = {"baseline": args.baseline, "candidate": args.candidate,
              "population": configs[0]["population_path"], "seeds": seeds,
              "games_per_arm": 1120, "opponents": 14, "seats": [1, 2],
              "comparison": comparison, "reliability": dict(zip(("original", "v2"), reliability)),
              "arms": {label: {key: value for key, value in metric.items() if key != "results"}
                       for label, metric in zip(("original", "v2"), metrics)}}
    lines = ["# Full Control Priest validation: 1,120 games per arm", "",
             "The earlier final check used five opponents, 30 seeds and two seats (300 games).",
             "The 3,240-game total pooled development and multiple comparison arms; it did not",
             "establish 1,120-game coverage for the final agent. This report closes that gap.", "",
             "Both versions were frozen before fresh seeds 152000–152039. The population,",
             "opponent policies and decks exactly match the historical Zoo 14-opponent suite.",
             "Each opponent receives 40 seeds in both seats, or 80 games per arm. The official",
             "hs-arena 0.2.2 engine executes real games without model calls. The 300-game result",
             "against five stronger/current local opponents remains a separate test population.", "",
             "## Overall results", "",
             "| Agent | Wins / games | Rate | Wilson 95% | Mean turns | Mean hero damage |",
             "|---|---:|---:|---|---:|---:|"]
    for name, metric in zip(("Original opposing Priest", "Frozen final Priest V2"), metrics):
        lo, hi = metric["wilson95"]
        lines.append(f"| {name} | {metric['wins']}/1120 | {metric['win_rate']:.2%} | {lo:.2%}–{hi:.2%} | {metric['mean_turns']:.2f} | {metric['mean_hero_damage']:.2f} |")
    lo, hi = comparison["cluster_bootstrap95"]
    lines += ["", f"Paired V2 improvement: **{comparison['delta']*100:+.2f} percentage points**,",
              f"95% seed-cluster bootstrap interval [{lo*100:+.2f}, {hi*100:+.2f}] points.",
              f"There are {comparison['gains']} paired gains and {comparison['losses']} paired losses.",
              "Bootstrap uses 10,000 whole-seed resamples with analysis seed 598. The interval",
              "describes this fixed local population; it is not a Mystery Bot or Astra estimate.", "",
              "## Every opponent", "",
              "| Opponent | Original wins / 80 | V2 wins / 80 | V2 rate | Change |",
              "|---|---:|---:|---:|---:|"]
    for spec in population:
        name = spec["name"]
        a, b = (metric["by_opponent"][name] for metric in metrics)
        assert a["games"] == b["games"] == 80
        lines.append(f"| {name} | {a['wins']} | {b['wins']} | {b['wins']/80:.2%} | {(b['wins']-a['wins'])/80*100:+.2f} pp |")
    lines += ["", "## Actual first and second player", "",
              "Seat assignment and actual first player are distinct; both seats were tested.", "",
              "| Actual order | Original wins / games | V2 wins / games |",
              "|---|---:|---:|"]
    for key, label in (("True", "First"), ("False", "Second")):
        a, b = (metric["by_first"][key] for metric in metrics)
        lines.append(f"| {label} | {a['wins']}/{a['games']} | {b['wins']}/{b['games']} |")
    lines += ["", "## Reliability, failures and limits", "",
              "Across both complete arms (2,240 games), neither player has a policy exception,",
              "illegal action, timeout, forfeit or engine void. Full schedules and both-player",
              "execution records are checked before producing this report.", "",
              "Final V2 loss signals (overlapping observations, not proven causes):", ""]
    for signal, count in candidate["failure_signals"].items():
        lines.append(f"- {signal}: {count}")
    lines += ["", "Every loss has a concrete public state and chosen action in",
              "`experiments/priest-full-v2-holdout/failure-states.json`; official replays remain",
              "locally in that run's ignored `games/` directory. Direct-lethal priority is",
              "audited separately; no exhaustive zero-missed-lethal claim is made.", "",
              "No card, strategy weight, submitted source or ZIP changed in this extension.",
              "Previous 25 engine tests and real Luna 2–1 / 125 exact relays remain applicable.",
              "The historical suite is broader in styles, while the smaller current pool contains",
              "newer frozen champions. Do not compare their aggregate percentages as a strength",
              "change. Do not directly rank this Priest against historical Zoo percentages from",
              "different seeds; that would require a fresh paired comparison.", "",
              "Acceptance: complete historical coverage and report the frozen result without",
              "retuning. Next hypothesis: improve stabilization against the modern Face Hunter",
              "and test any future change on new development seeds before fresh validation."]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "comparison.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"original_wins": baseline["wins"], "v2_wins": candidate["wins"],
                      "games_per_arm": 1120, "comparison": comparison, "reliability": reliability}, indent=2))


if __name__ == "__main__":
    main()
