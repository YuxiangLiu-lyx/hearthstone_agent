"""Run the unchanged 14-opponent Zoo suite with Priest public-history handling.

This is the same official-engine, model-free test population used by Zoo's
1,120-game validation. Forty fresh seeds and two seats give 80 games per opponent.
The submitted skills and all opponent policies remain frozen.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from hs_arena.deck import load_deck
from hs_arena.protocol import Config
from hs_arena.runner import play_game

from development.benchmarks.run import ObservedPlayer, fingerprint, load_policy
from development.face_hunter.report import summarize
from development.priest.run import PriestPlayer, ROOT

POPULATION = ROOT / "development/opponents/zoo-research.json"


def worker(task):
    candidate, opponent_spec, seed, seat, output = task
    # Match the released CLI's public-history annotation, including temporary theft.
    sys.path.insert(0, str(ROOT / "control_priest/scripts"))
    policy, actions = load_policy(candidate)
    cfg = json.loads((Path(candidate) / "config.json").read_text())
    player = PriestPlayer("candidate", load_deck(Path(candidate) / "deck.json"),
                         lambda state: policy.decide(state, cfg))
    spec = opponent_spec
    if spec.get("policy"):
        opposing, _ = load_policy(ROOT / spec["policy"])
        opposing_cfg = json.loads((ROOT / spec["policy"] / "config.json").read_text())
        opponent_fn = lambda state: opposing.decide(state, opposing_cfg)
    elif spec["mode"] == "search":
        from development.opponents.search import decide
        opponent_fn = lambda state: decide(state, actions.expand)
    else:
        from development.opponents.population import decide
        opponent_fn = lambda state: decide(state, spec["mode"], actions.expand)
    opponent = ObservedPlayer(spec["name"], load_deck(ROOT / spec["deck"]), opponent_fn)
    folder = Path(output) / "games" / f"{spec['name']}-s{seed}-p{seat}"
    result = play_game({seat: player, 3-seat: opponent}, game_dir=folder,
                       game_id=folder.name, seed=seed, config=Config(max_turns=180))
    return {"game": folder.name, "candidate_errors": player.errors,
            "opponent_errors": opponent.errors, "result": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--seeds", type=int, default=40)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--holdout", action="store_true")
    args = parser.parse_args()
    assert args.holdout == (args.start >= 100000)
    assert args.seeds > 0
    population = json.loads(POPULATION.read_text())
    assert len(population) == len({spec["name"] for spec in population}) == 14
    candidate = Path(args.candidate)
    load_deck(candidate / "deck.json")
    for spec in population:
        load_deck(ROOT / spec["deck"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    config = {
        "version": args.version, "candidate": args.candidate,
        "code_sha256": fingerprint(candidate),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "public_history_source_sha256": fingerprint(ROOT / "control_priest"),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "deck": json.loads((candidate / "deck.json").read_text()),
        "config": json.loads((candidate / "config.json").read_text()),
        "population_path": str(POPULATION.relative_to(ROOT)), "population": population,
        "population_code_sha256": fingerprint(ROOT / "development/opponents"),
        "opponent_versions": {spec["name"]: {
            "deck": json.loads((ROOT / spec["deck"]).read_text()),
            "policy_sha256": fingerprint(ROOT / spec["policy"]) if spec.get("policy") else None,
        } for spec in population},
        "seeds": list(range(args.start, args.start + args.seeds)),
        "holdout": args.holdout, "seat_swap": True,
        "planned_games": 14 * args.seeds * 2,
        "transport": "official Python runner, no model",
        "change": "Extend validation to the historical 14-opponent suite; frozen policy and deck.",
        "next_hypothesis": "Report coverage and per-matchup weaknesses; do not retune on these seeds.",
    }
    (out / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    tasks = [(args.candidate, spec, seed, seat, str(out))
             for spec in population for seed in config["seeds"] for seat in (1, 2)]
    errors = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, task) for task in tasks]
        with (out / "execution-results.jsonl").open("w") as log:
            for index, future in enumerate(as_completed(futures), 1):
                result = future.result()
                log.write(json.dumps(result) + "\n")
                log.flush()
                if result["candidate_errors"] or result["opponent_errors"]:
                    errors.append(result)
                if index % 40 == 0 or index == len(tasks):
                    print(f"Completed {index}/{len(tasks)}; execution errors {len(errors)}", flush=True)
    (out / "execution-errors.json").write_text(json.dumps(errors, indent=2) + "\n")
    metrics = summarize(out, config)
    assert metrics["attempted"] == len(tasks)
    if errors or any(metrics[key] for key in ("illegal", "timeouts", "early_exits", "void_or_aborted")):
        raise RuntimeError("Execution defects invalidate this run; inspect both players' records.")
    print(json.dumps({key: value for key, value in metrics.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()
