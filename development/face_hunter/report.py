"""Summarize real official-runner games, preserving concrete failure observations."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

from development.benchmarks.run import fingerprint, wilson


def observations(folder, seat):
    log = folder / f"p{seat}/observations.jsonl"
    if log.exists():
        return [json.loads(line) for line in log.read_text().splitlines()]
    rows = []
    for p in sorted((folder / f"p{seat}/decisions").glob("*.state.json")):
        state = json.loads(p.read_text())
        action_path = p.with_name(p.name.replace(".state.json", ".action.json"))
        action = json.loads(action_path.read_text())["action"] if action_path.exists() else None
        rows.append({"state": state, "action": action})
    return rows


def summarize(out, config):
    out = Path(out)
    games, failure_rows, timings = [], [], []
    modes = Counter()
    policy_errors = []
    cli_fallbacks = 0
    for result_path in sorted((out / "games").glob("*/result.json")):
        folder = result_path.parent
        result = json.loads(result_path.read_text())
        setup = json.loads((folder / "game.json").read_text())
        seat = config.get("candidate_seat", int(folder.name[-1]) if folder.name.endswith(("p1", "p2")) else 1)
        rows = observations(folder, seat)
        stderr = folder / f"p{seat}/stderr.log"
        if stderr.exists():
            cli_fallbacks += sum('policy fallback:' in line or 'bounded worker fallback:' in line for line in stderr.read_text(errors='replace').splitlines())
        seen = set()
        for row in rows:
            if row.get("policy_error"):
                policy_errors.append({"game":folder.name,"seq":row["state"].get("seq"),"error":row["policy_error"]})
            if row.get("decision_info"):
                modes[row["decision_info"].get("mode","unknown")] += 1
            own = row["state"].get("you")
            if own:
                for c in own["hand"] + own["board"] + [own["hero"], own.get("hero_power"), own.get("weapon")]:
                    if c: seen.add(c["entity_id"])
            if "elapsed_s" in row: timings.append(row["elapsed_s"])
        events = [json.loads(line) for line in (folder / "replay.jsonl").read_text().splitlines()]
        damage = sum(e["amount"] for e in events if e["event"] == "damage" and e["player"] == 3-seat
                     and str(e.get("card_id", "")).startswith("HERO_")
                     and (e.get("source") or {}).get("entity_id") in seen)
        opponent = next(p["name"] for p in setup["players"] if p["index"] == 3-seat)
        phases = Counter(r["state"]["phase"] for r in rows)
        item = {"game_id": result["game_id"], "seed": result["seed"], "candidate_seat": seat,
                "candidate_first": result["first_player"] == seat, "opponent": opponent,
                "winner": result["winner"], "won": result["winner"] == seat,
                "reason": result["reason"], "turns": result["turns"], "hero_damage": damage,
                "illegal": result["illegal_counts"][str(seat)], "timeouts": result["timeouts"][str(seat)],
                "early_exit": result["reason"] == "forfeit_exit" and result["winner"] != seat,
                "phases": dict(phases), "replay": str(folder / "replay.jsonl")}
        games.append(item)
        if not item["won"]:
            main = [r for r in rows if r["state"]["phase"] == "main"]
            if main:
                row = main[-1]; s = row["state"]
                tags = []
                if len(s["you"]["hand"]) <= 1: tags.append("low_hand_resources")
                if any(m.get("taunt") for m in s["opponent"]["board"]): tags.append("opposing_taunt")
                if sum(m["attack"] for m in s["opponent"]["board"]) >= s["you"]["hero"]["health"] + s["you"]["hero"].get("armor", 0): tags.append("visible_board_lethal_threat")
                if not tags: tags.append("race_or_board_loss")
                failure_rows.append({**item, "signals": tags, "key_state": s, "action": row["action"]})
    valid = [g for g in games if g["reason"] not in ("void_engine_error", "aborted")]
    wins = sum(g["won"] for g in valid)
    groups = defaultdict(list)
    for g in valid: groups[g["opponent"]].append(g)
    metrics = {"version": config["version"], "attempted": len(games), "games": len(valid), "wins": wins,
               "win_rate": wins/len(valid) if valid else None, "wilson95": wilson(wins, len(valid)),
               "mean_turns": statistics.mean(g["turns"] for g in valid) if valid else None,
               "mean_hero_damage": statistics.mean(g["hero_damage"] for g in valid) if valid else None,
               "hero_damage_definition": "Damage events to the opposing hero with an observed friendly source, including armor damage and overkill.",
               "illegal": sum(g["illegal"] for g in games), "timeouts": sum(g["timeouts"] for g in games),
               "early_exits": sum(g["early_exit"] for g in games), "void_or_aborted": len(games)-len(valid),
               "policy_errors":len(policy_errors), "decision_modes":dict(modes),
               "cli_fallbacks":cli_fallbacks,
               "missed_lethals": None, "lethal_audit_status": "Not audited; no zero-miss claim.",
               "decision_s_mean": statistics.mean(timings) if timings else None, "decision_s_max": max(timings, default=None),
               "failure_signals": dict(Counter(tag for f in failure_rows for tag in f["signals"])),
               "by_opponent": {k:{"games":len(v), "wins":sum(g["won"] for g in v)} for k,v in groups.items()},
               "by_first": {str(first):{"games":sum(g["candidate_first"] == first for g in valid),
                                       "wins":sum(g["won"] and g["candidate_first"] == first for g in valid)} for first in (True, False)},
               "results": games}
    (out / "config.json").write_text(json.dumps(config, indent=2)+"\n")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2)+"\n")
    (out / "failure-states.json").write_text(json.dumps(failure_rows, indent=2)+"\n")
    (out / "policy-errors.json").write_text(json.dumps(policy_errors, indent=2)+"\n")
    rate = f"{100*metrics['win_rate']:.1f}%" if valid else "N/A"
    lo, hi = metrics["wilson95"]
    text = f"# {config['version']} experiment\n\nTransport: {config['transport']}. Runtime: hs-arena 0.2.2.\n\n"
    text += f"Results: {wins}/{len(valid)} wins ({rate}); Wilson 95% interval [{lo:.3f}, {hi:.3f}].\n"
    text += f"Mean global turns: {metrics['mean_turns']}; mean outgoing hero damage: {metrics['mean_hero_damage']}.\n"
    text += f"Illegal actions: {metrics['illegal']}; timeouts: {metrics['timeouts']}; early exits: {metrics['early_exits']}.\n\n"
    text += f"Policy exceptions: {metrics['policy_errors']}; CLI fallbacks: {metrics['cli_fallbacks']}.\n\n"
    if config.get('acceptance'): text += f"Acceptance: {config['acceptance']}\n\n"
    text += "Small samples are smoke tests, not reliable estimates of long-run competitive strength.\n\n"
    text += f"Change: {config.get('change', 'Initial fixed-deck baseline.')}\n\n"
    text += f"Next hypothesis: {config.get('next_hypothesis', 'Add bounded tactical search without changing the deck.')}\n\n"
    text += "See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.\n"
    (out / "summary.md").write_text(text)
    failure_text = "# Failure review\n\nSignals below are observations, not proven causal explanations. No exhaustive lethal audit has been run.\n\n"
    for f in failure_rows:
        failure_text += f"- {f['game_id']}, seed {f['seed']}, seat {f['candidate_seat']}: {', '.join(f['signals'])}; turn {f['key_state']['turn']}.\n"
    if not failure_rows: failure_text += "No losses in this sample.\n"
    failure_text += "\nConcrete observations and selected actions are saved in failure-states.json; full official logs remain in games/.\n"
    (out / "failures.md").write_text(failure_text)
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out"); parser.add_argument("--version", default="v0")
    parser.add_argument("--transport", default="real MCP client, no model")
    parser.add_argument("--skill", default="face_hunter")
    args = parser.parse_args()
    skill = Path(args.skill)
    config = {"version":args.version, "transport":args.transport,
              "git_commit":subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "code_sha256":fingerprint(skill), "deck":json.loads((skill/"deck.json").read_text()),
              "config":json.loads((skill/"config.json").read_text()),
              "seeds":sorted({json.loads(p.read_text())["seed"] for p in Path(args.out).glob("games/*/result.json")})}
    metrics = summarize(args.out, config)
    print(json.dumps({k:v for k,v in metrics.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
