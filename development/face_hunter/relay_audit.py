"""Compare actual model MCP actions to printed Python output, including deck setup."""
import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("games"); p.add_argument("--out", required=True)
    args = p.parse_args()
    results = []
    for folder in sorted(Path(args.games).glob("*/p1/decisions")):
        printed, errors = {}, []
        for transcript in sorted((folder.parent/"seat").glob("session_*.jsonl")):
            for line in transcript.read_text().splitlines():
                event = json.loads(line); item = event.get("item", {})
                if event.get("type") != "item.completed" or item.get("type") != "command_execution":
                    continue
                if "scripts/decide.py" not in item.get("command", ""):
                    continue
                output = item.get("aggregated_output", "")
                if "policy fallback:" in output or "bounded worker fallback:" in output:
                    errors.append(output)
                for raw in output.splitlines():
                    try:
                        value = json.loads(raw)
                    except ValueError:
                        continue
                    if isinstance(value, dict) and "seq" in value and "action" in value:
                        printed.setdefault(value["seq"], []).append(value["action"])
        n, relayed, differences = 0, 0, []
        for path in sorted(folder.glob("*.action.json")):
            state = json.loads(path.with_name(path.name.replace(".action.json", ".state.json")).read_text())
            action = json.loads(path.read_text())["action"]
            n += 1
            if action in printed.get(state["seq"], []):
                relayed += 1
            else:
                differences.append({"seq": state["seq"], "phase": state["phase"], "action": action,
                                    "printed": printed.get(state["seq"], [])})
        results.append({"path": str(folder), "decisions": n, "script_invoked_and_relayed": relayed,
                        "fallback_outputs": errors, "differences": differences})
    output = {"games": results, "decisions": sum(r["decisions"] for r in results),
              "script_invoked_and_relayed": sum(r["script_invoked_and_relayed"] for r in results),
              "fallback_outputs": sum(len(r["fallback_outputs"]) for r in results)}
    Path(args.out).write_text(json.dumps(output, indent=2)+"\n")
    print(json.dumps({k:v for k,v in output.items() if k != "games"}, indent=2))


if __name__ == "__main__":
    main()
