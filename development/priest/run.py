"""Paired Priest benchmarks against frozen strong local opponents, using official games."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys

from hs_arena.agents.greedy_bot import GreedyBot
from hs_arena.deck import load_deck
from hs_arena.protocol import Config
from hs_arena.runner import play_game
from development.benchmarks.run import ObservedPlayer, load_policy, fingerprint
from development.face_hunter.report import summarize

ROOT = Path(__file__).resolve().parents[2]
OPPONENTS = {"paladin": "development/checkpoints/v3-paladin-relay-champion",
             "zoo": "development/checkpoints/v7-zoo-strength",
             "priest": "development/candidates/adversaries/priest-control"}


class PriestPlayer(ObservedPlayer):
    def __init__(self, name, deck, fn):
        super().__init__(name, deck, fn)
        self.history = []

    def decide(self, state):
        self.history.extend(state.get("events", []))
        # Same public-history interpretation as the submitted CLI.
        from priest_tactics import with_history
        return super().decide(with_history(state, self.history))


def worker(task):
    candidate, deck_path, name, seed, seat, output = task
    sys.path.insert(0, str(ROOT/"control_priest/scripts"))
    policy, _ = load_policy(candidate)
    config = json.loads((Path(candidate)/"config.json").read_text())
    player = PriestPlayer("candidate", load_deck(deck_path), lambda s: policy.decide(s, config))
    if name == "greedy":
        opponent = GreedyBot("greedy", load_deck(ROOT/"hs-arena-0.2.2/decks/greedy_mage.json"))
    elif name == "hunter":
        from development.face_hunter.run import HunterPlayer
        sys.path.insert(0, str(ROOT/"face_hunter/scripts"))
        opponent = HunterPlayer(json.loads((ROOT/"face_hunter/config.json").read_text()))
    else:
        folder = ROOT/OPPONENTS[name]
        opposing, _ = load_policy(folder)
        cfg = json.loads((folder/"config.json").read_text())
        opponent = ObservedPlayer(name, load_deck(folder/"deck.json"), lambda s: opposing.decide(s, cfg))
    folder = Path(output)/"games"/f"{name}-s{seed}-p{seat}"
    result = play_game({seat: player, 3-seat: opponent}, game_dir=folder, game_id=folder.name,
                       seed=seed, config=Config(max_turns=180))
    return {"game": folder.name, "errors": player.errors, "result": result}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True); p.add_argument("--deck")
    p.add_argument("--out", required=True); p.add_argument("--version", required=True)
    p.add_argument("--start", type=int, default=51000); p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--opponents", default="greedy,paladin,zoo,hunter,priest")
    p.add_argument("--holdout", action="store_true")
    args = p.parse_args()
    assert args.holdout == (args.start >= 100000)
    deck = args.deck or str(Path(args.candidate)/"deck.json")
    load_deck(deck)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=False)
    config = {"version": args.version, "candidate": args.candidate, "deck": json.loads(Path(deck).read_text()),
              "code_sha256": fingerprint(args.candidate), "config": json.loads((Path(args.candidate)/"config.json").read_text()),
              "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "opponents": args.opponents.split(","), "seeds": list(range(args.start, args.start+args.seeds)),
              "holdout": args.holdout, "seat_swap": True, "transport": "official Python runner, no model",
              "change": args.version, "next_hypothesis": "Review paired results and concrete failures before further changes.",
              "opponent_fingerprints": {n: fingerprint(ROOT/path) for n, path in {**OPPONENTS, "hunter": "face_hunter"}.items()}}
    (out/"config.json").write_text(json.dumps(config, indent=2)+"\n")
    tasks = [(args.candidate, deck, name, seed, seat, str(out)) for name in config["opponents"]
             for seed in config["seeds"] for seat in (1, 2)]
    errors = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, task) for task in tasks]
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result["errors"]:
                errors.append(result)
            if i % 20 == 0 or i == len(tasks):
                print(f"Completed {i}/{len(tasks)}", flush=True)
    metrics = summarize(out, config)
    (out/"execution-errors.json").write_text(json.dumps(errors, indent=2)+"\n")
    if errors:
        raise RuntimeError(f"Policy failed in {len(errors)} games; do not promote")
    print(json.dumps({k:v for k,v in metrics.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
