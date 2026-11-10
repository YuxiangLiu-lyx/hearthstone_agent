"""Paired, model-free comparisons using the official runner and frozen opponents."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

from hs_arena.agents.base import Player, Decision
from hs_arena.agents.greedy_bot import GreedyBot
from hs_arena.agents.random_bot import RandomBot
from hs_arena.deck import load_deck
from hs_arena.protocol import Config
from hs_arena.runner import play_game
from development.benchmarks.run import ObservedPlayer, fingerprint, load_policy
from development.face_hunter.report import summarize

ROOT = Path(__file__).resolve().parents[2]
OPPONENTS = {
    "paladin": "development/checkpoints/v3-paladin-relay-champion",
    "zoo": "development/checkpoints/v7-zoo-strength",
    "priest": "development/candidates/adversaries/priest-control",
}


class HunterPlayer(Player):
    kind = "hunter-python"

    def __init__(self, config):
        super().__init__("hunter-"+config["version"], load_deck(ROOT / "face_hunter/deck.json"))
        self.config = config
        self.history = []

    def start(self, seat):
        super().start(seat)
        self.log = open(seat.player_dir / "observations.jsonl", "w", encoding="utf-8")

    def decide(self, state):
        from strategy import choose_with_info
        from state_features import with_public_history
        from action_validator import legal, fallback
        self.history.extend(state.get("events", []))
        state = with_public_history(state, self.history)
        start = time.perf_counter()
        error = None
        info = {}
        try:
            action, info = choose_with_info(state, self.config)
            if not legal(state, action):
                raise ValueError("Policy returned an illegal action")
        except Exception:
            error = traceback.format_exc()
            action = fallback(state)
        elapsed = time.perf_counter()-start
        self.log.write(json.dumps({"state": state, "action": action, "elapsed_s": elapsed, "policy_error": error, "decision_info":info})+"\n")
        return Decision("action", action)

    def stop(self):
        self.log.close()


def worker(task):
    sys.path.insert(0, str(ROOT / "face_hunter/scripts"))
    config, name, seed, seat, output = task
    hunter = HunterPlayer(config)
    mage_deck = load_deck(ROOT / "hs-arena-0.2.2/decks/greedy_mage.json")
    if name == "greedy": opponent = GreedyBot("greedy", mage_deck)
    elif name == "random": opponent = RandomBot("random", mage_deck)
    elif name == "v0": opponent = HunterPlayer(json.loads((ROOT / "development/face_hunter/configs/v0.json").read_text()))
    else:
        folder = ROOT / OPPONENTS[name]
        policy, _ = load_policy(folder)
        opposing_config = json.loads((folder / "config.json").read_text()) if (folder / "config.json").exists() else {}
        opponent = ObservedPlayer(name, load_deck(folder / "deck.json"), lambda s: policy.decide(s, opposing_config))
    destination = Path(output) / "games" / f"{name}-s{seed}-p{seat}"
    return play_game({seat:hunter, 3-seat:opponent}, game_dir=destination, game_id=destination.name,
                     seed=seed, config=Config(max_turns=180))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True);p.add_argument("--out", required=True)
    p.add_argument("--start", type=int, default=42100);p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--opponents", default="greedy,paladin,zoo,priest")
    p.add_argument("--workers", type=int, default=4);p.add_argument("--holdout", action="store_true")
    p.add_argument("--change", default="Fixed-deck strategy comparison")
    args = p.parse_args()
    assert args.holdout == (args.start >= 100000), "Reserved holdout seeds require --holdout"
    out = Path(args.out);out.mkdir(parents=True, exist_ok=False)
    config = json.loads(Path(args.config).read_text())
    metadata = {"version":config["version"], "config":config, "transport":"official Python runner, no model",
                "code_sha256":fingerprint(ROOT/"face_hunter"),
                "git_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
                "deck":json.loads((ROOT/"face_hunter/deck.json").read_text()),
                "seeds":list(range(args.start,args.start+args.seeds)),"seat_swap":True,
                "holdout":args.holdout,"opponents":args.opponents.split(","),"change":args.change,
                "next_hypothesis":"Inspect measured failure categories before choosing one further change.",
                "opponent_fingerprints":{n:fingerprint(ROOT/OPPONENTS[n]) for n in args.opponents.split(",") if n in OPPONENTS}}
    (out/"config.json").write_text(json.dumps(metadata,indent=2)+"\n")
    tasks = [(config,n,s,seat,str(out)) for n in args.opponents.split(",") for s in metadata["seeds"] for seat in (1,2)]
    completed = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker,t) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            f.result();completed+=1
            if completed%10 == 0 or completed == len(tasks):print(f"Completed {completed}/{len(tasks)}",flush=True)
    metrics = summarize(out, metadata)
    print(json.dumps({k:v for k,v in metrics.items() if k != "results"},indent=2))


if __name__ == "__main__":main()
