# Local MCP client

The final, portable client is `development/clients/face-hunter-final`.
It follows the official MCP example transport and invokes our watchdog-protected
Python CLI for every decision. It does not use GreedyBot to choose actions.

To generate another isolated client from the current skill:

```sh
.venv/bin/python -m development.benchmarks.make_client face_hunter tests/local_client/new-run
.venv/bin/hs-arena play --p1 client:tests/local_client/new-run --p2 greedy --games 3 --seed 43020 --out experiments/new-mcp/games
```

Use a new destination for every client/run. `generated/` contains the earlier local
smoke client and is ignored by Git; the final client is tracked separately.
