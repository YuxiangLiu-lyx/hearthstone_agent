"""Create an official-protocol MCP client from a skill for cheap transport tests."""
import argparse
import shutil
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('skill');p.add_argument('destination');a=p.parse_args()
    d=Path(a.destination)
    shutil.copytree(a.skill,d,ignore=shutil.ignore_patterns('__pycache__'))
    source=Path('hs-arena-0.2.2/examples/greedy_mcp_client/client.py').read_text()
    source=source.replace('from hs_arena.agents.greedy_bot import GreedyBot',
                          "sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))\nfrom decide import response")
    source=source.replace('    bot = GreedyBot("greedy", load_deck("deck.json"))','')
    start=source.index('            if state["phase"] == "deck_submission":')
    end=source.index('            reply = client.call("act"',start)
    source=source[:start]+'            action = response(state)["action"]\n'+source[end:]
    # Run the exact watchdog-protected CLI, including its interpreter startup, on each decision.
    source=source.replace('            action = response(state)["action"]',
        '            reply_json = subprocess.check_output([sys.executable, "scripts/decide.py"], text=True, timeout=8)\n            action = json.loads(reply_json)["action"]')
    (d/'client.py').write_text(source)
    print(d)

if __name__=='__main__':main()
