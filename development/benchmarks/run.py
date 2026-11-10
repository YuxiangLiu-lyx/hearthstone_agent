"""Run paired real games. Usage: python -m development.benchmarks.run --help."""
import argparse
import concurrent.futures
import hashlib
import importlib
import json
import math
import statistics
import sys
import time
import traceback
from types import SimpleNamespace
from collections import defaultdict
from pathlib import Path

from hs_arena.agents.base import Player, Decision
from hs_arena.deck import load_deck
from hs_arena.protocol import Config
from hs_arena.runner import play_game

ROOT = Path(__file__).resolve().parents[2]


def fingerprint(path):
    digest = hashlib.sha256()
    for p in sorted(Path(path).rglob("*")):
        if p.is_file() and p.suffix in (".py", ".json", ".md") and "__pycache__" not in p.parts:
            digest.update(str(p.relative_to(path)).encode())
            digest.update(p.read_bytes())
    return digest.hexdigest()


def load_policy(folder):
    folder = Path(folder).resolve()
    names = ("policy", "base_policy", "actions", "evaluator", "planner", "simulator", "zoo_combat")
    saved = {n: sys.modules.get(n) for n in names}
    previous_path = list(sys.path)
    def restore(modules, path):
        sys.path[:] = path
        for name in names:
            sys.modules.pop(name, None)
            if modules.get(name) is not None:
                sys.modules[name] = modules[name]
    try:
        restore({}, [str(folder / "scripts"), *previous_path])
        policy = importlib.import_module("policy")
        actions = importlib.import_module("actions")
        namespace = {n: sys.modules.get(n) for n in names}
    finally:
        restore(saved, previous_path)
    def decide(state, config=None):
        # Isolate same-named helper modules when two different frozen skills share a worker.
        saved = {n: sys.modules.get(n) for n in names}
        path = list(sys.path)
        try:
            restore(namespace, [str(folder / "scripts"), *path])
            return policy.decide(state, config)
        finally:
            namespace.update({n: sys.modules.get(n) for n in names})
            restore(saved, path)
    return SimpleNamespace(decide=decide), actions


class ObservedPlayer(Player):
    kind = "benchmark"

    def __init__(self, name, deck, fn):
        super().__init__(name, deck)
        self.fn = fn
        self.times = []
        self.unused = []
        self.errors = []

    def start(self, seat):
        super().start(seat)
        self.log = open(seat.player_dir / "observations.jsonl", "w")

    def decide(self, state):
        start = time.perf_counter()
        try:
            action = self.fn(state)
        except Exception:
            self.errors.append(traceback.format_exc())
            return Decision("exited", message=self.errors[-1])
        dt = time.perf_counter() - start
        self.times.append(dt)
        if action and action.get("type") == "end_turn":
            self.unused.append(state["you"]["mana"])
        self.log.write(json.dumps({"state": state, "action": action, "elapsed_s": dt}, separators=(",", ":")) + "\n")
        if dt > state["timeout_s"]:
            return Decision("timeout")
        return Decision("action", action)

    def stop(self):
        self.log.close()


def worker(task):
    from development.opponents.population import decide as opponent_decide
    policy, actions = load_policy(task["candidate"])
    cfg_path = Path(task["candidate"]) / "config.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    deck = load_deck(task["deck"])
    opp = task["opponent"]
    a = ObservedPlayer("candidate", deck, lambda s: policy.decide(s, cfg))
    if opp.get("policy"):
        opposing_policy, _ = load_policy(opp["policy"])
        opp_config_path = Path(opp["policy"]) / "config.json"
        opp_config = json.loads(opp_config_path.read_text()) if opp_config_path.exists() else {}
        fn = lambda s: opposing_policy.decide(s, opp_config)
    elif opp["mode"] == "search":
        from development.opponents.search import decide as search_decide
        fn = lambda s: search_decide(s, actions.expand)
    else:
        fn = lambda s: opponent_decide(s, opp["mode"], actions.expand)
    b = ObservedPlayer(opp["name"], load_deck(opp["deck"]), fn)
    seat = task["seat"]
    players = {seat: a, 3-seat: b}
    folder = Path(task["out"]) / f'{opp["name"]}-s{task["seed"]}-p{seat}'
    try:
        r = play_game(players, game_dir=folder, game_id=folder.name, seed=task["seed"], config=Config(max_turns=180))
        r.update(candidate_seat=seat, opponent=opp["name"], opponent_class=b.deck.hero_class,
                 candidate_class=deck.hero_class, score=float(r["winner"] == seat),
                 candidate_first=r["first_player"] == seat,
                 candidate_times=a.times, opponent_times=b.times, unused_mana=a.unused,
                 policy_errors=a.errors, replay=str(folder / "replay.jsonl"),
                 observations=str(folder / f"p{seat}" / "observations.jsonl"))
        return r
    except Exception:
        return {"seed": task["seed"], "opponent": opp["name"], "candidate_seat": seat,
                "reason": "harness_error", "score": 0, "error": traceback.format_exc()}


def quantile(values, q):
    return sorted(values)[min(len(values)-1, math.ceil(q*len(values))-1)] if values else None


def wilson(wins, n):
    if not n:
        return [0, 1]
    z = 1.96
    p = wins / n
    center = (p + z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [center-half, center+half]


def aggregate(games):
    valid = [g for g in games if g["reason"] not in ("void_engine_error", "harness_error", "aborted")]
    wins = sum(g["score"] for g in valid)
    times = [t for g in valid for t in g["candidate_times"]]
    unused = [t for g in valid for t in g["unused_mana"]]
    out = {"attempted": len(games), "games": len(valid), "wins": wins,
           "win_rate": wins/len(valid) if valid else None, "wilson95": wilson(wins, len(valid)),
           "void_or_errors": len(games)-len(valid),
           "turns_mean": statistics.mean(g["turns"] for g in valid) if valid else None,
           "decision_s_mean": statistics.mean(times) if times else None,
           "decision_s_p95": quantile(times, .95), "decision_s_p99": quantile(times, .99),
           "decision_s_max": max(times, default=None), "decisions": len(times),
           "unused_mana_mean": statistics.mean(unused) if unused else None,
           "illegal": sum(g["illegal_counts"][str(g["candidate_seat"])] for g in valid),
           "timeouts": sum(g["timeouts"][str(g["candidate_seat"])] for g in valid),
           "early_exits": sum(g["reason"] == "forfeit_exit" and g["winner"] != g["candidate_seat"] for g in valid),
           "policy_errors": sum(len(g.get("policy_errors", [])) for g in games)}
    for label, key in (("by_opponent", "opponent"), ("by_first", "candidate_first"), ("by_class", "opponent_class")):
        groups = defaultdict(list)
        for g in valid:
            groups[str(g[key])].append(g)
        out[label] = {k: {"games": len(v), "wins": sum(x["score"] for x in v),
                          "win_rate": sum(x["score"] for x in v)/len(v)} for k,v in groups.items()}
    out["failures"] = [{k:g.get(k) for k in ("seed", "opponent", "candidate_seat", "reason", "replay", "observations")}
                       for g in games if not g["score"]]
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True)
    p.add_argument("--deck")
    p.add_argument("--population", default="development/opponents/train.json")
    p.add_argument("--out", required=True)
    p.add_argument("--start", type=int, default=1000)
    p.add_argument("--seeds", type=int, default=20)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--split", choices=["fast", "train", "holdout"], default="train")
    args = p.parse_args()
    if args.split == "holdout" and args.start < 100000:
        p.error("Holdout seeds must start at 100000 or greater")
    if args.split != "holdout" and args.start >= 100000:
        p.error("Training must not consume reserved holdout seeds")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    pop = json.loads(Path(args.population).read_text())
    manifest = {**vars(args), "candidate_sha256": fingerprint(args.candidate), "population": pop,
                "population_code_sha256": fingerprint(ROOT / "development/opponents"),
                "candidate_deck": json.loads(Path(args.deck or Path(args.candidate)/"deck.json").read_text()),
                "opponent_versions": {o["name"]: {"deck": json.loads(Path(o["deck"]).read_text()),
                    "policy_sha256": fingerprint(o["policy"]) if o.get("policy") else None} for o in pop},
                "runtime": "hs-arena 0.2.2", "promotion_gate": "paired lower 95% CI > 0; no group down > .10; zero execution defects; independent holdout"}
    (out/"manifest.json").write_text(json.dumps(manifest, indent=2))
    tasks = [{"candidate": args.candidate, "deck": args.deck or str(Path(args.candidate)/"deck.json"),
              "opponent": opp, "seed": seed, "seat": seat, "out": str(out)}
             for opp in pop for seed in range(args.start, args.start+args.seeds) for seat in (1,2)]
    results=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, t) for t in tasks]
        with open(out/"games.jsonl", "w") as f:
            for future in concurrent.futures.as_completed(futures):
                r = future.result()
                results.append(r)
                f.write(json.dumps(r)+"\n")
                f.flush()
                if len(results)%20 == 0 or len(results)==len(tasks):
                    print(f'{len(results)}/{len(tasks)} wins={sum(x["score"] for x in results):.0f}', flush=True)
    summary = aggregate(results)
    (out/"summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k != "failures"}, indent=2))


if __name__ == "__main__":
    main()
