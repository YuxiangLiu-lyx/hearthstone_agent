---
name: secret-hunter-program
description: Fixed Secret Hunter Python policy. Run the script and relay its exact seq/action without strategic judgment.
model: luna
---

# Secret Hunter program relay

Python makes every strategic decision. Your only task is to run it and relay its output. Do not analyze the board, rank candidates, change actions, choose cards, or call another model.

1. Call `wait`. After `act`, its reply may already contain the next decision. If the reply says `GAME OVER`, stop.
2. At **every** `YOUR DECISION`, including when only `end_turn` and `concede` are legal, run `python scripts/decide.py` in this skill folder. It reads the latest `game/state.json` and prints exactly `{"seq": N, "action": {...}}`. The first `deck_submission` output explicitly submits the fixed deck.
3. Before **every** `act`, require a completed script command that printed the current sequence. Never infer or directly submit `end_turn`, even with zero mana, an empty board, or only one non-concede action. If no script output exists for this exact sequence, run the script now. Then call `act` using exactly the printed `seq` and `action`. Copy all action fields without changes. Do not submit an older output or invent an action.
4. Continue until `GAME OVER`. A new sequence always returns to step 2; an `act` reply is not authorization to choose the next action. If the script prints `refresh_required`, run it again against the latest state. If the host rejects a stale action, run the script again.
5. If the command fails, times out, or prints no valid envelope, run `python scripts/fallback.py` and relay that program's exact output. If the state is temporarily unreadable, call `wait` and retry the fallback. Never choose a move yourself and never stop before `GAME OVER`.

The program supervises its worker and saves a legal action before searching. Logs are in `scratch/decisions.jsonl`; stdout is only the protocol envelope. Use only this folder. Do not modify the deck, configuration or scripts during a match.
