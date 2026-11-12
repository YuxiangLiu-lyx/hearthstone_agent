# CS 598 A1 Homework 2: Hearthstone Agent Arena

| | |
|---|---|
| Due | Sunday, November 15, 2026, 11:59:59 pm ET; see the [course schedule](https://bu-agenticai-class-fall26.vercel.app/) |
| Weight | 10% of the course grade (10 points), plus up to additional 10 points of bonus |
| Work | Individual |
| Package (Please download) | [hs-arena-0.2.2.zip](https://bu-agenticai-class-fall26.vercel.app/materials/assignments/hw2/hs-arena-0.2.2.zip) (runtime, examples, game data, and documentation) |
| Submission ID | `hw2` |

## 1. The assignment

Build an agent that plays a simulated version of Hearthstone (once a popular deck battle game) by writing a **skill**: a folder containing a playbook (`SKILL.md`) and, optionally, Python scripts and reference material. Your agent chooses a class and submits its deck through MCP in the first decision of each game.

The course runs your skill using the model you specify **in your Slack submission command**:

- `haiku`: Claude Haiku 5.5, run by Claude Code;
- `luna`: GPT-6-Luna, run by Codex.

Both use **medium** reasoning effort. You must provide the model choice on your submission.

The game uses a fixed Basic and Classic card pool, simulated by [fireplace](https://github.com/jleclanche/fireplace). The package contains card data, examples, the game implementation, and the tool protocol. Your agent can inspect these resources to learn the game and discover strategies. You do not need to learn Hearthstone yourself or search the web for its rules.

How your agent plays is up to you: a playbook the model follows, Python scripts that compute or simulate, notes kept during a game, or a combination. A script may decide every move while the model relays its decisions to the game tools.

## 2. What you submit

Submit **one ZIP containing one skill folder**, with `SKILL.md` directly inside that folder:

```text
my-agent/
├── SKILL.md       required: name and description frontmatter, then instructions
├── scripts/       optional: Python code
├── references/    optional: knowledge files
└── assets/        optional: supporting resources
```

See the [Agent Skills specification](https://agentskills.io/specification) for the folder and `SKILL.md` format. You may include supporting material permitted by that protocol, subject to the HW2 restrictions below. A separate report or chat transcript is not required. You may use and adapt the package's examples.

The **entire submission must be at most 10 MB**. Include only what your agent needs. Do not bundle a Python environment, package installer, executable binary, or model weights. Submitted scripts must be **Python only**. Use the Python standard library and packages already available in the course game environment, including `hs_arena` and its bundled dependencies. We will **not install additional packages** from `requirements.txt` or download dependencies for your submission. Do not assume a package is available simply because it is installed on your own computer.

Send a direct message to the course Slack agent with this structure and **one ZIP attachment in the same message**:

```text
submit hw2 <agent-nickname> <model-name>
```

For example, attach `my-agent.zip` and write:

```text
submit hw2 mage haiku
```

- `agent-nickname` is a nickname **you choose for your game agent**, not your student name. Use one word, 1–32 letters, digits, underscores, or hyphens. Nicknames must be unique across the class, ignoring capitalization.
- `model-name` must be exactly `haiku` or `luna`.

The agent binds the nickname and model to your registered student identity and that submission. You may change either on a later submission; your **highest-scoring submission** determines the nickname, model, and skill used for grading and the ladder (see section 6). Public ladder results show agent nicknames, not student names. Choose a nickname that does not reveal your identity if you wish to keep it private.

If required command fields or the ZIP attachment are missing, the agent explains how to correct the submission, including the example `submit hw2 faker haiku`. A rejected command does not use an opportunity. A successful confirmation states **which submission this is out of 3 and how many opportunities remain**. After three successful submissions, further uploads are rejected. Wait for confirmation; attaching a file alone is not a submission.

## 3. How your skill is played

For each game, the course starts **one fresh agent session** for your seat, with a fresh copy of your skill, the course prompt, game tools, and working folders:

- `game/`: visible game state, card pool, and event history;
- `scratch/`: space for notes during this game;
- tools `wait`, `act`, and `history`;
- a shell for running your Python scripts and the installed `hs_arena` package.

During evaluation there are **no subagents, no web tools, and no network access**. These are evaluation restrictions; you may use advanced models and other development methods while preparing your skill.

Both players first receive `phase: deck_submission`. Your skill must tell the agent how to choose a class and submit an action such as:

```json
{"type":"submit_deck","hero_class":"MAGE","cards":["...30 card IDs..."]}
```

Your agent must choose its class and 30-card deck from `game/card_pool.json` and submit them through MCP with `act` and the pending sequence number in the first decision of each game. Describe how to make that choice in your skill. Opponent choices are hidden at this stage. Once accepted, your class and deck are fixed for that game, and mulligans begin.

**Nothing carries between games.** Each game starts independently. A series against one opponent may start all of its games concurrently; there is no opportunity to record what happened in one game and feed that experience into the next game in that series. You can study returned replays and improve your skill before a later submission.

For local practice, see the package README and run:

```text
hs-arena play --p1 skill:my-agent --p2 greedy
```

Use your own Claude Code or Codex account locally. The package's local launcher uses its `model: haiku` or `model: luna` frontmatter setting; this local setting does **not** replace the required model argument in your Slack command. Local tests are unlimited and do not consume your three course submissions. `hs-arena validate my-agent` is a local troubleshooting aid, not a course admission or grading stage.

## 4. Rules

1. Submit one skill folder within the size and Python restrictions in section 2.
2. Any playing strategy is allowed within these rules.
3. Your agent must not access other players' files or hidden state, use the network, call additional models, or use hacks or jailbreaks to obtain hidden information such as the opponent's hand or deck. Reading your own files and the provided public game code, card data, and installed Python libraries is allowed. Games are logged and audited. If we find deliberate and intentional cheating or malicious behavior, your submission will be graded as 0.
4. Build a 30-card deck from the course pool: cards of your chosen class plus neutral cards, at most two copies of each card and at most one of each Legendary. See `docs/card_pool.md` and `hs-arena cards`. This fixed pool differs from the live commercial game.
5. **Time limit: 180 seconds per decision. A single timeout forfeits that game.** This also applies during deck submission and mulligan.
6. **The third illegal action in a game forfeits that game.** A rejected action is reported to the agent; earlier errors can be corrected while the game continues.
7. **Ending the agent session before the game finishes forfeits that game.** Ending your turn with the normal game action is allowed and is not an early session exit. Staff handle verified course-side service failures separately.
8. There is no memory or file persistence between games. Knowledge and strategy prepared before submission may be included in your skill.



## 5. Opponents

| Opponent | What you know |
|---|---|
| **Bot 1: Greedy Mage** | Available as `--p2 greedy`, with its Mage deck and source code in the package. The examples also demonstrate this strategy as a skill and MCP client. |
| **Bot 2: Mystery Bot** | A stronger rule-based bot whose code is not released. You encounter it in course test runs. |
| **Boss Fight: Astra** | A powerful agent run by GPT-6 Astra, with deck and strategy designed by the instructor. No further details are released. |
| **Classmates** | Opponents in the ladder after the deadline, identified publicly by agent nickname. |

## 6. Submissions and evaluation

You have **3 submission opportunities in total**, including any late submissions.

- **Every submission is evaluated:** 6 games against Bot 1, 4 against Bot 2, and 4 against Astra. You receive results and can download your replays.
- **Your highest-scoring submission is your effective submission.** Compare the total of the base points and Astra bonus earned by each submission (up to 14 points, before any late deduction). If you submit fewer than three times, we select the highest-scoring one among those you submitted. A later, lower-scoring submission does not replace it.
- **That same submission enters the ladder** after the deadline, subject to the ladder cutoff in section 9. Its recorded base points and Astra bonus count toward your grade; these games are not rerun for final grading. Ladder games are new games, and the ladder bonus is added to the selected submission's score.

Turnaround **depends on our computation bandwidth**. Submit your first version early. Near the beginning, results may arrive within a few minutes; as more students submit near the deadline, the queue may take longer. 

In every even-length series, each side goes first in exactly half of the games. Individual games are independent and may run in parallel, as described in section 3.

## 7. Grading

Maximum: **10 base points + 10 bonus points**, contributing directly to course total grade. A draw counts as a loss except in the ladder.

**Base points (maximum 10)**

| Part | Games | Points |
|---|---|---|
| Completion | Only the 6 games against Bot 1 | Start with 5 points and subtract 1 per forfeited game. Six forfeits earn 0. Ordinary game losses do not reduce completion points. |
| Bot 1 wins | 6 | 5–6 wins: +3; 3–4 wins: +2; 1–2 wins: +1; 0 wins: 0 |
| Bot 2 wins | 4 | 3–4 wins: +2; 1–2 wins: +1; 0 wins: 0 |

**Bonus points (maximum 10)**

| Part | Points |
|---|---|
| Astra | +1 per win across 4 games, up to +4 |
| Ladder | At least 10 games against randomly drawn, different classmates. Elo ratings are fitted from all ladder results together. A draw counts as half a win. Rank bonuses: top 5%: +6; 5–10%: +5; 10–20%: +4; 20–30%: +3; 30–40%: +2; 40–50%: +1. A cutoff at proportion `p` is rank `ceil(p × N)` among `N` eligible participants. |

## 8. Replays and public results

You can download the turn-by-turn `replay.jsonl` for your own evaluated games and read it with `hs-arena replay`. You receive your own games' replays only. Public ladder results will diplay participants by the nickname bound to their final submission.

## 9. Timeline and policies

| Date | Event |
|---|---|
| Sunday, November 15, 2026, 11:59:59 pm ET | Submission deadline, as listed on the course schedule |
| Wednesday, November 18, 2026, 11:59:59 pm ET | Last time a final submission can arrive without exceeding the three-day ladder cutoff |
| After the deadline | Final evaluation and ladder; timing depends on computation bandwidth |

- **Late work:** deduct **2 points for each started 24-hour interval** after the deadline, with a minimum final score of 0. The course's two shared late exceptions can waive the points deduction when applicable.
- **Ladder cutoff:** a final submission received **more than 72 hours late** cannot enter the ladder competition and cannot earn ladder bonus. **This cutoff cannot be waived**, including with a course late exception.
- **Individual work.** This is an individual competitive assignment.
- **AI-assisted development:** you may use advanced models and any development methods to prepare your skill. Only evaluation is restricted to Haiku or Luna and the runtime rules above.

## 10. FAQ

**I have never played Hearthstone. Can I do this?**

Yes. Ideally, you do not need to know how to play: the assignment is designed around your agent discovering strategies, rather than rewarding your own game expertise. Prior Hearthstone knowledge is not required. The fixed card version also differs from the live game, so real-game knowledge may not transfer directly. Let your development agent inspect the package and experiment.

**What exactly do I turn in?**

A ZIP of your skill folder. It can contain the instructions, references, assets, and other supporting files described in the [Agent Skills specification](https://agentskills.io/specification), within HW2's 10 MB limit and Python-only execution policy. Send `submit hw2 <agent-name> <haiku|luna>` with the ZIP attached. You do not need a separate report.

**Can I use a stronger model to develop my agent?**

Yes. Development methods are unrestricted. We restrict the model only when running your submitted skill for evaluation: you choose Haiku or Luna in the Slack command.

**Can my agent change class or deck between games?**

Yes. Describe the selection strategy in your skill. When MCP asks for a class and deck at the start of a game, your agent may choose randomly or follow another strategy. Once that deck is accepted, the submitted class and deck remain fixed for the rest of that game.

**Can a Python script decide every move?**

Yes. See `examples/greedy_skill`: its script chooses the move and the agent submits it with `act`.

**Can I keep memory?**

Within a game, yes: use `scratch/` and `history`. No state carries into another game. You may analyze returned replays during development and include your improvements in a later submission.

**Can I add Python packages?**

We do not install packages for individual submissions. Use the standard library and dependencies already bundled with the game environment. Do not submit an environment or rely on libraries available only on your own computer.

**Can I change my agent nickname or model?**

Yes. You may choose a different nickname or model on a later submission. The nickname must be unique across the class. Your highest-scoring submission controls the final nickname, model, and skill, including for the ladder. A rejected submission does not change them.

**What happens if my skill does not work?**

An accepted submission still counts. Its games are forfeited if the agent cannot run, times out once, makes three illegal actions, or exits before the game ends. Test locally before using a course submission opportunity.

