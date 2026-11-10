"""The Mage greedy bot as an MCP client of its seat's game MCP server.

This is what Claude Code or Codex do when they play a skill, without a model: start the seat's MCP server,
call `wait`, decide, call `act`, until GAME OVER. The decision comes from the course's greedy bot
(hs_arena.agents.greedy_bot), the same rules as `--p2 greedy`.

Run it as a player:  hs-arena play --p1 client:examples/greedy_mcp_client --p2 random
The seat starts this file in the agent folder (a copy of this directory plus game/ and scratch/) and puts the
command that starts the MCP server into the environment variable HS_ARENA_MCP.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
from decide import response
from hs_arena.deck import load_deck


class MCPClient:
    """Minimal MCP client over stdio: one JSON-RPC message per line."""

    def __init__(self, command):
        self.proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                     encoding="utf-8")
        self.next_id = 0

    def request(self, method, params=None):
        self.next_id += 1
        msg = {"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params or {}}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("the MCP server closed the connection")
            reply = json.loads(line)
            if reply.get("id") == self.next_id:
                if "error" in reply:
                    raise RuntimeError(reply["error"])
                return reply["result"]

    def notify(self, method):
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.proc.stdin.flush()

    def call(self, tool, **arguments):
        result = self.request("tools/call", {"name": tool, "arguments": arguments})
        return "".join(c.get("text", "") for c in result.get("content", []))

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=10)


def main():
    client = MCPClient(json.loads(os.environ["HS_ARENA_MCP"]))
    client.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "greedy-mcp-client", "version": "1"}})
    client.notify("notifications/initialized")
    tools = [t["name"] for t in client.request("tools/list")["tools"]]
    print(f"tools: {tools}", file=sys.stderr)


    reply = client.call("wait")
    while not reply.startswith("GAME OVER"):
        if reply.startswith("YOUR DECISION"):
            # the text is for a model; a program reads the same state as JSON from game/state.json
            state = json.loads(Path("game/state.json").read_text(encoding="utf-8"))
            reply_json = subprocess.check_output([sys.executable, "scripts/decide.py"], text=True, timeout=8)
            action = json.loads(reply_json)["action"]
            reply = client.call("act", seq=state["seq"], action=action)
        else:
            reply = client.call("wait")  # the opponent is still playing
    print(reply.splitlines()[0], file=sys.stderr)
    client.close()


if __name__ == "__main__":
    main()
