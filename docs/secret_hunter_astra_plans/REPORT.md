# Secret Hunter Astra replay repairs

The 30-card ordered original King Krush deck is frozen. Every candidate validates the course deck, checks the deck file SHA-256 and compares the actual deck-submission action to Y1. The local opponents and the previous MCGS experiment are preserved.

The three source turns are public observations from the C2 submission. The existing replay adapter swaps the two Arcane Shot slots for Misdirection and King Krush and reconstructs legal actions in the course engine. Hidden cards and randomness in the continuations are simulated. Every reference to Astra win rate below refers to the existing local Astra proxies.

## Full matches

Each row compares the same seeds, seats and opponents. The independent core and guard blocks were opened only for the selected two-feature candidate, after the development screen. The core includes three Astra proxies, two Bot2 proxies and one Bot1 proxy.

| Development (16 seeds) | Astra | Bot2 | Bot1 | All |
| --- | ---: | ---: | ---: | ---: |
| Y1 | 83/96 | 54/64 | 28/32 | 165/192 |
| Recurring summon pressure | 82/96 | 54/64 | 28/32 | 164/192 |
| Explosive Trap credit | 83/96 | 55/64 | 29/32 | 167/192 |
| Both features | 85/96 | 55/64 | 29/32 | 169/192 |
| Conditional Amani burst | 82/96 | 54/64 | 28/32 | 164/192 |

| Independent comparison | Y1 | Both features | Candidate-only wins | Y1-only wins | Gain, 95% seed-cluster interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| Core Astra | 176/240 | 188/240 | 19 | 7 | +5.00 pp [+0.42, +9.58] |
| Core Bot2 | 140/160 | 145/160 | 7 | 2 | +3.13 pp [0.00, +6.88] |
| Core Bot1 | 73/80 | 73/80 | 2 | 2 | 0.00 pp [−5.00, +5.00] |
| Entire core | 389/480 | 406/480 | 28 | 11 | +3.54 pp [+0.62, +6.87] |
| Astra/Bot2 equal-family mean | 80.42% | 84.48% | 26 | 9 | +4.06 pp [+0.94, +7.40] |
| Fourteen-opponent guard pool | 256/280 | 259/280 | 6 | 3 | +1.07 pp [−1.07, +3.21] |
| Full-CLI core spot check | 37/48 | 39/48 | 3 | 1 | +4.17 pp [0.00, +12.50] |

The independent Astra gains came from the board proxy (55 to 61 wins), tempo proxy (68 to 69), and sticky proxy (53 to 58). The guard pool includes two opponents that each cost one game. Its aggregate interval includes zero. Full-CLI scores include 17/24 to 19/24 on Astra and are descriptive with only four seed clusters. Full-CLI P99 was 0.449 s for Y1 and 0.412 s for the two-feature candidate, with candidate maximum 0.739 s. All reported full match arms had zero illegal Hunter actions, timeouts, worker errors or recorded fallbacks.

## Turn-level evidence

The recurring-summon feature scores Knife Juggler and Imp Master against next-turn mana, hand size, the next draw, board space and vulnerable friendly minions. In Astra-04, the two-feature candidate uses two Hounds on Knife Juggler and sends the third to face. The translated turn was executed by the supervised CLI. With full Y1 after the tested turn, the actual automated line improved the synthetic continuation against the frozen Zoo and tempo proxies.

The Explosive Trap feature scores exposed enemy material and checks which deathrattle tokens can die to two damage. In Astra-03, the two-feature candidate uses Kill Command on Harvest Golem and uses Steady Shot. Although the initial search includes Secretkeeper, the next atomic replanning pass discards the one-mana follow-up. The supervised CLI reproduced the omission. Keeping the target change and adding just the Secretkeeper separated the effect of the missing action from the rest of the turn.

| Public source turn | Proxy | Y1 | Actual two-feature turn | Same turn with Secretkeeper added |
| --- | --- | ---: | ---: | ---: |
| Astra-04, Juggler | Zoo | 6/40 | 15/40 | — |
| Astra-04, Juggler | Tempo | 10/40 | 11/40 | — |
| Astra-03, Golem | Zoo | 29/40 | 26/40 | 32/40 |
| Astra-03, Golem | Tempo | 34/40 | 24/40 | 33/40 |

The keeper follow-up can change the order of enemy trades. When the Dark Iron Dwarf kills the 1/2 Secretkeeper, it loses one health and can die to a subsequent trap trigger. Some replies avoid the trap or use spells first. The continuation estimates apply to the tested proxies and sampled worlds. The paired keeper ablation flipped 8 losses and cost 2 wins against Zoo, and flipped 11 losses and cost 2 wins against tempo.

The Amani variant compares Y1's full turn against a Bow attack and all three Animal Companion outcomes. The replay's visible attack is six and a self-ping on the undamaged Amani can add three. In the prior stress test, with the historical Mortal Coil line forced in a synthetic world, the manual Bow route won 40/40 compared with 0/40. Ordinary Zoo continuations went 36/40 to 32/40, and tempo went 33/40 to 33/40. The actual CLI equipped the bow, played Companion and killed Amani in all 12 replay runs, covering all three Companion summons. In 96 development Astra games no decision covered the full Bow-and-Companion gate, and the arm went 82/96 against Y1's 83/96. There is insufficient full-game coverage for an Amani promotion.

## Preserving the trap follow-up

The follow-up prototype caches only legal untargeted plays and hero power after the turn search removes a supported Deathrattle body with Explosive Trap armed. It validates the game, turn, board, hero, hand, weapon and legality before consuming each step. The normal lethal proof runs first. Actual CLI execution against the reconstructed Astra-03 position reached Kill Command on the Golem, Steady Shot, Secretkeeper, then end turn.

On 24 new paired hypotheses per proxy, the prototype's automated Astra-03 turn raised terminal wins from 14 to 21 against Zoo and from 16 to 21 against tempo, with full Y1 after that turn. Its Astra-04 outcomes were 10 to 10 and 8 to 11 respectively. In a separate 144-game per arm core screen, Y1 won 122 games and the two-feature candidate and the follow-up prototype both won 123. Their outcomes matched for every paired game. The new continuation triggered zero times in that whole-game sample. Keep the two-feature candidate as the next whole-game baseline and collect more qualifying turns before adopting the follow-up.

## Next training iteration

Mine more complete turns from the existing core and guard pools, including Y1 wins near each trigger. For each turn, enumerate the current plan plus legal alternatives and compare complete turns under shared hidden-card hypotheses. Keep continuation policy fixed and play to terminal. Record candidate-only and Y1-only wins. Reuse an original replay as a mechanism check and split tuning and validation by source game and seed.

For Amani and similar burst windows, stratify hidden scenarios into no ping, naturally sampled ping, and a forced ping stress case. Optimize a small public-state rule against unconditional terminal value over the first two groups. Use forced-ping outcomes to check coverage. Candidate lines can use a small trade, Taunt or removal and should cover burst even when Bow and Companion are absent. Log exposure, legal candidate coverage and changed actions so a rare trigger cannot look like a successful new strategy from a few replay wins.

For deterministic trap setup, mine turns where the first action of the search plan breaks a Deathrattle minion and the later decisions diverge from that plan. Include wins with deliberate banking of mana or cards. Replay the verified continuation, ordinary replanning and a cheap alternate follow-up under the same hidden-card draws. Use the two-feature result as the comparison anchor for this incremental change.

## Reproduce

Use the installed course environment and run commands from the repo root. The two-feature build fingerprint is `ad6194e2024f0375805be8a32c5f78230af7f8d3af06a161dd6748bd89e3abc9`. The deck fingerprint is `54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4`.

```sh
python -m development.secret_hunter_astra_plans.build --out runs/astra-plans/skills/engine-trap-v2 engine trap
python -m development.secret_hunter_astra_plans.build --out runs/astra-plans/skills/burst-v3 burst
python -m development.secret_hunter_astra_plans.build --out runs/astra-plans/skills/engine-trap-commit-v3 engine trap trap-commit
python -m development.secret_hunter_astra_plans.probe --candidate runs/astra-plans/skills/engine-trap-v2 --out runs/astra-plans/replay-cli-engine-trap-v2.json
python -m development.secret_hunter_astra_plans.probe --candidate runs/astra-plans/skills/engine-trap-commit-v3 --case deathrattle --out runs/astra-plans/replay-cli-engine-trap-commit-v3.json
python -m development.secret_hunter_astra_plans.continue_turns --candidate runs/astra-plans/skills/engine-trap-v2 --start 51010 --samples 40 --out runs/astra-plans/paired-turns.json
python -m development.secret_hunter_astra_plans.continue_turns --candidate runs/astra-plans/skills/engine-trap-v2 --start 51010 --samples 40 --deathrattle-tail --out runs/astra-plans/paired-deathrattle-tail.json
python -m development.secret_hunter_astra_plans.continue_turns --candidate runs/astra-plans/skills/engine-trap-commit-v3 --start 53010 --samples 24 --out runs/astra-plans/paired-turns-commit-v3.json
```

Use `development.teacher_eval.run` for the warm Python blocks. All fresh warm blocks used the tool's `confirmation` flag except the guard pool, which used `guardrail`. The phase labels below record their experimental role.

| Phase | Seed start | Seeds | Pool |
| --- | ---: | ---: | --- |
| Development screen | 21100000 | 16 | core |
| Frozen confirmation | 21110000 | 40 | core |
| Guard | 21120000 | 10 | guardrail |
| Full-CLI spot check | 21130000 | 4 | core |
| Trap continuation follow-up | 21140000 | 12 | core |

```sh
python -m development.teacher_eval.run --candidate development/secret_hunter_response/candidates/Y1 --out runs/astra-plans/confirm-Y1 --start 21110000 --seeds 40 --split confirmation
python -m development.teacher_eval.run --candidate runs/astra-plans/skills/engine-trap-v2 --out runs/astra-plans/confirm-engine-trap-v2 --start 21110000 --seeds 40 --split confirmation
python -m development.teacher_eval.compare runs/astra-plans/confirm-Y1 runs/astra-plans/confirm-engine-trap-v2 --out runs/astra-plans/confirm-engine-trap-v2-paired.json
```

The full-CLI spot check used `development.secret_hunter_mcgs.cli_match.worker` for each paired match with both seats. Candidate execution used public state and public event history, and the offline builder did the hidden-card sampling.
