"""Official stdio MCP transport example adapted to the same supervised Python policy."""
import json
import os
import subprocess
import sys
from pathlib import Path



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
            command=[sys.executable,'scripts/decide.py']
            try:
                output=subprocess.run(command,capture_output=True,text=True,timeout=2.5,check=True)
                envelope=json.loads(output.stdout)
            except (subprocess.SubprocessError,ValueError):
                output=subprocess.run([sys.executable,'scripts/fallback.py'],capture_output=True,text=True,timeout=1,check=True)
                envelope=json.loads(output.stdout)
            if envelope.get('refresh_required'):continue
            reply=client.call('act',seq=envelope['seq'],action=envelope['action'])
        else:
            reply=client.call('wait')
    print(reply.splitlines()[0], file=sys.stderr)
    client.close()


if __name__ == "__main__":
    main()
