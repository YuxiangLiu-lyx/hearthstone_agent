# Timing evidence and failure scope

The official timer starts at state publication, reconstructed as
`deadline_epoch_s - timeout_s`. Every helper call uses that same absolute deadline
and converts it to a monotonic budget. Waiting or asking for deeper search does not
restart the decision timer. Actual action times are taken from the official MCP
entry log, including model startup, deliberation and tool time since publication.
An MCP entry is an approximation of host receipt; this is not a model API latency.

| Layer | Implemented control | Verified scope |
|---|---|---|
| Default worker | Parent kills and reaps child at 2 seconds | Actual skill fault game: one 20-second sleep was terminated; measured tool duration 2.004 seconds, normal process scheduling overhead included |
| Ordinary/deep work | Default cap 2 seconds, below the 5-second ordinary ceiling; deep cap 10 seconds, also limited by the original adoption/target deadline | Local budget tests and actual default calls; no observed real-model deep request claimed unless logged |
| Suggestion acceptance | Reject after 40 seconds from publication; keep current legal default | Artificially advanced publication age produces late_default; only applies if main model invokes the selector |
| Decision target | 90-second target and 30-second official reserve | Tools use these limits; main model cannot be forced to return or call act |
| Model generation | No supported cancellation from submitted skill | Not implemented; killing the main session causes forfeit |
| Independent submission | No supported script transport inside permitted SkillSeat workspace | Not implemented; ClientSeat environment is not a SkillSeat guarantee |
| Initial deck | Main model prepares and MCP-submits the fixed deck | C5 CLI smoke: publication-to-act 17.211 seconds; no prestarted rescue controller |

The C4 injected-worker game used an explicitly separate fault candidate: its first
main-phase analysis slept for 20 seconds; the production parent and its two-second
watchdog were unchanged. It completed 46 actions with one TimeoutExpired fallback,
no missing submission, no validation bypass, and no altered validated action. Overall
decision P50/P95/P99/max were 7.880/15.200/18.340/18.340 seconds. This artificial
delay is control evidence, excluded from quality confirmation results.

The final unmodified C5 ZIP CLI game completed 26 actions, including 16 structured
model choices and two actual disagreements with the default. It had no missing
preparation, bypass or selection mismatch. Publication-to-act P50/P95/P99/max were
8.750/15.334/17.211/17.211 seconds; worker maximum was 0.0521 seconds. One game has
unstable tail quantiles and does not test all kinds of model stalls. The larger
frozen reports supersede these small-sample normal-latency observations.

The 16-test suite additionally exercised child crash, a shorter injected hard cap,
invalid candidate IDs, bool/float action fields, extra keys, stale seq, duplicate
selection, changed game ID with the same seq, a half-second remaining deadline,
missing model suggestions and game_over. Local short-deadline fallback took
0.0238 seconds in the recorded C5 run. Duplicate/stale helpers emit no ready action.
The terminal path starts no worker. subprocess.run kills and waits for the sole
worker; no worker creates descendants or calls a model. These checks cover local
tool behavior, not a guarantee against a main model replaying an old action directly.

The missing-model test deliberately confirms that no independent action file is
created: it exposes the unresolved guarantee rather than pretending a delayed
test substitute is a real Luna result. A real C4 early session exit is a separate
execution failure and is retained as a loss in that version's report. The final
audits also include elapsed time for decisions that never reached act, preventing
success-only latency summaries from hiding failures.

Evidence: [contract](CONTRACT.md), [mechanism/fault checks](checks.json),
[final extracted-artifact checks](checks-extracted.json),
[skill fault audit](skill-fault-audit.json),
[C5 CLI audit](c5-zip-cli-model-audit.json), and final version model audits.
The release remains **research-only**.
