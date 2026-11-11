# Source register and executable hypotheses

Retrieved 2026-11-10, America/New_York. Search results were followed to original
article bodies. No online deck list or modern card values were copied into the deck.

| ID | Original source, author/publisher | Confirmed date/version | Relevance and limitations |
|---|---|---|---|
| S1 | [Top 200 Legend with Obsolete Secret Hunter](https://www.reddit.com/r/CompetitiveHS/comments/55dois/top_200_legend_with_obsolete_secret_hunter_64_wr/), u/DimfrostHS | 2016 pre-Call of the Wild nerf; renderer shows relative age, exact day not confirmed | Original player's Secretkeeper/Bow/Tracking and role-switching account. Huntress, Cat Trick and other expansion cards unavailable here. Anecdotal wins are not our evidence. |
| S2 | [Hunter Secrets](https://www.icy-veins.com/hearthstone/hunter-secrets), Kat/Icy Veins | 2018-04-10 | Explains triggers, testing weak attackers, play-order interactions. Course engine tests override historical descriptions. |
| S3 | [Midrange Hunter](https://www.icy-veins.com/hearthstone/midrange-hunter-deck), Kat/Icy Veins | 2020-08-06, Scholomance | Curve, selective trades, Beast/Hounds synergy, burn transition. Modern card recommendations excluded. |
| S4 | [Who's the Beatdown?](https://articles.starcitygames.com/articles/whos-the-beatdown/), Mike Flores/Star City Games | 1999-01-01 reprint | Role assignment depends on relative speed and long-game resources. Magic examples require adaptation; no Hearthstone numerical claim inferred. |
| S5 | [What is Tempo?](https://www.icy-veins.com/hearthstone/what-is-tempo-in-hearthstone), Sottle/Icy Veins | 2015-08-26 | Mana opportunity cost, initiative, sticky minions. Mana spent is not itself a sufficient objective. |
| S6 | [Card Advantage](https://www.icy-veins.com/hearthstone/card-advantage-in-hearthstone), Aleco/Icy Veins | 2018-01-18 | Resource conservation and avoiding inefficient exchanges. Fixed Hunter has little draw, so value must be balanced with a finite clock. |
| S7 | [Course HW2](https://bu-agenticai-class-fall26.vercel.app/materials/assignments/hw2.md), BU CS598 | Current fetched copy; local package 0.2.2 | Binding submission/evaluation contract. SPA web rendering only showed Loading; raw markdown fetched successfully with HTTPS. |
| S8 | [Codex CLI reference](https://developers.openai.com/codex/cli/reference/), OpenAI | Current fetched page | Local course source, not generic CLI assumptions, resolves model ID and medium effort. Actual skill logs verify gpt-6-luna. |

The guessed Classic guide URL at Icy Veins was inaccessible. The older Bear/Snake
Hunter Reddit guide's original post is deleted; comments do not replace its missing
body and no claim is attributed to that unavailable original. Search snippets from
wiki/forum order discussions were discovery leads, not accepted mechanism evidence.

## Knowledge ledger

| Claim | Source | Conditions | Exceptions | Engine check | Evidence status |
|---|---|---|---|---|---|
| Mulligan for a playable curve/plan | S1,S3 | Early minions, keeper plus one useful Secret | Expensive combo packages absent; do not keep Krush | All selected actions pass actual templates | Heuristic; B0 script 43/56 vs A0 33/56, confounded rule bundle |
| Switch between trading and face pressure | S3,S4 | Compare retaliation, resources and two-turn burn | Healing, Taunts, unknown burst, random effects | Public action summaries; scripted fixtures | Strategic hypothesis, no isolated causal effect |
| Power competes with development for two mana | S3,S5 | Later reach valuable; early bodies may recur damage | Immediate lethal and survival dominate | Course power cost/damage; known lethal fixture | Mechanism verified, policy contextual |
| Secret order and testing matter | S2 | Weak attacker can consume Freezing; hero attack triggers Explosive | Snake requires a minion attacked and capacity | Both Explosive/Freezing orders tested | Verified course behavior, historical differences retained |
| Bow gains durability on own revealed Secrets | S1,S2 + engine | Weapon still equipped | Spent final charge cannot be renewed | +2 vs +1 in order fixture | Verified |
| Secretkeeper grows after own Secrets only | engine | Unsilenced keeper present | Printed text says any Secret | Own and enemy Secret test | Verified text/implementation mismatch |
| Juggler and Hyena reward summons/deaths | S2,S3 + engine | Juggler before Hounds/Snake; Hyena before Beast deaths | Random knife targets; board cap; silence | Snake produces three knives; deterministic solver rejects random summons | Partly verified; random multi-action solver unsupported |
| Dire Wolf placement changes immediate reach | engine | Adjacent ready minions | Deaths shift adjacency | Real-engine Wolf+burn lethal family | Verified supported case |
| Preserve Beast for Kill Command/Houndmaster | S3 + engine | Beast survives until resolution | Sacrificing Beast can reduce burn | 5-damage burn and +2/+2 Taunt fixture | Verified |
| Ooze can be tempo or weapon answer | engine, research inference | Consider current curve and publicly seen weapons | No hidden weapon assumed | Weapon destruction verified | Mechanism verified; hold/tempo policy uncalibrated |
| Highmane/Krush support different late plans | S1,S3 + engine | Sticky value versus nine-mana eight Charge attack | Taunt, removal, unavailable mana | Highmane two tokens; actual Krush lethal | Verified effects, strategic choice heuristic |
| Tracking chooses one, discards other two | S1 + engine | Three cards available | Short deck / full hand | Deck reduces by three; chosen card enters hand | Verified, no modern Discover semantics assumed |
| Random Companion can provide conditional lethal | engine | Three equiprobable entourage outcomes | Subsequent unhandled triggers stop proof | Tool identifies 1/3 supported lethal branch | Exact branch mass, incomplete continuation coverage |

No source's empirical win rate is reused as a claim about this course agent. The
full card table and engine/data hashes are in card-audit.json and runtime.json.
